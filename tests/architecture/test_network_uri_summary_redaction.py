"""W14-3 architecture gate: every ``path=`` / ``summary=`` keyword
assignment in `runtime_capture/network.py` must route through
``redact_secrets()``.

Closes the M13 audit (`[FOLLOWUP
codex-2026-05-10-M13-network-uri-summary-redaction]`).

The canonical redaction point is ``redact_secrets()`` imported at the
top of ``executor/flows/playwright/runtime_capture/network.py:12``.
After W14-3, ``parse_tshark_event_line`` sources both the ``path`` and
``summary`` fields of ``NetworkEvent`` from local variables that flow
through ``redact_secrets(...)`` first, so a malicious extension cannot
surface bearer tokens / AWS keys / DB URLs verbatim in the persisted
ActivationReport.

Two invariants are pinned here (W13-6 pattern mirror):

1. ``test_network_module_imports_redact_secrets`` — the module must
   carry the ``redact_secrets`` import; without it the routing gate
   below is a syntactic shell.

2. ``test_path_and_summary_assignments_route_through_redact_secrets`` —
   every ``path=<expr>`` / ``summary=<expr>`` keyword arg in the
   ``NetworkEvent(...)`` constructor call inside this module must source
   the value from one of:

   a. A ``Call`` to ``redact_secrets(...)`` directly.
   b. A ``Name`` access on a local variable in the same function that
      was assigned from ``redact_secrets(...)``.
   c. The empty-string ``Constant`` (non-tshark-derived events can
      legitimately leave the field empty).

Pattern modeled on the W13-6
``tests/architecture/test_arguments_preview_redaction.py`` gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NETWORK_MODULE = (
    REPO_ROOT
    / "executor"
    / "flows"
    / "playwright"
    / "runtime_capture"
    / "network.py"
)
TARGET_FIELDS = {"path", "summary"}
ALLOWED_REDACT_CALLS = {"redact_secrets"}


def _value_is_redact_call(value: ast.AST) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in ALLOWED_REDACT_CALLS
    )


def _value_is_empty_string(value: ast.AST) -> bool:
    return isinstance(value, ast.Constant) and value.value == ""


def _value_is_redact_local(value: ast.AST, redact_vars: set[str]) -> bool:
    return isinstance(value, ast.Name) and value.id in redact_vars


def _collect_redact_local_names(func_node: ast.AST) -> set[str]:
    """Return the set of local variables assigned from ``redact_secrets(...)``."""
    redact_vars: set[str] = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign) and _value_is_redact_call(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    redact_vars.add(target.id)
    return redact_vars


def _check_value(value: ast.AST, redact_vars: set[str]) -> bool:
    return (
        _value_is_redact_call(value)
        or _value_is_empty_string(value)
        or _value_is_redact_local(value, redact_vars)
    )


def test_network_module_imports_redact_secrets() -> None:
    """The module must carry the ``redact_secrets`` import.

    Without this, the routing gate below is a syntactic shell: keyword
    assignments could correctly call something named ``redact_secrets``
    that resolves to an unredacted shim in a different module.
    """
    tree = ast.parse(NETWORK_MODULE.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
    assert "redact_secrets" in imported_names, (
        f"{NETWORK_MODULE.relative_to(REPO_ROOT)} must import "
        "`redact_secrets` from `packages.analysis_contracts.evidence`."
    )


def test_path_and_summary_assignments_route_through_redact_secrets() -> None:
    """Every ``path=`` / ``summary=`` keyword assignment must come from
    a redacting source.
    """
    tree = ast.parse(NETWORK_MODULE.read_text(encoding="utf-8"))
    violations: list[str] = []

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        redact_vars = _collect_redact_local_names(func)
        for node in ast.walk(func):
            if (
                isinstance(node, ast.keyword)
                and node.arg in TARGET_FIELDS
                and not _check_value(node.value, redact_vars)
            ):
                violations.append(
                    f"{NETWORK_MODULE.relative_to(REPO_ROOT)}:"
                    f"{node.value.lineno}: {node.arg}=<expr> not routed "
                    "through redact_secrets()"
                )

    assert not violations, (
        "Every NetworkEvent path= / summary= keyword assignment must route "
        f"through redact_secrets() (W14-3 M13 invariant). Violations:\n"
        + "\n".join(violations)
    )
