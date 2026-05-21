"""W15-2 architecture gate: workspace cleanup helpers must check
``is_symlink()`` (or ``os.path.islink``) BEFORE branching into
``shutil.rmtree`` so adversarial symlinks are not dereferenced.

Codex 2026-05-10 M12 close-out. The pre-W15-2 ``clean_workspace`` body
branched on ``is_dir()`` (which follows symlinks) before falling
through to ``shutil.rmtree``; a symlink-to-directory inside the
workspace therefore crashed cleanup (Python ≥3.7 ``shutil.rmtree``
refuses to rmtree a symlink), and the broader concern is that the
symlink target is operator-controlled state that must not be touched
by automation cleanup.

Scope-locked to the two workspace cleanup chokepoints currently in the
executor tree:

- ``executor/flows/playwright/workspace/__init__.py`` -> ``clean_workspace``
- ``executor/flows/playwright/reset_state.py`` -> ``_clear_directory``

If a new cleanup helper is added that calls ``shutil.rmtree`` over a
directory containing untrusted entries, add it to ``WORKSPACE_HELPERS``
so this gate keeps the discipline pinned.

Modeled on the W14-5 / W15-1 AST gate pattern.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_HELPERS: tuple[tuple[Path, str], ...] = (
    (
        REPO_ROOT / "executor" / "flows" / "playwright" / "workspace" / "__init__.py",
        "clean_workspace",
    ),
    (
        REPO_ROOT / "executor" / "flows" / "playwright" / "reset_state.py",
        "_clear_directory",
    ),
)


def _module_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _find_rmtree_calls(fn: ast.FunctionDef) -> list[ast.Call]:
    """Return ``shutil.rmtree(...)`` / bare ``rmtree(...)`` calls."""
    calls: list[ast.Call] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_attr_rmtree = isinstance(func, ast.Attribute) and func.attr == "rmtree"
        is_name_rmtree = isinstance(func, ast.Name) and func.id == "rmtree"
        if is_attr_rmtree or is_name_rmtree:
            calls.append(node)
    return calls


def _find_symlink_check_calls(fn: ast.FunctionDef) -> list[ast.Call]:
    """Return calls that classify a path as a symlink without following.

    Matches:

    - ``path.is_symlink()`` (``Path.is_symlink``)
    - ``os.path.islink(path)`` (``islink`` attr — namespace-resilient)
    - ``os.lstat(path)`` (lower-level; uses lstat directly)
    """
    attr_names = {"is_symlink", "islink", "lstat"}
    bare_names = {"lstat", "islink"}
    calls: list[ast.Call] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_attr_match = isinstance(func, ast.Attribute) and func.attr in attr_names
        is_name_match = isinstance(func, ast.Name) and func.id in bare_names
        if is_attr_match or is_name_match:
            calls.append(node)
    return calls


# ---------------------------------------------------------------------------
# Invariant 1 — every workspace cleanup helper checks for symlink-ness
# before delegating to ``shutil.rmtree``
# ---------------------------------------------------------------------------


def test_workspace_cleanup_helpers_check_symlink_before_rmtree() -> None:
    """Every enumerated cleanup chokepoint must call ``is_symlink()``
    (or ``os.path.islink`` / ``os.lstat``) at a smaller line number than
    its earliest ``shutil.rmtree(...)`` call.

    AST-line-number ordering is a weaker proof than a runtime guard but
    is the right tool here: the helpers are small, the rmtree call site
    is unambiguous, and any reorder that pulls rmtree above the symlink
    check is exactly the bug class this gate exists to prevent.
    """
    violations: list[str] = []
    for module_path, fn_name in WORKSPACE_HELPERS:
        rel = module_path.relative_to(REPO_ROOT).as_posix()
        tree = _module_tree(module_path)
        fn = _find_function(tree, fn_name)
        if fn is None:
            violations.append(f"{rel}: function `{fn_name}` not found")
            continue
        rmtree_calls = _find_rmtree_calls(fn)
        if not rmtree_calls:
            # Helper no longer delegates to rmtree -> gate is vacuous
            # for this entry. Not a violation.
            continue
        symlink_calls = _find_symlink_check_calls(fn)
        if not symlink_calls:
            violations.append(
                f"{rel}:{fn.lineno} `{fn_name}` calls shutil.rmtree() "
                "but never checks is_symlink() / os.path.islink / "
                "os.lstat — adversarial symlinks would be followed."
            )
            continue
        earliest_symlink = min(c.lineno for c in symlink_calls)
        earliest_rmtree = min(c.lineno for c in rmtree_calls)
        if earliest_symlink >= earliest_rmtree:
            violations.append(
                f"{rel}: in `{fn_name}` symlink classification at line "
                f"{earliest_symlink} is not before shutil.rmtree() at "
                f"line {earliest_rmtree}; cleanup must branch on "
                "symlink-ness before delegating to rmtree."
            )
    assert not violations, (
        "Workspace cleanup helpers must check is_symlink() before "
        "calling shutil.rmtree() to prevent following adversarial "
        "symlinks (W15-2, Codex 2026-05-10 M12). Violations:\n" + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Invariant 2 — vacuous-truth guard: the helpers table must enumerate
# at least the two known chokepoints. If both helpers are renamed /
# removed in a refactor, invariant 1 above would pass vacuously.
# ---------------------------------------------------------------------------


def test_workspace_helpers_table_pins_known_chokepoints() -> None:
    """The two known cleanup chokepoints must each exist as a
    ``FunctionDef`` at their declared module path. Renames are allowed
    only via an explicit update to ``WORKSPACE_HELPERS``.
    """
    missing: list[str] = []
    for module_path, fn_name in WORKSPACE_HELPERS:
        rel = module_path.relative_to(REPO_ROOT).as_posix()
        if not module_path.exists():
            missing.append(f"{rel} (module missing)")
            continue
        tree = _module_tree(module_path)
        if _find_function(tree, fn_name) is None:
            missing.append(f"{rel}::{fn_name} (function missing)")
    assert not missing, (
        "WORKSPACE_HELPERS table is out of sync with the executor tree; "
        "if a helper was renamed/moved, update the table. Missing:\n"
        + "\n".join(missing)
    )
    assert len(WORKSPACE_HELPERS) >= 2, (
        "WORKSPACE_HELPERS must enumerate at least the two known "
        "cleanup chokepoints (clean_workspace + _clear_directory)."
    )
