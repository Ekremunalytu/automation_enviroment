"""W14-6.a architecture gate (`[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`):
strict ratchet on the ``# arch-allow: bare-binary-path`` pragma count.

The W8-4 helper module ``executor.binary_paths`` is the canonical home
for absolute paths to every binary invoked by ``executor/``. The
companion gate ``tests/architecture/test_absolute_binary_paths.py``
forbids bare-name binary literals in ``subprocess.run([...])`` /
``subprocess.Popen([...])`` calls, with a ``# arch-allow: bare-binary-path``
pragma escape for the rare site where the bare name is genuinely
needed.

The W8-4 follow-up `arch-gate-bare-binary-pragma-ratchet` flags that
pragma count is currently load-bearing but not enforced: a future
audit-bypass landing 2-3 more bare-binary literals would silently
land if it dropped the same pragma. This gate pins the pragma count
and per-file distribution so any growth fails CI and forces an
explicit migration to absolute paths (W8-4 spirit) or an explicit
baseline bump in this file.

Enforced baseline (source of truth: the ``_BASELINE_PRAGMA_COUNT`` /
``_EXPECTED_PRAGMA_DISTRIBUTION`` constants below, verified against the tree):

- ``executor/flows/playwright/vscode/editor.py`` — 3 pragmas
  (xdotool invocations: window focus + key send + window list).
- ``executor/flows/playwright/reset_state.py`` — 2 pragmas
  (pgrep / bash invocations during sandbox reset).
- ``executor/flows/playwright/monitor/runtime.py`` — 1 pragma
  (``ps`` invocation in runtime probe).
- ``executor/flows/playwright/vscode/__init__.py`` — 1 pragma
  (xdotool invocation in the vscode package init).

Total: **7 pragmas across 4 files**. (History: W14-6 sub-commit 6 lowered the
count from 7 → 6 by migrating ``runtime_capture/extension_host_capture.py``'s
inotifywait site to ``executor.binary_paths.INOTIFYWAIT_PATH``; a later change
re-introduced one xdotool pragma in ``vscode/__init__.py``, so the enforced
baseline is again 7. The constants — not this prose — are authoritative; this
gate fails if the tree drifts from them.)

Pragma reduction is the desired direction. If a future PR migrates
one of these sites to ``executor.binary_paths.*`` constants (or adds
a new absolute path to that module), it should also lower the
baseline in this file by the same amount in the same commit so the
gate ratchets monotonically downward.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNED_DIR = "executor"
PRAGMA = "arch-allow: bare-binary-path"

_BASELINE_PRAGMA_COUNT: Final[int] = 7

_EXPECTED_PRAGMA_DISTRIBUTION: Final[dict[str, int]] = {
    "executor/flows/playwright/vscode/editor.py": 3,
    "executor/flows/playwright/reset_state.py": 2,
    "executor/flows/playwright/monitor/runtime.py": 1,
    "executor/flows/playwright/vscode/__init__.py": 1,
}


def _count_pragmas_in_file(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if PRAGMA in line)


def _iter_pragma_distribution() -> dict[str, int]:
    distribution: dict[str, int] = {}
    for module_path in sorted((REPO_ROOT / SCANNED_DIR).rglob("*.py")):
        count = _count_pragmas_in_file(module_path)
        if count == 0:
            continue
        rel = module_path.relative_to(REPO_ROOT).as_posix()
        distribution[rel] = count
    return distribution


def test_bare_binary_pragma_total_count_matches_baseline() -> None:
    """The total pragma count across ``executor/`` must equal the
    pinned W14-6 baseline. Growth indicates a new bare-binary literal
    landed without migration to ``executor.binary_paths``; shrinkage
    indicates a migration happened and the baseline should be lowered
    in the same commit."""
    distribution = _iter_pragma_distribution()
    total = sum(distribution.values())
    assert total == _BASELINE_PRAGMA_COUNT, (
        f"`# arch-allow: bare-binary-path` pragma count drift detected. "
        f"Baseline: {_BASELINE_PRAGMA_COUNT}. Current: {total}. "
        f"Distribution: {distribution}. If you intentionally added a "
        "bare-binary literal, migrate it to an absolute path under "
        "`executor.binary_paths` (W8-4 spirit) instead. If a migration "
        "already happened and lowered the count, update "
        "_BASELINE_PRAGMA_COUNT and _EXPECTED_PRAGMA_DISTRIBUTION in "
        "this file to ratchet the gate down."
    )


def test_bare_binary_pragma_per_file_count_matches_distribution() -> None:
    """The per-file pragma distribution must match the pinned W14-6
    map exactly. Catches the case where the total stays the same but
    a pragma moves from one file to another — usually a sign that
    one site was migrated to absolute paths while a new site got
    pragma'd without an arch review."""
    distribution = _iter_pragma_distribution()
    assert distribution == _EXPECTED_PRAGMA_DISTRIBUTION, (
        "`# arch-allow: bare-binary-path` pragma distribution drift. "
        f"Expected: {_EXPECTED_PRAGMA_DISTRIBUTION}. Got: {distribution}. "
        "If a known site was migrated to `executor.binary_paths`, "
        "remove it from _EXPECTED_PRAGMA_DISTRIBUTION in this commit "
        "and lower _BASELINE_PRAGMA_COUNT accordingly. If a new site "
        "genuinely needs a pragma, add it to the map *and* explain "
        "in the commit message why migration is not feasible."
    )


def test_bare_binary_pragma_counter_self_check() -> None:
    """Self-test: the synthetic counter logic correctly counts the
    pragma string against a known-shape source. Without this guard a
    refactor of ``_count_pragmas_in_file`` could silently return 0
    for every file and the two gates above would pass vacuously.
    """
    synthetic_source = "\n".join(
        [
            "import subprocess",
            'subprocess.run(["bare1", "arg"])  # arch-allow: bare-binary-path',
            "# arch-allow: bare-binary-path",
            'subprocess.Popen(["bare2", "arg"])',
            'subprocess.run(["/usr/bin/code", "arg"])  # no pragma',
            "# arch-allow: bare-binary-path  # multi-line comment OK",
            'subprocess.Popen(["bare3", "arg"])',
        ]
    )
    count = sum(1 for line in synthetic_source.splitlines() if PRAGMA in line)
    assert count == 3, (
        "self-test: synthetic source has 3 pragma occurrences "
        f"(same-line, line-above, multi-line); counter saw {count}."
    )
