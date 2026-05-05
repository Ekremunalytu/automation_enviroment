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


_DUAL_IMPORT_ALLOW_LIST = {
    "executor/flows/playwright/monitor_support.py",
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
    facade = REPO_ROOT / "executor/flows/playwright/signals.py"
    references = _import_references(facade)
    flat = [ref for _, ref in references if ref.startswith("signal_policy")]
    assert not flat, (
        "executor/flows/playwright/signals.py still references flat "
        f"signal_policy: {flat}"
    )
    package_refs = [
        ref
        for _, ref in references
        if ref.startswith("packages.analysis_engine.signals.policy")
    ]
    assert package_refs, (
        "executor/flows/playwright/signals.py must import from "
        "packages.analysis_engine.signals.policy (W9-2 contract)."
    )


def test_extension_catalog_service_stays_a_thin_facade() -> None:
    """W11-7: `workflows/extension_catalog/service.py` must remain re-export only.

    The original 475-LoC `service.py` was the audit 2026-04-27 §5 "ahtapot":
    six responsibilities packed into one module. After the W11-7 split,
    `manifest_to_schema.py` owns the hydration pipeline and `lifecycle.py`
    owns the public surface; `service.py` survives as a back-compat facade
    for `workflows/marketplace/router.py` and the canonical-imports test.
    This gate prevents the facade from re-growing function/class bodies —
    if any future PR adds logic here it fails this test, and the right
    answer is to land that logic in `lifecycle.py` or `manifest_to_schema.py`.
    """
    facade = REPO_ROOT / "workflows/extension_catalog/service.py"
    tree = ast.parse(facade.read_text(encoding="utf-8"))

    allowed_node_types: tuple[type[ast.AST], ...] = (
        ast.Import,
        ast.ImportFrom,
    )
    violations: list[str] = []
    for node in tree.body:
        # Module docstring: a top-level Expr wrapping a string Constant.
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        # `__all__ = [...]` re-export listing.
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
        ):
            continue
        if isinstance(node, allowed_node_types):
            continue
        violations.append(f"line {node.lineno}: {type(node).__name__}")

    assert not violations, (
        "workflows/extension_catalog/service.py must stay a thin re-export "
        "facade (W11-7 audit §5 ahtapot closure invariant). "
        "Move new logic into lifecycle.py or manifest_to_schema.py:\n"
        + "\n".join(violations)
    )


def test_extension_catalog_service_reexports_match_canonical_modules() -> None:
    """W11-7: every name in `service.__all__` must come from the focused modules.

    Pins the contract that the facade's re-exported set is exactly what
    `lifecycle.py` and `manifest_to_schema.py` provide — no orphan
    re-exports, no shim-wrapped versions of public symbols.
    """
    from workflows.extension_catalog import (
        lifecycle,
        manifest_to_schema,
        service,
    )

    expected_in_manifest_to_schema = {"ExtensionManifestMismatchError"}
    expected_in_lifecycle = set(service.__all__) - expected_in_manifest_to_schema

    for name in expected_in_manifest_to_schema:
        facade_obj = getattr(service, name)
        canonical_obj = getattr(manifest_to_schema, name)
        assert facade_obj is canonical_obj, (
            f"service.{name} must be the same object as "
            f"manifest_to_schema.{name} (W11-7 re-export invariant)."
        )

    for name in expected_in_lifecycle:
        facade_obj = getattr(service, name)
        canonical_obj = getattr(lifecycle, name)
        assert facade_obj is canonical_obj, (
            f"service.{name} must be the same object as lifecycle.{name} "
            "(W11-7 re-export invariant)."
        )
