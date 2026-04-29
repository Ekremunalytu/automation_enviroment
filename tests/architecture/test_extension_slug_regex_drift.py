"""W8-5 architecture regression gate: forbid duplicate slug regex literals.

The W8-2 helper ``packages.marketplace_identity._slug.MARKETPLACE_SLUG_TOKEN_RE``
is the canonical home for the marketplace slug regex. The W8-5
consolidation re-imports that constant in
``appcore/contracts/validators.py`` so two surfaces (marketplace identity
helper + FastAPI ``Path(..., pattern=...)`` gate) share one source-of-truth.

This detector scans production code (``appcore/``, ``executor/``,
``workflows/``, ``packages/``) for any ``re.compile(...)`` whose first
argument is a string literal equal to the slug pattern, anywhere outside
the two allowlisted homes. A drift hit means a third copy has appeared
and must be funnelled through the constant.
"""

from __future__ import annotations

import ast
from pathlib import Path

from packages.marketplace_identity import MARKETPLACE_SLUG_TOKEN_RE

REPO_ROOT = Path(__file__).parents[2]
SCANNED_DIRS = ("appcore", "executor", "workflows", "packages")
ALLOWED_PATHS = (
    "packages/marketplace_identity/_slug.py",
    "appcore/contracts/validators.py",
)
SLUG_PATTERN_LITERAL = MARKETPLACE_SLUG_TOKEN_RE.pattern


def _module_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _is_re_compile_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute) and func.attr == "compile":
        value = func.value
        if isinstance(value, ast.Name) and value.id == "re":
            return True
    if isinstance(func, ast.Name) and func.id == "compile":
        # Avoid false-fire on builtin ``compile`` — only re.compile counts.
        return False
    return False


def _detects_slug_pattern_literal(call: ast.Call) -> int | None:
    """Return the call's lineno if the first arg is a str constant equal to
    the slug pattern literal, else None."""
    if not call.args:
        return None
    first_arg = call.args[0]
    if not (isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str)):
        return None
    if first_arg.value != SLUG_PATTERN_LITERAL:
        return None
    return call.lineno


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for top in SCANNED_DIRS:
        files.extend(sorted((REPO_ROOT / top).rglob("*.py")))
    return files


def test_no_duplicate_slug_regex_literal_in_production_code() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files():
        rel = _module_label(module_path)
        if rel in ALLOWED_PATHS:
            continue

        source = module_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_re_compile_call(node):
                continue
            offense_line = _detects_slug_pattern_literal(node)
            if offense_line is None:
                continue
            violations.append(f"{rel}:{offense_line}")

    assert not violations, (
        "duplicate slug regex literal detected. "
        "Re-import packages.marketplace_identity.MARKETPLACE_SLUG_TOKEN_RE "
        "(or appcore.contracts.validators.ACTIVATION_REPORT_NAME_RE for "
        "name-shaped patterns) instead of re-compiling the same string.\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _scan_synthetic_source(source: str) -> list[int]:
    tree = ast.parse(source)
    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _is_re_compile_call(node):
            continue
        offense_line = _detects_slug_pattern_literal(node)
        if offense_line is None:
            continue
        offending.append(offense_line)
    return offending


def test_detector_flags_synthetic_slug_pattern_duplicate() -> None:
    source = "import re\n" f"PAT = re.compile(r{SLUG_PATTERN_LITERAL!r})\n"
    assert _scan_synthetic_source(source) == [2]


def test_detector_ignores_unrelated_regex_literal() -> None:
    source = "import re\nP = re.compile(r'^foo$')\n"
    assert _scan_synthetic_source(source) == []


def test_detector_ignores_builtin_compile() -> None:
    """``compile(...)`` (builtin, no ``re.`` prefix) is unrelated and must
    not false-fire on a slug-pattern literal."""
    source = f"PAT = compile({SLUG_PATTERN_LITERAL!r}, '<string>', 'eval')\n"
    assert _scan_synthetic_source(source) == []


def test_detector_ignores_re_match_calls() -> None:
    """Only ``re.compile(...)`` is in scope; ``re.match(...)`` etc. produce
    runtime matches but do not stash a duplicate compiled pattern."""
    source = "import re\n" f"hit = re.match(r{SLUG_PATTERN_LITERAL!r}, 'foo')\n"
    assert _scan_synthetic_source(source) == []
