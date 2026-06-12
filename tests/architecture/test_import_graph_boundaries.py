"""Import-graph architectural tests — package isolation boundaries.

Split from tests/architecture/test_import_graph.py during W16-6 to reduce single-file size.
Covers: packages stay framework-agnostic, executor avoids workflow/appcore, workflows only via executor control.
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


def _resolve_relative_import(
    module_path: Path, level: int, module: str | None
) -> str | None:
    """Resolve a relative ``from .. import`` to its absolute dotted module.

    ``level`` is the leading-dot count and ``module`` the optional suffix
    (``None`` for ``from . import x``). The anchor is the importing file's
    own package walked up ``level - 1`` times, matching Python's
    relative-import semantics, so the boundary check sees the resolved
    root instead of silently skipping it (F-3). Returns ``None`` when the
    level walks above the repo top (an import Python itself rejects); a
    beyond-top-level anchor resolves to ``""`` so the bare imported name
    becomes the root, catching a pathological cross-package relative.
    """
    package_parts = list(module_path.relative_to(REPO_ROOT).with_suffix("").parts[:-1])
    up = level - 1
    if up > len(package_parts):
        return None
    anchor = package_parts[: len(package_parts) - up]
    if module:
        anchor = anchor + module.split(".")
    return ".".join(anchor)


def _import_references(module_path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    references: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                references.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # F-3: resolve the relative import to its absolute module so
                # the boundary check sees the real root instead of skipping
                # the edge. A relative import cannot escape its own top-level
                # package, so the resolved root is normally in-package;
                # resolving still keeps the gate honest and flags a
                # pathological beyond-top-level relative reaching a banned root.
                base = _resolve_relative_import(module_path, node.level, node.module)
                if base is None:
                    continue
                for alias in node.names:
                    ref = f"{base}.{alias.name}" if base else alias.name
                    references.append((node.lineno, ref))
            elif node.module:
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
        # Workflows reach the executor only through its sanctioned control
        # facades: `executor.control` (dynamic sandbox) and
        # `executor.static_control` (static pre-check analyzer, ES-3b). Both
        # mirror each other and exist precisely so workflows never import the
        # host-orchestration internals (`executor.host` / `executor.static_host`).
        return any(
            import_ref == boundary or import_ref.startswith(f"{boundary}.")
            for boundary in ("executor.control", "executor.static_control")
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
    "executor/flows/playwright/monitor/support.py",
}

_RUNTIME_ROOTS = ("appcore", "executor", "packages", "workflows")
_SYS_PATH_ALLOW_LIST: set[str] = set()


def test_relative_import_resolution_feeds_boundary_check() -> None:
    """F-3: relative imports resolve to their absolute module so the
    banned-root check is no longer blind to them.

    Exercises the resolver directly with synthetic paths under the repo
    root (the files need not exist — resolution is a pure path
    computation):

    * an in-package relative (``from . import x`` in a ``packages``
      module) resolves to a ``packages.*`` root, which is *allowed* — the
      gate must not false-flag it;
    * a parent-package relative (``from ..attribution import x`` in the
      monitor package) resolves to the correct sibling subpackage;
    * a *beyond-top-level* relative (``from .. import appcore`` from a
      top-level ``packages`` module — invalid Python, but a static gate
      must not be blind to it) resolves so the bare imported name becomes
      the root, which the banned-root check would then flag.
    """
    # In-package relative -> allowed root (no false positive).
    base = _resolve_relative_import(REPO_ROOT / "packages" / "foo" / "bar.py", 1, None)
    assert base == "packages.foo"
    assert "packages" not in _PACKAGES_BANNED_ROOTS

    # Parent-package relative -> correct sibling subpackage.
    monitor_init = (
        REPO_ROOT / "executor" / "flows" / "playwright" / "monitor" / "__init__.py"
    )
    base = _resolve_relative_import(monitor_init, 2, "attribution")
    assert base == "executor.flows.playwright.attribution"

    # Beyond-top-level relative -> bare name becomes the root, which the
    # banned-root check the boundary tests apply would now catch.
    base = _resolve_relative_import(REPO_ROOT / "packages" / "mod.py", 2, None)
    assert base == ""
    ref = f"{base}.appcore" if base else "appcore"
    assert ref.split(".", maxsplit=1)[0] in _PACKAGES_BANNED_ROOTS
