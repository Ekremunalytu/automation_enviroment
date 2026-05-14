"""W14-4 architecture gate: ``EvidenceEvent`` carries a
``@model_validator(mode='after')`` whose body enforces the
``_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS`` allowlist (closed mapping from
``kind`` to ``raw_context.event_class``).

Closes the HIGH-severity audit (`[FOLLOWUP
evidence-event-kind-raw-context-invariant]`). Pre-W14-4 the two fields
could drift (e.g. ``kind='network'`` + ``event_class='file'``, or
``kind='extension_host'`` paired with the default scenario
raw_context) and the ``packages/analysis_engine/rules/_common.py``
getattr-with-default accessors masked the mismatch as a silent false
negative for downstream detection rules. The post-fix
``@model_validator`` raises at ingest so producer drift cannot land.

The behavioral surface lives in
``tests/platform/contracts/test_raw_context_discriminated.py`` (one
positive case per kind in the 9-entry allowlist + 54 mismatch
parametrize + an unknown-kind reject + an edge case for the default
``raw_context`` falling on a non-scenario kind); this gate keeps a
future refactor from accidentally dropping the validator or shrinking
the allowlist.

Pattern modeled on the W14-2
``tests/architecture/test_output_signal_ts_guard.py`` body-invariant
gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_MODULE = (
    REPO_ROOT / "packages" / "analysis_contracts" / "contracts.py"
)
MODEL_CLASS = "EvidenceEvent"
VALIDATOR_DECORATOR = "model_validator"
VALIDATOR_MODE_KEYWORD = "mode"
EXPECTED_MODE = "after"
KIND_ATTR = "kind"
EVENT_CLASS_ATTR = "event_class"
RAW_CONTEXT_ATTR = "raw_context"
ALLOWLIST_NAME = "_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS"
REQUIRED_ALLOWLIST_KEYS = frozenset(
    {
        "scenario",
        "activation",
        "extension_host",
        "log",
        "ui_blocker",
        "network",
        "file",
        "process",
        "output_channel_appendline",
    }
)


def _module_tree() -> ast.Module:
    return ast.parse(CONTRACTS_MODULE.read_text(encoding="utf-8"))


def _find_class(module_tree: ast.Module, name: str) -> ast.ClassDef:
    for node in ast.walk(module_tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(
        f"class {name} not found in {CONTRACTS_MODULE.relative_to(REPO_ROOT)}"
    )


def _find_module_assignment(module_tree: ast.Module, name: str) -> ast.Assign | ast.AnnAssign:
    for stmt in module_tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return stmt
        elif (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == name
        ):
            return stmt
    raise AssertionError(
        f"module-level assignment {name} not found in "
        f"{CONTRACTS_MODULE.relative_to(REPO_ROOT)}"
    )


def _decorator_is_model_validator_after(decorator: ast.expr) -> bool:
    """Match ``@model_validator(mode='after')`` regardless of import alias."""
    if not isinstance(decorator, ast.Call):
        return False
    callee = decorator.func
    if isinstance(callee, ast.Name) and callee.id != VALIDATOR_DECORATOR:
        return False
    if (
        isinstance(callee, ast.Attribute)
        and callee.attr != VALIDATOR_DECORATOR
    ):
        return False
    for keyword in decorator.keywords:
        if keyword.arg == VALIDATOR_MODE_KEYWORD and isinstance(
            keyword.value, ast.Constant
        ):
            return keyword.value.value == EXPECTED_MODE
    return False


def _self_attribute(node: ast.AST, attr: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
        and node.attr == attr
    )


def _self_chained_attribute(node: ast.AST, head: str, tail: str) -> bool:
    """Match ``self.<head>.<tail>``."""
    return (
        isinstance(node, ast.Attribute)
        and node.attr == tail
        and _self_attribute(node.value, head)
    )


def _function_references_attribute(func: ast.FunctionDef, matcher) -> bool:
    return any(matcher(node) for node in ast.walk(func))


def _function_has_raise_value_error(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Raise):
            continue
        exc = node.exc
        if (
            isinstance(exc, ast.Call)
            and isinstance(exc.func, ast.Name)
            and exc.func.id == "ValueError"
        ):
            return True
    return False


def _function_references_allowlist(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Name) and node.id == ALLOWLIST_NAME:
            return True
    return False


def test_evidence_event_kind_allowlist_pinned() -> None:
    """The ``_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS`` allowlist exists at
    module scope and contains every kind that producer code or
    fixtures currently emit. Shrinking this set without an explicit
    audit would re-open the silent-drift surface.
    """
    tree = _module_tree()
    assign = _find_module_assignment(tree, ALLOWLIST_NAME)
    value = assign.value
    assert isinstance(value, ast.Dict), (
        f"{ALLOWLIST_NAME} in {CONTRACTS_MODULE.relative_to(REPO_ROOT)} must be "
        "a dict literal so the gate below can inspect its keys statically."
    )
    keys: set[str] = set()
    for key_node in value.keys:
        assert isinstance(key_node, ast.Constant) and isinstance(
            key_node.value, str
        ), f"{ALLOWLIST_NAME} keys must be string constants"
        keys.add(key_node.value)
    missing = REQUIRED_ALLOWLIST_KEYS - keys
    assert not missing, (
        f"{ALLOWLIST_NAME} in {CONTRACTS_MODULE.relative_to(REPO_ROOT)} must "
        f"include every producer kind; missing: {sorted(missing)}"
    )


def test_evidence_event_kind_invariant_validator_exists() -> None:
    """``EvidenceEvent`` must define a ``@model_validator(mode='after')``
    whose body references both ``self.kind`` (via
    ``_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS`` lookup) and
    ``self.raw_context.event_class``, and raises ``ValueError`` when
    the invariant breaks. Without this validator the discriminated
    union allows the two fields to drift silently.
    """
    tree = _module_tree()
    cls = _find_class(tree, MODEL_CLASS)

    matched: list[str] = []
    for stmt in cls.body:
        if not isinstance(stmt, ast.FunctionDef):
            continue
        if not any(
            _decorator_is_model_validator_after(decorator)
            for decorator in stmt.decorator_list
        ):
            continue
        references_kind = _function_references_attribute(
            stmt, lambda n: _self_attribute(n, KIND_ATTR)
        )
        references_event_class = _function_references_attribute(
            stmt,
            lambda n: _self_chained_attribute(
                n, RAW_CONTEXT_ATTR, EVENT_CLASS_ATTR
            ),
        )
        references_allowlist = _function_references_allowlist(stmt)
        raises_value_error = _function_has_raise_value_error(stmt)
        if (
            references_kind
            and references_event_class
            and references_allowlist
            and raises_value_error
        ):
            matched.append(stmt.name)

    assert matched, (
        f"{MODEL_CLASS} in {CONTRACTS_MODULE.relative_to(REPO_ROOT)} must "
        f"define a @{VALIDATOR_DECORATOR}(mode={EXPECTED_MODE!r}) method "
        f"that references self.{KIND_ATTR}, "
        f"self.{RAW_CONTEXT_ATTR}.{EVENT_CLASS_ATTR}, the "
        f"{ALLOWLIST_NAME} mapping, and raises ValueError on mismatch "
        "(W14-4 [FOLLOWUP evidence-event-kind-raw-context-invariant])."
    )
