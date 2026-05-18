"""Import-graph architectural tests — executor-specific import patterns.

Split from tests/architecture/test_import_graph.py during W16-6 to reduce single-file size.
Covers: no dual-import fallback, no sys.path manipulation, executor imports signals from packages.
"""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]

_PACKAGES_BANNED_ROOTS = {"appcore", "executor", "ui", "workflows"}
_EXECUTOR_BANNED_ROOTS = {"appcore", "workflows"}
_WORKFLOW_ALLOWED_ROOTS = {"appcore", "packages", "workflows"}
_REPO_LOCAL_ROOTS = {
    path.name
    for path in REPO_ROOT.iterdir()
    if path.is_dir() and any(path.rglob("*.py"))
}.union({path.stem for path in REPO_ROOT.glob("*.py") if path.name != "__init__.py"})


def _iter_python_files(top_level_dir: str) -> list[Path]:
    return sorted((REPO_ROOT / top_level_dir).rglob("*.py"))


def _import_references(module_path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    references: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                references.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.level:
                continue
            for alias in node.names:
                references.append((node.lineno, f"{node.module}.{alias.name}"))
    return references


def _module_label(module_path: Path) -> str:
    return module_path.relative_to(REPO_ROOT).as_posix()



_DUAL_IMPORT_ALLOW_LIST = {
    "executor/flows/playwright/monitor/support.py",
}

_RUNTIME_ROOTS = ("appcore", "executor", "packages", "workflows")
_SYS_PATH_ALLOW_LIST: set[str] = set()


def _handler_catches_import_error(handler: ast.ExceptHandler) -> bool:
    exc_type = handler.type
    if exc_type is None:
        return False
    if isinstance(exc_type, ast.Name) and exc_type.id == "ImportError":
        return True
    if isinstance(exc_type, ast.Tuple):
        return any(
            isinstance(elt, ast.Name) and elt.id == "ImportError"
            for elt in exc_type.elts
        )
    return False


def test_no_dual_import_fallback_in_executor() -> None:
    violations: list[str] = []
    for module_path in _iter_python_files("executor"):
        rel = _module_label(module_path)
        if rel in _DUAL_IMPORT_ALLOW_LIST:
            continue
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if _handler_catches_import_error(handler):
                    violations.append(f"{rel}:{node.lineno}")
    assert not violations, (
        "executor/ tree has dual-import ImportError fallbacks (W9-3 forbids):\n"
        + "\n".join(violations)
    )


def _is_sys_path_attr(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "path"
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    )


def test_no_sys_path_manipulation_in_runtime() -> None:
    violations: list[str] = []
    for root in _RUNTIME_ROOTS:
        for module_path in _iter_python_files(root):
            rel = _module_label(module_path)
            if rel in _SYS_PATH_ALLOW_LIST:
                continue
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"insert", "append"}
                    and _is_sys_path_attr(node.func.value)
                ):
                    violations.append(f"{rel}:{node.lineno}")
    assert not violations, (
        "runtime tree has sys.path.insert/append calls (W9-4 forbids):\n"
        + "\n".join(violations)
    )


def test_executor_imports_signals_from_packages() -> None:
    facade = REPO_ROOT / "executor/flows/playwright/signals/__init__.py"
    references = _import_references(facade)
    flat = [ref for _, ref in references if ref.startswith("signal_policy")]
    assert not flat, (
        "executor/flows/playwright/signals/__init__.py still references flat "
        f"signal_policy: {flat}"
    )
    package_refs = [
        ref
        for _, ref in references
        if ref.startswith("packages.analysis_engine.signals.policy")
    ]
    assert package_refs, (
        "executor/flows/playwright/signals/__init__.py must import from "
        "packages.analysis_engine.signals.policy (W9-2 contract)."
    )

