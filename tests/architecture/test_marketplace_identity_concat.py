"""W8-2 architecture regression gate: forbid raw publisher.name-version concat.

The W8-2 helper `packages.marketplace_identity.safe_marketplace_slug` is the
canonical entry point for the three-token marketplace slug. This test scans
production code (`appcore/`, `executor/`, `workflows/`, `packages/` minus
`packages/marketplace_identity/`) for f-strings whose internal structure
matches the `publisher . name - version` adjacency pattern, which is exactly
what the helper exists to replace.

Allowlist:
- `packages/marketplace_identity/**` — the helper itself.
- `tests/**` — not scanned (test fixtures legitimately construct
  adversarial slugs to exercise the helper).
- File-level pragma `# arch-allow: marketplace-identity-concat` placed on
  the same line as the offending f-string (or the line directly above) for
  the rare case a future site genuinely needs raw concat.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCANNED_DIRS = ("appcore", "executor", "workflows", "packages")
EXCLUDED_PREFIX = "packages/marketplace_identity"
PRAGMA = "arch-allow: marketplace-identity-concat"


def _module_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _attr_or_name(node: ast.AST, expected: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == expected
    if isinstance(node, ast.Attribute):
        return node.attr == expected
    return False


def _is_string_constant_containing(node: ast.AST, needle: str) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and needle in node.value
    )


def _detects_three_token_concat(joined: ast.JoinedStr) -> int | None:
    """Return the f-string's lineno if `{publisher}.{name}-{version}` adjacency
    appears anywhere in its parts, else None."""
    parts = joined.values
    if len(parts) < 5:
        return None
    for i in range(len(parts) - 4):
        a, b, c, d, e = parts[i : i + 5]
        publisher_match = isinstance(a, ast.FormattedValue) and _attr_or_name(
            a.value, "publisher"
        )
        dot_separator = _is_string_constant_containing(b, ".")
        name_match = isinstance(c, ast.FormattedValue) and _attr_or_name(
            c.value, "name"
        )
        dash_separator = _is_string_constant_containing(d, "-")
        version_match = isinstance(e, ast.FormattedValue) and _attr_or_name(
            e.value, "version"
        )
        if (
            publisher_match
            and dot_separator
            and name_match
            and dash_separator
            and version_match
        ):
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


def test_no_raw_publisher_name_version_concat_in_production_code() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files():
        rel = _module_label(module_path)
        if rel.startswith(EXCLUDED_PREFIX):
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
            offense_line = _detects_three_token_concat(node)
            if offense_line is None:
                continue
            # Pragma may sit on the offending line itself or the line above
            # (so a multi-line f-string can still be annotated cleanly).
            if any(line in pragma_at for line in (offense_line, offense_line - 1)):
                continue
            violations.append(f"{rel}:{offense_line}")

    assert not violations, (
        "raw publisher.name-version concat detected. "
        "Use packages.marketplace_identity.safe_marketplace_slug() instead, "
        "or add `# arch-allow: marketplace-identity-concat` if intentional.\n"
        + "\n".join(violations)
    )


def test_detector_flags_a_synthetic_violation() -> None:
    """Self-test: confirm the detector actually fires on the canonical
    raw-concat pattern. If the AST shape ever drifts (e.g. a Python upgrade
    changes `JoinedStr` layout) this catches it before the real scan
    silently turns into a no-op."""
    source = 'f"{publisher}.{name}-{version}.vsix"'
    tree = ast.parse(source, mode="eval")
    assert isinstance(tree.body, ast.JoinedStr)
    assert _detects_three_token_concat(tree.body) == 1


def test_detector_ignores_unrelated_fstring() -> None:
    """A self-test that confirms benign f-strings (single token, two-token
    `publisher.name` without version, or unrelated identifiers) do NOT
    trigger the detector — the false-positive guard."""
    benign_sources = [
        'f"prefix-{slug}.vsix"',
        'f"{publisher}.{name}"',
        'f"{actor}.{verb}-{noun}"',
        'f"{publisher} - {name} ({version})"',  # spaced, missing dot/dash
    ]
    for src in benign_sources:
        tree = ast.parse(src, mode="eval")
        assert isinstance(tree.body, ast.JoinedStr)
        assert (
            _detects_three_token_concat(tree.body) is None
        ), f"detector false-fired on benign f-string: {src!r}"
