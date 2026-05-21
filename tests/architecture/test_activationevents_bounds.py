"""W15-3 architecture gate: activationEvents surfaces must declare
size caps to prevent oversize-manifest DoS / DB row inflation.

Codex 2026-05-10 U8 close-out. Pre-W15-3 the manifest field
``activationEvents`` was unbounded across three surfaces (Pydantic
ingest schema, manifest pre-parser, DB columns), so a hostile manifest
could push gigabyte-scale data through ingestion. This gate pins:

- ``ExtensionActivationEventsSchema.event_type`` -> ``Field(..., max_length=64)``
- ``ExtensionActivationEventsSchema.event_value`` -> ``Field(..., max_length=1024)``
- ``ExtensionDetailSchema.activation_events`` -> ``Field(..., max_length=512)`` (list cap)
- ``ExtensionActivationEvents.event_type`` SQLAlchemy column -> ``String(64)``
- ``ExtensionActivationEvents.event_value`` SQLAlchemy column -> ``String(1024)``

Plus a vacuous-truth guard so a future refactor that renames any of
these targets must update this gate's tables.

Modeled on the W15-1 / W15-2 AST gate pattern.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CATALOG_SCHEMA = REPO_ROOT / "appcore" / "contracts" / "schema_defs" / "catalog.py"
EXTENSION_MODEL = REPO_ROOT / "appcore" / "storage" / "model_defs" / "extension.py"

# Expected caps on Pydantic fields: (file, class_name, field_name, max_length).
PYDANTIC_FIELD_CAPS: tuple[tuple[Path, str, str, int], ...] = (
    (CATALOG_SCHEMA, "ExtensionActivationEventsSchema", "event_type", 64),
    (CATALOG_SCHEMA, "ExtensionActivationEventsSchema", "event_value", 1024),
    (CATALOG_SCHEMA, "ExtensionDetailSchema", "activation_events", 512),
)

# Expected caps on SQLAlchemy columns: (file, class_name, attr, sa_type, length).
DB_COLUMN_CAPS: tuple[tuple[Path, str, str, str, int], ...] = (
    (EXTENSION_MODEL, "ExtensionActivationEvents", "event_type", "String", 64),
    (EXTENSION_MODEL, "ExtensionActivationEvents", "event_value", "String", 1024),
)


def _module_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _find_annassign(cls: ast.ClassDef, attr: str) -> ast.AnnAssign | None:
    for node in cls.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == attr
        ):
            return node
    return None


def _field_max_length(node: ast.AnnAssign) -> int | None:
    """Return ``max_length=`` int from a ``Field(...)`` AnnAssign value, or None."""
    value = node.value
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    if not (isinstance(func, ast.Name) and func.id == "Field"):
        return None
    for kw in value.keywords:
        if (
            kw.arg == "max_length"
            and isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, int)
        ):
            return kw.value.value
    return None


def _column_length(node: ast.AnnAssign, sa_type: str) -> int | None:
    """Return N from ``mapped_column(<sa_type>(N), ...)``, or None."""
    value = node.value
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    if not (isinstance(func, ast.Name) and func.id == "mapped_column"):
        return None
    if not value.args:
        return None
    first = value.args[0]
    if not isinstance(first, ast.Call):
        return None
    type_func = first.func
    if not (isinstance(type_func, ast.Name) and type_func.id == sa_type):
        return None
    if not first.args:
        return None
    arg0 = first.args[0]
    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, int):
        return arg0.value
    return None


# ---------------------------------------------------------------------------
# Invariants 1-3 — Pydantic field ``max_length`` caps
# ---------------------------------------------------------------------------


def test_pydantic_event_type_capped_at_64() -> None:
    path, cls_name, field, expected = PYDANTIC_FIELD_CAPS[0]
    tree = _module_tree(path)
    cls = _find_class(tree, cls_name)
    assert cls is not None, f"{path}: class `{cls_name}` missing"
    field_node = _find_annassign(cls, field)
    assert field_node is not None, f"`{cls_name}.{field}` annotated field missing"
    cap = _field_max_length(field_node)
    assert cap == expected, (
        f"`{cls_name}.{field}` expected `Field(..., max_length={expected})`; "
        f"got max_length={cap}"
    )


def test_pydantic_event_value_capped_at_1024() -> None:
    path, cls_name, field, expected = PYDANTIC_FIELD_CAPS[1]
    tree = _module_tree(path)
    cls = _find_class(tree, cls_name)
    assert cls is not None, f"{path}: class `{cls_name}` missing"
    field_node = _find_annassign(cls, field)
    assert field_node is not None, f"`{cls_name}.{field}` annotated field missing"
    cap = _field_max_length(field_node)
    assert cap == expected, (
        f"`{cls_name}.{field}` expected `Field(..., max_length={expected})`; "
        f"got max_length={cap}"
    )


def test_pydantic_activation_events_list_capped_at_512() -> None:
    path, cls_name, field, expected = PYDANTIC_FIELD_CAPS[2]
    tree = _module_tree(path)
    cls = _find_class(tree, cls_name)
    assert cls is not None, f"{path}: class `{cls_name}` missing"
    field_node = _find_annassign(cls, field)
    assert field_node is not None, f"`{cls_name}.{field}` annotated field missing"
    cap = _field_max_length(field_node)
    assert cap == expected, (
        f"`{cls_name}.{field}` expected `Field(..., max_length={expected})`; "
        f"got max_length={cap}"
    )


# ---------------------------------------------------------------------------
# Invariants 4-5 — SQLAlchemy ``String(N)`` column caps
# ---------------------------------------------------------------------------


def test_db_event_type_column_capped_at_64() -> None:
    path, cls_name, attr, sa_type, expected = DB_COLUMN_CAPS[0]
    tree = _module_tree(path)
    cls = _find_class(tree, cls_name)
    assert cls is not None, f"{path}: class `{cls_name}` missing"
    col_node = _find_annassign(cls, attr)
    assert col_node is not None, f"`{cls_name}.{attr}` column annotation missing"
    length = _column_length(col_node, sa_type)
    assert length == expected, (
        f"`{cls_name}.{attr}` expected "
        f"`mapped_column({sa_type}({expected}), ...)`; got "
        f"{sa_type}({length})"
    )


def test_db_event_value_column_capped_at_1024() -> None:
    path, cls_name, attr, sa_type, expected = DB_COLUMN_CAPS[1]
    tree = _module_tree(path)
    cls = _find_class(tree, cls_name)
    assert cls is not None, f"{path}: class `{cls_name}` missing"
    col_node = _find_annassign(cls, attr)
    assert col_node is not None, f"`{cls_name}.{attr}` column annotation missing"
    length = _column_length(col_node, sa_type)
    assert length == expected, (
        f"`{cls_name}.{attr}` expected "
        f"`mapped_column({sa_type}({expected}), ...)`; got "
        f"{sa_type}({length})"
    )


# ---------------------------------------------------------------------------
# Invariant 6 — vacuous-truth guard: every (class, attr) target must
# resolve to a real annotated field at its declared module path so a
# rename forces a table update rather than passing vacuously.
# ---------------------------------------------------------------------------


def test_activationevents_bound_targets_exist() -> None:
    missing: list[str] = []
    targets: list[tuple[Path, str, str]] = [
        (p, c, f) for (p, c, f, _) in PYDANTIC_FIELD_CAPS
    ] + [(p, c, a) for (p, c, a, _, _) in DB_COLUMN_CAPS]
    for module_path, cls_name, attr in targets:
        rel = module_path.relative_to(REPO_ROOT).as_posix()
        if not module_path.exists():
            missing.append(f"{rel} (module missing)")
            continue
        tree = _module_tree(module_path)
        cls = _find_class(tree, cls_name)
        if cls is None:
            missing.append(f"{rel}::{cls_name} (class missing)")
            continue
        if _find_annassign(cls, attr) is None:
            missing.append(f"{rel}::{cls_name}.{attr} (field missing)")
    assert not missing, (
        "activationEvents bound targets are out of sync; if a target "
        "was renamed/moved, update PYDANTIC_FIELD_CAPS / DB_COLUMN_CAPS. "
        "Missing:\n" + "\n".join(missing)
    )
