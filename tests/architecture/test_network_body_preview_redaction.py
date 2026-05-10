"""W12-5 architecture gate: every *_body_preview assignment must route through redact_secrets.

The canonical redaction point is ``_bounded_body_metadata()`` in
``executor/flows/playwright/runtime_capture/network.py:140-158``, which wraps
body bytes in ``redact_secrets()`` (line 156) before returning the ``preview``
field of its TypedDict result.

This gate fails if any module under ``executor/``, ``packages/``, or
``workflows/`` assigns to ``request_body_preview`` or
``response_body_preview`` (as a keyword argument, attribute write, or
dict-key assignment) where the value is not:

1. A ``Call`` to ``redact_secrets(...)`` directly, or
2. A ``Subscript`` of a name produced by ``_bounded_body_metadata(...)``
   in the same function, or
3. A ``Name``/``Attribute`` access on one of the whitelisted passthrough
   sources (``network_event``, ``evidence_event``, ``event``, ``payload``).

Defense-in-depth sibling to the runtime regression tests:

- ``tests/platform/security/test_output_signals_redaction.py`` (output signals)
- ``tests/executor/test_playwright_monitor_runtime.py``::
  ``test_parse_tshark_event_line_redacts_secrets_in_body_preview``
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = ("executor", "packages", "workflows")
EXCLUDED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TARGET_FIELD_NAMES = {"request_body_preview", "response_body_preview"}
ALLOWED_REDACT_CALLS = {"redact_secrets"}
ALLOWED_FACTORY_CALLS = {"_bounded_body_metadata"}
ALLOWED_PASSTHROUGH_SOURCES = {"network_event", "evidence_event", "event", "payload"}


def _value_is_redact_call(value: ast.AST) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in ALLOWED_REDACT_CALLS
    )


def _value_is_passthrough(value: ast.AST) -> bool:
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
        return value.value.id in ALLOWED_PASSTHROUGH_SOURCES
    return isinstance(value, ast.Name) and value.id in ALLOWED_PASSTHROUGH_SOURCES


def _value_is_factory_subscript(value: ast.AST, factory_var_names: set[str]) -> bool:
    if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
        return value.value.id in factory_var_names
    return False


def _collect_factory_vars(func_node: ast.AST) -> set[str]:
    vars_: set[str] = set()
    for node in ast.walk(func_node):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id in ALLOWED_FACTORY_CALLS
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    vars_.add(target.id)
    return vars_


def _check_value(value: ast.AST, factory_vars: set[str]) -> bool:
    return (
        _value_is_redact_call(value)
        or _value_is_passthrough(value)
        or _value_is_factory_subscript(value, factory_vars)
    )


def _scan_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        factory_vars = _collect_factory_vars(func)
        for node in ast.walk(func):
            if (
                isinstance(node, ast.keyword)
                and node.arg in TARGET_FIELD_NAMES
                and not _check_value(node.value, factory_vars)
            ):
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}:{node.value.lineno}: "
                    f"{node.arg}=<expr> not routed through redact_secrets"
                )
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and target.attr in TARGET_FIELD_NAMES
                        and not _check_value(node.value, factory_vars)
                    ):
                        violations.append(
                            f"{path.relative_to(REPO_ROOT)}:{node.lineno}: "
                            f".{target.attr} = <expr> not routed through redact_secrets"
                        )
                    if (
                        isinstance(target, ast.Subscript)
                        and isinstance(target.slice, ast.Constant)
                        and target.slice.value in TARGET_FIELD_NAMES
                        and not _check_value(node.value, factory_vars)
                    ):
                        violations.append(
                            f"{path.relative_to(REPO_ROOT)}:{node.lineno}: "
                            f"d[{target.slice.value!r}] = <expr> not routed through redact_secrets"
                        )

    return violations


def test_body_preview_assignments_are_redacted() -> None:
    violations: list[str] = []
    for root in SCAN_ROOTS:
        for path in (REPO_ROOT / root).rglob("*.py"):
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if "/tests/" in str(path) or path.name.startswith("test_"):
                continue
            violations.extend(_scan_file(path))

    assert not violations, (
        "Every *_body_preview assignment must route through redact_secrets() "
        "or _bounded_body_metadata() (see "
        "executor/flows/playwright/runtime_capture/network.py:140-158). "
        "Violations:\n" + "\n".join(violations)
    )
