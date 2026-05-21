"""W14-2 architecture gate: ``datetime.fromtimestamp()`` inside the
output-signal module must be fed an epoch that flowed through the
``_coerce_safe_epoch_s`` guard.

Closes the M4 + M7 audit (`[FOLLOWUP
codex-2026-05-10-M4-M7-output-ts-range-validation]`).

The canonical sanitizer is ``_coerce_safe_epoch_s()`` in
``executor/flows/playwright/signals/output.py``. After W14-2 the only
``datetime.fromtimestamp()`` call site in that module
(``_format_epoch_ms``) sources its epoch from a local variable populated
by ``_coerce_safe_epoch_s(...)``, so adversarial ``ts: 1e999`` / ``NaN``
inputs cannot abort the call with ``OverflowError`` / ``OSError`` /
``ValueError``.

Two invariants are pinned here (W13-6 pattern mirror):

1. ``test_safe_epoch_coercer_caps_at_safe_window`` — the coercer's body
   itself contains both a ``math.isfinite(...)`` check AND a range
   comparison against ``_MIN_SAFE_EPOCH_S`` / ``_MAX_SAFE_EPOCH_S``.
   Without these the routing gate below is a syntactic shell.

2. ``test_fromtimestamp_calls_route_through_coercer`` — every
   ``datetime.fromtimestamp(...)`` call inside ``signals/output.py``
   sources its argument from one of:

   a. A ``Call`` to ``_coerce_safe_epoch_s(...)`` directly.
   b. A ``Name`` access on a local variable in the same function that was
      assigned from ``_coerce_safe_epoch_s(...)``.

Defense-in-depth sibling to the behavioral regression tests:

- ``tests/security/test_output_signal_ts_range.py``

Pattern modeled on the W13-6
``tests/architecture/test_arguments_preview_redaction.py`` gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIGNALS_OUTPUT_MODULE = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "signals" / "output.py"
)
COERCER_NAME = "_coerce_safe_epoch_s"
FROMTIMESTAMP_ATTR = "fromtimestamp"


def _is_fromtimestamp_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == FROMTIMESTAMP_ATTR
    )


def _is_coercer_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == COERCER_NAME
    )


def _collect_coercer_local_names(func_node: ast.AST) -> set[str]:
    """Return the set of local variable names assigned from the coercer call."""
    coercer_vars: set[str] = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign) and _is_coercer_call(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    coercer_vars.add(target.id)
    return coercer_vars


def _argument_is_routed_through_coercer(arg: ast.AST, coercer_vars: set[str]) -> bool:
    if _is_coercer_call(arg):
        return True
    return isinstance(arg, ast.Name) and arg.id in coercer_vars


def test_safe_epoch_coercer_caps_at_safe_window() -> None:
    """The coercer body must apply both finiteness and range bounds.

    Without this invariant the routing gate below is a syntactic shell:
    ``fromtimestamp`` calls would correctly flow through
    ``_coerce_safe_epoch_s`` yet still raise on adversarial values because
    the coercer would let them pass. Pin the body so the architecture
    promise actually holds.
    """
    tree = ast.parse(SIGNALS_OUTPUT_MODULE.read_text(encoding="utf-8"))
    coercer_func: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == COERCER_NAME:
            coercer_func = node
            break
    assert coercer_func is not None, (
        f"{COERCER_NAME}() must be defined in "
        f"{SIGNALS_OUTPUT_MODULE.relative_to(REPO_ROOT)} — the W14-2 M4-M7 fix "
        "depends on it as the single chokepoint."
    )

    has_isfinite_call = False
    has_range_check = False
    for inner in ast.walk(coercer_func):
        # `math.isfinite(...)` check
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "isfinite"
        ):
            has_isfinite_call = True
        # Range comparison against the safe-window constants (any side)
        if isinstance(inner, ast.Compare):
            referenced_names = {
                operand.id
                for operand in [inner.left, *inner.comparators]
                if isinstance(operand, ast.Name)
            }
            if referenced_names & {"_MIN_SAFE_EPOCH_S", "_MAX_SAFE_EPOCH_S"}:
                has_range_check = True

    assert has_isfinite_call, (
        f"{COERCER_NAME}() in {SIGNALS_OUTPUT_MODULE.relative_to(REPO_ROOT)} "
        "must invoke math.isfinite() to reject inf/nan inputs."
    )
    assert has_range_check, (
        f"{COERCER_NAME}() in {SIGNALS_OUTPUT_MODULE.relative_to(REPO_ROOT)} "
        "must compare against _MIN_SAFE_EPOCH_S / _MAX_SAFE_EPOCH_S to bound "
        "the safe window."
    )


def test_fromtimestamp_calls_route_through_coercer() -> None:
    """Every ``datetime.fromtimestamp(...)`` call inside
    ``signals/output.py`` must source its argument from
    ``_coerce_safe_epoch_s(...)`` (directly or via a same-function local).
    """
    tree = ast.parse(SIGNALS_OUTPUT_MODULE.read_text(encoding="utf-8"))
    violations: list[str] = []

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        coercer_vars = _collect_coercer_local_names(func)
        for node in ast.walk(func):
            if not _is_fromtimestamp_call(node):
                continue
            if not node.args:
                violations.append(
                    f"{SIGNALS_OUTPUT_MODULE.relative_to(REPO_ROOT)}:"
                    f"{node.lineno}: fromtimestamp() called with no arguments"
                )
                continue
            first_arg = node.args[0]
            if not _argument_is_routed_through_coercer(first_arg, coercer_vars):
                violations.append(
                    f"{SIGNALS_OUTPUT_MODULE.relative_to(REPO_ROOT)}:"
                    f"{node.lineno}: datetime.fromtimestamp(<expr>) not routed "
                    f"through {COERCER_NAME}() in function {func.name!r}"
                )

    assert not violations, (
        f"Every datetime.fromtimestamp() call in "
        f"{SIGNALS_OUTPUT_MODULE.relative_to(REPO_ROOT)} must source its "
        f"argument from {COERCER_NAME}() (W14-2 M4-M7 invariant). "
        "Violations:\n" + "\n".join(violations)
    )
