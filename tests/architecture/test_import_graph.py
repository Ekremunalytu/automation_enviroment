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


def test_packages_remain_framework_agnostic() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files("packages"):
        for line_number, import_ref in _import_references(module_path):
            root = import_ref.split(".", maxsplit=1)[0]
            if root in _PACKAGES_BANNED_ROOTS:
                violations.append(
                    f"{_module_label(module_path)}:{line_number} imports {import_ref}"
                )

    assert not violations, "packages/ import graph violations:\n" + "\n".join(
        violations
    )


def test_executor_avoids_workflow_and_appcore_imports() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files("executor"):
        for line_number, import_ref in _import_references(module_path):
            root = import_ref.split(".", maxsplit=1)[0]
            if root in _EXECUTOR_BANNED_ROOTS:
                violations.append(
                    f"{_module_label(module_path)}:{line_number} imports {import_ref}"
                )

    assert not violations, "executor/ import graph violations:\n" + "\n".join(
        violations
    )


def _workflow_import_allowed(import_ref: str) -> bool:
    root = import_ref.split(".", maxsplit=1)[0]
    if root in _WORKFLOW_ALLOWED_ROOTS:
        return True
    if root == "executor":
        return import_ref == "executor.control" or import_ref.startswith(
            "executor.control."
        )
    return root not in _REPO_LOCAL_ROOTS


def test_workflows_use_only_executor_control_boundary() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files("workflows"):
        for line_number, import_ref in _import_references(module_path):
            if not _workflow_import_allowed(import_ref):
                violations.append(
                    f"{_module_label(module_path)}:{line_number} imports {import_ref}"
                )

    assert not violations, "workflows/ import graph violations:\n" + "\n".join(
        violations
    )
