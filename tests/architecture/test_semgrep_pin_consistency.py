"""Architecture gate: the Semgrep version pin is single-sourced (ES-4, ADR 0016).

The runner records ``_SEMGREP_VERSION`` in every report; the hardened image
installs the wheel pinned in ``docker/static_analyzer/requirements.txt``. If the
two drift, the report advertises a version the container does not actually run.
This gate asserts they are byte-identical and the pin is exact (``==``), since
rule-match semantics are version-sensitive (ADR 0016 §Consequences).
"""

from __future__ import annotations

import re
from pathlib import Path

from static_runtime import semgrep_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = REPO_ROOT / "docker" / "static_analyzer" / "requirements.txt"
_PIN_RE = re.compile(r"^semgrep==(?P<version>[0-9][0-9A-Za-z.+-]*)\s*$", re.MULTILINE)


def test_semgrep_pin_matches_runner_constant() -> None:
    text = REQUIREMENTS.read_text(encoding="utf-8")
    match = _PIN_RE.search(text)
    assert match is not None, (
        f"{REQUIREMENTS.relative_to(REPO_ROOT)} must pin semgrep exactly "
        "(semgrep==X.Y.Z) — the pin is load-bearing for rule semantics."
    )
    assert match.group("version") == semgrep_runner._SEMGREP_VERSION, (
        "Semgrep version drift: requirements.txt pins "
        f"{match.group('version')!r} but static_runtime/semgrep_runner.py's "
        f"_SEMGREP_VERSION is {semgrep_runner._SEMGREP_VERSION!r}. Keep them "
        "identical so the recorded version matches the installed wheel."
    )


def test_semgrep_pin_is_exact_not_range() -> None:
    text = REQUIREMENTS.read_text(encoding="utf-8")
    semgrep_lines = [
        line for line in text.splitlines() if line.strip().startswith("semgrep")
    ]
    assert semgrep_lines, "no semgrep requirement line found"
    for line in semgrep_lines:
        assert "==" in line, f"semgrep pin must be exact (==), got: {line!r}"
        assert not any(op in line for op in (">=", "<=", "~=", ">", "<")), (
            f"semgrep pin must be exact, not a range: {line!r}"
        )
