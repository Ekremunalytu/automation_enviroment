"""W14-2 architecture gate: ``int(...)`` calls inside the marketplace report
builder must NOT consume extension-controlled ``automation_health`` values
without ``_safe_int_coerce`` routing.

Closes the M11 audit (`[FOLLOWUP
codex-2026-05-10-M11-report-health-malformed-types`]).

The canonical defensive coercer is ``_safe_int_coerce()`` in
``workflows/marketplace/analysis_reports.py``. After W14-2 the report
builder routes every ``automation_health.get(...)``-sourced numeric
field through that helper, so a malicious extension that writes
``target_activation_count: "not-an-int"`` cannot blow up the report with
``ValueError``.

Two invariants are pinned here (W13-6 pattern mirror):

1. ``test_safe_int_coercer_swallows_typeerror_valueerror_overflow`` — the
   coercer body itself catches ``(TypeError, ValueError, OverflowError)``
   at least once. Without this the routing gate below is a syntactic shell.

2. ``test_int_calls_in_report_builder_route_through_coercer`` — every
   ``int(...)`` call inside ``analysis_reports.build_report_messages``
   must NOT take an ``automation_health.get(...)`` expression as its
   first argument. The call must route through ``_safe_int_coerce``
   (or the value must come from a non-``automation_health`` source).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_MODULE = REPO_ROOT / "workflows" / "marketplace" / "analysis_reports.py"
COERCER_NAME = "_safe_int_coerce"
BUILDER_NAME = "build_report_messages"


def _is_int_call_on_automation_health_get(node: ast.AST) -> bool:
    """Return True if ``node`` is ``int(automation_health.get(...))``."""
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "int"
        and node.args
    ):
        return False
    arg = node.args[0]
    # `automation_health.get(...)` direct
    if (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Attribute)
        and arg.func.attr == "get"
        and isinstance(arg.func.value, ast.Name)
        and arg.func.value.id == "automation_health"
    ):
        return True
    # `automation_health.get(...) or 0` — pre-W14-2 shape (BoolOp)
    if isinstance(arg, ast.BoolOp):
        for value in arg.values:
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and value.func.attr == "get"
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "automation_health"
            ):
                return True
    return False


def test_safe_int_coercer_swallows_typeerror_valueerror_overflow() -> None:
    """The defensive coercer body must catch the three coercion error
    types extension-controlled scalars can produce.

    Without this invariant, ``_safe_int_coerce`` would re-raise the same
    ``ValueError`` / ``TypeError`` / ``OverflowError`` the raw ``int(...)``
    call did, and the routing gate below would be a syntactic shell.
    """
    tree = ast.parse(REPORTS_MODULE.read_text(encoding="utf-8"))
    coercer_func: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == COERCER_NAME:
            coercer_func = node
            break
    assert coercer_func is not None, (
        f"{COERCER_NAME}() must be defined in "
        f"{REPORTS_MODULE.relative_to(REPO_ROOT)} — the W14-2 M11 fix "
        "depends on it as the single chokepoint."
    )

    caught_exception_names: set[str] = set()
    for inner in ast.walk(coercer_func):
        if isinstance(inner, ast.ExceptHandler) and inner.type is not None:
            handler_types: list[ast.expr] = (
                list(inner.type.elts)
                if isinstance(inner.type, ast.Tuple)
                else [inner.type]
            )
            for handler_type in handler_types:
                if isinstance(handler_type, ast.Name):
                    caught_exception_names.add(handler_type.id)

    required = {"TypeError", "ValueError", "OverflowError"}
    missing = required - caught_exception_names
    assert not missing, (
        f"{COERCER_NAME}() in {REPORTS_MODULE.relative_to(REPO_ROOT)} must "
        f"catch all of {sorted(required)} so adversarial scalars never "
        f"escape the helper. Missing: {sorted(missing)}; "
        f"caught: {sorted(caught_exception_names)}."
    )


def test_int_calls_in_report_builder_route_through_coercer() -> None:
    """No ``int(automation_health.get(...))`` patterns may survive inside
    ``build_report_messages``. The W14-2 fix rewrites that single call
    site to ``_safe_int_coerce(automation_health.get(...))``; if a future
    edit re-introduces the raw cast, this gate fires.
    """
    tree = ast.parse(REPORTS_MODULE.read_text(encoding="utf-8"))
    builder_func: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == BUILDER_NAME:
            builder_func = node
            break
    assert builder_func is not None, (
        f"{BUILDER_NAME}() must be defined in {REPORTS_MODULE.relative_to(REPO_ROOT)}."
    )

    violations: list[str] = []
    for node in ast.walk(builder_func):
        if _is_int_call_on_automation_health_get(node):
            violations.append(
                f"{REPORTS_MODULE.relative_to(REPO_ROOT)}:{node.lineno}: "
                f"int(automation_health.get(...)) is not type-safe; "
                f"route through {COERCER_NAME}()"
            )

    assert not violations, (
        f"Every numeric cast on automation_health fields in {BUILDER_NAME}() "
        f"must route through {COERCER_NAME}() (W14-2 M11 invariant). "
        "Violations:\n" + "\n".join(violations)
    )
