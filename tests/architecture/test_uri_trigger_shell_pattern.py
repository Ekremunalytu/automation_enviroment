"""W8-3 architecture regression gate: forbid raw ``xdg-open`` shell-string interpolation.

The W8-3 helper ``executor.flows.playwright.uri_validation.run_uri_trigger`` is the
canonical entry point for invoking ``xdg-open`` against a trigger URI; it
validates the scheme against an allow-list and uses ``subprocess.run`` in
argv form. This test scans production code (``appcore/``, ``executor/``,
``workflows/``, ``packages/``) for f-strings that splice a value into a
``xdg-open ...`` shell template — exactly the pattern the helper exists
to replace.

Allowlist:
- ``executor/flows/playwright/uri_validation.py`` — the helper itself (only
  references ``xdg-open`` from a constant path and docstring; the detector
  would not flag those, but exclusion makes the intent explicit).
- ``tests/**`` — not scanned (test fixtures legitimately construct
  adversarial shell-string payloads to exercise the helper and
  surrounding security tests).
- File-level pragma ``# arch-allow: xdg-open-shell-string`` placed on the
  same line as the offending f-string (or the line directly above) for
  the rare case a future site genuinely needs raw concat.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCANNED_DIRS = ("appcore", "executor", "workflows", "packages")
EXCLUDED_PATHS = ("executor/flows/playwright/uri_validation.py",)
PRAGMA = "arch-allow: xdg-open-shell-string"


def _module_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _detects_xdg_open_shell_template(joined: ast.JoinedStr) -> int | None:
    """Return the f-string's lineno if a constant containing ``xdg-open`` is
    immediately followed by a ``FormattedValue`` interpolation, else None.

    Catches both common forms:

    * ``f"xdg-open '{uri}'"`` → ``Constant("xdg-open '")`` + ``FormattedValue``
    * ``f"xdg-open {uri}"`` → ``Constant("xdg-open ")`` + ``FormattedValue``
    """
    parts = joined.values
    for index, part in enumerate(parts):
        if not (isinstance(part, ast.Constant) and isinstance(part.value, str)):
            continue
        if "xdg-open" not in part.value:
            continue
        if index + 1 >= len(parts):
            continue
        if isinstance(parts[index + 1], ast.FormattedValue):
            return joined.lineno
    return None


def _pragma_lines(source: str) -> set[int]:
    return {
        lineno
        for lineno, line in enumerate(source.splitlines(), start=1)
        if PRAGMA in line
    }


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for top in SCANNED_DIRS:
        files.extend(sorted((REPO_ROOT / top).rglob("*.py")))
    return files


def test_no_raw_xdg_open_shell_template_in_production_code() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files():
        rel = _module_label(module_path)
        if rel in EXCLUDED_PATHS:
            continue

        source = module_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        pragma_at = _pragma_lines(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue
            offense_line = _detects_xdg_open_shell_template(node)
            if offense_line is None:
                continue
            if any(line in pragma_at for line in (offense_line, offense_line - 1)):
                continue
            violations.append(f"{rel}:{offense_line}")

    assert not violations, (
        "raw xdg-open shell-string interpolation detected. "
        "Use executor.flows.playwright.uri_validation.run_uri_trigger() instead, "
        "or add `# arch-allow: xdg-open-shell-string` if intentional.\n"
        + "\n".join(violations)
    )


def test_detector_flags_a_synthetic_violation() -> None:
    """Self-test: confirm the detector fires on the canonical
    ``f"xdg-open '{uri}'"`` pattern. If the AST shape ever drifts (e.g.
    a Python upgrade changes ``JoinedStr`` layout) this catches it
    before the real scan silently turns into a no-op."""
    source = "f\"xdg-open '{uri}'\""
    tree = ast.parse(source, mode="eval")
    assert isinstance(tree.body, ast.JoinedStr)
    assert _detects_xdg_open_shell_template(tree.body) == 1


def test_detector_flags_unquoted_synthetic_violation() -> None:
    """Same flavour without surrounding quotes — ``f"xdg-open {uri}"`` is
    just as dangerous and must also fire."""
    source = 'f"xdg-open {uri}"'
    tree = ast.parse(source, mode="eval")
    assert isinstance(tree.body, ast.JoinedStr)
    assert _detects_xdg_open_shell_template(tree.body) == 1


def test_detector_ignores_unrelated_fstrings() -> None:
    """False-positive guard: benign f-strings (no ``xdg-open`` literal,
    or ``xdg-open`` literal without a following interpolation) must NOT
    trigger the detector."""
    benign_sources = [
        'f"echo {value}"',
        'f"Triggering URI: {uri}"',
        'f"xdg-open documentation reference"',
        'f"Run xdg-open manually if the trigger fails"',
    ]
    for src in benign_sources:
        tree = ast.parse(src, mode="eval")
        assert isinstance(tree.body, ast.JoinedStr)
        assert (
            _detects_xdg_open_shell_template(tree.body) is None
        ), f"detector false-fired on benign f-string: {src!r}"


def _scan_synthetic_source(source: str) -> list[int]:
    """Mirror the production scan loop body for a synthetic source.

    Returns a list of offending lineno entries that survive the pragma
    filter — empty list means "no violation". Used by the pragma escape
    tests below so they exercise the same gate the real test does
    without going through the filesystem walk.
    """
    pragma_at = _pragma_lines(source)
    tree = ast.parse(source)
    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        offense_line = _detects_xdg_open_shell_template(node)
        if offense_line is None:
            continue
        if any(line in pragma_at for line in (offense_line, offense_line - 1)):
            continue
        offending.append(offense_line)
    return offending


def test_pragma_escapes_violation_on_same_line() -> None:
    """A ``# arch-allow: xdg-open-shell-string`` pragma on the same line
    as the offending f-string must skip the violation. Without this the
    architecture detector would have no escape hatch for legitimate
    future shell-template sites."""
    source = (
        "# heading\ncmd = f\"xdg-open '{uri}'\"  # arch-allow: xdg-open-shell-string\n"
    )
    assert _scan_synthetic_source(source) == []


def test_pragma_escapes_violation_on_line_above() -> None:
    """A pragma placed on the line *directly above* the offending
    f-string must also skip the violation. This covers multi-line
    f-string expressions where the offending lineno is one below the
    annotation comment."""
    source = "# arch-allow: xdg-open-shell-string\ncmd = f\"xdg-open '{uri}'\"\n"
    assert _scan_synthetic_source(source) == []


def test_pragma_two_lines_above_does_not_escape() -> None:
    """A pragma further than one line above the offending f-string must
    NOT skip the violation — otherwise an unrelated comment far up the
    file could accidentally silence a real finding."""
    source = (
        "# arch-allow: xdg-open-shell-string\n"
        "# unrelated intervening comment\n"
        "cmd = f\"xdg-open '{uri}'\"\n"
    )
    assert _scan_synthetic_source(source) == [3]
