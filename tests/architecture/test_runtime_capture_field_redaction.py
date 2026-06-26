"""Architecture gate: extension-controlled report-event fields route through
``redact_secrets()`` at construction.

Closes ``[BUG report-field-redaction-completeness]`` (extrace-audit 2026-06-15):
redaction was enforced per-field on ``NetworkEvent`` (W14-3) but three sibling
sinks surfaced extension-controlled strings verbatim —

  - ``ProcessEvent.command`` / ``cwd`` / ``summary``
    (``runtime_capture/extension_host_strace_parse.py``),
  - ``FileEvent.path`` / ``secondary_path`` / ``summary``
    (``runtime_capture/filesystem.py``),
  - ``LogStreamEntry.message`` / ``activation_event``
    (``monitor/scenario_accountant.py``).

``redact_secrets`` is a no-op on ordinary paths/commands and masks only
secret-shaped substrings (PEM / bearer / api_key / db_url / aws), so routing
these fields through it is forensic-preserving defense-in-depth. This gate pins
every listed-field keyword assignment in the named constructor to a redacting
source. Pattern modeled on ``test_network_uri_summary_redaction.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_REDACT_CALLS = {"redact_secrets"}

# (module path, constructor name, redaction-required keyword fields)
_TARGETS = [
    (
        "executor/flows/playwright/runtime_capture/extension_host_strace_parse.py",
        "ProcessEvent",
        {"command", "cwd", "summary"},
    ),
    (
        "executor/flows/playwright/runtime_capture/filesystem.py",
        "FileEvent",
        {"path", "secondary_path", "summary"},
    ),
    (
        "executor/flows/playwright/monitor/scenario_accountant.py",
        "LogStreamEntry",
        {"message", "activation_event"},
    ),
]


def _value_is_redact_call(value: ast.AST) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in ALLOWED_REDACT_CALLS
    )


def _value_is_empty_string(value: ast.AST) -> bool:
    return isinstance(value, ast.Constant) and value.value == ""


def _collect_redact_local_names(func_node: ast.AST) -> set[str]:
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
        or (isinstance(value, ast.Name) and value.id in redact_vars)
    )


@pytest.mark.parametrize(
    ("module_rel", "constructor", "fields"),
    _TARGETS,
    ids=[t[1] for t in _TARGETS],
)
def test_module_imports_redact_secrets(
    module_rel: str, constructor: str, fields: set[str]
) -> None:
    tree = ast.parse((REPO_ROOT / module_rel).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    assert "redact_secrets" in imported, (
        f"{module_rel} must import redact_secrets so the {constructor} "
        "redaction gate is not a syntactic shell."
    )


@pytest.mark.parametrize(
    ("module_rel", "constructor", "fields"),
    _TARGETS,
    ids=[t[1] for t in _TARGETS],
)
def test_constructor_fields_route_through_redact_secrets(
    module_rel: str, constructor: str, fields: set[str]
) -> None:
    tree = ast.parse((REPO_ROOT / module_rel).read_text(encoding="utf-8"))
    violations: list[str] = []
    constructions = 0

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        redact_vars = _collect_redact_local_names(func)
        for call in ast.walk(func):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == constructor
            ):
                continue
            constructions += 1
            for kw in call.keywords:
                if kw.arg in fields and not _check_value(kw.value, redact_vars):
                    violations.append(
                        f"{module_rel}:{kw.value.lineno}: {constructor}({kw.arg}=...) "
                        "not routed through redact_secrets()"
                    )

    assert constructions, (
        f"no {constructor}(...) constructions found in {module_rel}; the gate "
        "must point at a module that actually builds it."
    )
    assert not violations, (
        f"Every {constructor} {sorted(fields)} keyword assignment must route "
        "through redact_secrets() (report-field-redaction-completeness). "
        "Violations:\n" + "\n".join(violations)
    )
