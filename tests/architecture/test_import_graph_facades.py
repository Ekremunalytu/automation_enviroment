"""Import-graph architectural tests — facade thinness + reexport matching + lazy-proxy completeness.

Split from tests/architecture/test_import_graph.py during W16-6 to reduce single-file size.
Covers: extension_catalog_service, analysis_jobs facade, monitor facade eager-import + lazy-proxy.
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


def test_analysis_jobs_facade_stays_thin() -> None:
    """W11-8: ``crud_ops/analysis_jobs/__init__.py`` must remain re-export only.

    The original 348-LoC ``analysis_jobs.py`` was the audit 2026-04-27 §5
    "ahtapot" on the storage side: job lifecycle (create/cancel/complete/
    fail/recovery), step lifecycle (update_step), JSON serialization, and
    a shared error class packed into one module. After the W11-8 split,
    ``lifecycle.py`` owns the lifecycle/recovery surface and ``steps.py``
    owns the step-update + JSON serialization surface; the package
    ``__init__.py`` survives as a back-compat facade so ``appcore/storage/
    crud.py`` and any out-of-tree caller that still imports
    ``appcore.storage.crud_ops.analysis_jobs`` keeps resolving without a
    flag day. This gate prevents the facade from re-growing function or
    class bodies — if any future PR adds logic here it fails this test,
    and the right answer is to land that logic in ``lifecycle.py`` or
    ``steps.py``.
    """
    facade = REPO_ROOT / "appcore/storage/crud_ops/analysis_jobs/__init__.py"
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
        "appcore/storage/crud_ops/analysis_jobs/__init__.py must stay a "
        "thin re-export facade (W11-8 audit §5 ahtapot closure invariant). "
        "Move new logic into lifecycle.py or steps.py:\n" + "\n".join(violations)
    )


def test_analysis_jobs_facade_reexports_match_canonical_modules() -> None:
    """W11-8: every name in ``analysis_jobs.__all__`` must come from the
    focused modules, by ``is`` identity (not equality).

    Pins the contract that the facade's re-exported set is exactly what
    ``lifecycle.py`` and ``steps.py`` provide — no orphan re-exports, no
    shim-wrapped versions of public symbols. A future facade rewrite that
    swaps re-exports for shim wrappers fails this test.
    """
    from appcore.storage.crud_ops import analysis_jobs as facade
    from appcore.storage.crud_ops.analysis_jobs import lifecycle, steps

    expected_in_steps = {"update_analysis_job_step"}
    expected_in_lifecycle = set(facade.__all__) - expected_in_steps

    for name in expected_in_steps:
        facade_obj = getattr(facade, name)
        canonical_obj = getattr(steps, name)
        assert facade_obj is canonical_obj, (
            f"analysis_jobs.{name} must be the same object as steps.{name} "
            "(W11-8 re-export invariant)."
        )

    for name in expected_in_lifecycle:
        facade_obj = getattr(facade, name)
        canonical_obj = getattr(lifecycle, name)
        assert facade_obj is canonical_obj, (
            f"analysis_jobs.{name} must be the same object as "
            f"lifecycle.{name} (W11-8 re-export invariant)."
        )


def test_monitor_facade_does_not_eagerly_import_attribution() -> None:
    """W12-1: ``monitor/__init__.py`` must defer attribution imports.

    The attribution subpackage transitively imports ``monitor.records``,
    which (after W12-1 subpackaging) triggers ``monitor/__init__.py`` to
    load. Eager ``from ..attribution import annotate_*`` etc. inside the
    monitor facade re-introduces the import cycle and the partial-module
    AttributeError it produces. The PEP 562 ``__getattr__`` at the bottom
    of ``monitor/__init__.py`` proxies the attribution surface lazily so
    callers still see ``monitor.annotate_file_events`` via the public
    re-export shape (W12-2 trimmed the surface from 15 underscore names to
    10 public names). This gate fails fast if a future PR replaces the
    lazy proxy with a top-level import — the right answer is to extend
    ``_LAZY_ATTRIBUTION_NAMES`` and keep ``__getattr__``.
    """
    facade = REPO_ROOT / "executor/flows/playwright/monitor/__init__.py"
    tree = ast.parse(facade.read_text(encoding="utf-8"))

    violations: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        # Detect `from ..attribution import ...` (level==2, module=="attribution").
        if node.level == 2 and node.module == "attribution":
            violations.append(f"line {node.lineno}: from ..attribution import ...")

    assert not violations, (
        "monitor/__init__.py imports attribution eagerly — this re-creates "
        "the W12-1 attribution↔monitor cycle. Move the imports into the "
        "_LAZY_ATTRIBUTION_NAMES tuple + __getattr__ proxy at the bottom "
        "of the module:\n" + "\n".join(violations)
    )


def test_monitor_lazy_proxy_completeness() -> None:
    """W12-1: every name in the monitor facade's lazy tuples must resolve.

    ``monitor/__init__.py`` defines three tuples — ``_LAZY_ATTRIBUTION_NAMES``,
    ``_LAZY_LIFECYCLE_NAMES``, ``_LAZY_TYPES_NAMES`` — that the PEP 562
    ``__getattr__`` walks to proxy access into ``attribution``,
    ``monitor.lifecycle``, and ``monitor.types`` respectively. A typo in any
    tuple entry, or a name that no longer exists in its source module,
    silently produces ``AttributeError`` only at the call site of a future
    consumer; nothing else catches it. This gate iterates every entry and
    asserts ``getattr(monitor, name) is getattr(<source>, name)`` so the
    proxy contract is verified against the real source modules.
    """
    from executor.flows.playwright import attribution
    from executor.flows.playwright import monitor as monitor_pkg
    from executor.flows.playwright.monitor import lifecycle, types

    sources = (
        (monitor_pkg._LAZY_ATTRIBUTION_NAMES, attribution, "attribution"),
        (monitor_pkg._LAZY_LIFECYCLE_NAMES, lifecycle, "monitor.lifecycle"),
        (monitor_pkg._LAZY_TYPES_NAMES, types, "monitor.types"),
    )

    violations: list[str] = []
    for tuple_, source_module, source_label in sources:
        for name in tuple_:
            if not hasattr(source_module, name):
                violations.append(
                    f"monitor.{name} proxied to {source_label} but {source_label} "
                    f"has no attribute {name!r}"
                )
                continue
            facade_obj = getattr(monitor_pkg, name)
            canonical_obj = getattr(source_module, name)
            if facade_obj is not canonical_obj:
                violations.append(
                    f"monitor.{name} is not the same object as "
                    f"{source_label}.{name} (proxy identity broken)"
                )

    assert not violations, (
        "monitor facade lazy proxy contract broken (W12-1 PEP 562 invariant). "
        "Either fix the tuple in monitor/__init__.py or restore the missing "
        "name in the source module:\n" + "\n".join(violations)
    )
