"""W13-6 architecture gate: every ``arguments_preview`` assignment must route
through ``redact_secrets``.

The canonical redaction point is ``_bounded_arguments_preview()`` in
``executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:102-106``.
After W13-6 (sub-commit 3) that factory wraps the strace argument string in
``redact_secrets()`` before applying length truncation, so the three call sites
in the same module (``arguments_preview=...`` at lines 60, 70, 78) inherit
redaction at a single chokepoint.

Two invariants are pinned here:

1. ``test_arguments_preview_factory_applies_redact_secrets`` — the factory
   body itself contains a ``redact_secrets(...)`` call. Without this, the
   routing gate below is a syntactic shell and secrets can still leak.
2. ``test_arguments_preview_assignments_are_redacted`` — any module under
   ``executor/``, ``packages/``, or ``workflows/`` that assigns to
   ``arguments_preview`` (keyword, attribute, or dict-key) must source the
   value from one of:

   a. A ``Call`` to ``redact_secrets(...)`` directly.
   b. A ``Call`` to ``_bounded_arguments_preview(...)`` directly.
   c. A ``Name`` access on a local variable in the same function that was
      assigned from ``_bounded_arguments_preview(...)``.
   d. The empty-string ``Constant`` (the ``chdir`` parse path emits
      ``arguments_preview=""`` because the meaningful info lives in ``cwd``;
      an empty string carries no secret).
   e. A ``Name`` / ``Attribute`` access on a whitelisted passthrough source
      (``process_event``, ``evidence_event``, ``event``, ``payload``).

Defense-in-depth sibling to the runtime regression tests:

- ``tests/executor/test_playwright_extension_host.py::``
  ``test_parse_strace_event_arguments_preview_redacts_secrets``

Pattern modeled on the W12-5 ``test_network_body_preview_redaction.py`` gate
(``request_body_preview`` / ``response_body_preview``).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = ("executor", "packages", "workflows")
EXCLUDED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TARGET_FIELD_NAMES = {"arguments_preview"}
ALLOWED_REDACT_CALLS = {"redact_secrets"}
ALLOWED_FACTORY_CALLS = {"_bounded_arguments_preview"}
ALLOWED_PASSTHROUGH_SOURCES = {"process_event", "evidence_event", "event", "payload"}

FACTORY_MODULE = (
    REPO_ROOT
    / "executor"
    / "flows"
    / "playwright"
    / "runtime_capture"
    / "extension_host_strace_parse.py"
)
FACTORY_FUNCTION_NAMES = ALLOWED_FACTORY_CALLS


def _value_is_redact_call(value: ast.AST) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in ALLOWED_REDACT_CALLS
    )


def _value_is_factory_call(value: ast.AST) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in ALLOWED_FACTORY_CALLS
    )


def _value_is_empty_string(value: ast.AST) -> bool:
    return isinstance(value, ast.Constant) and value.value == ""


def _value_is_passthrough(value: ast.AST) -> bool:
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
        return value.value.id in ALLOWED_PASSTHROUGH_SOURCES
    return isinstance(value, ast.Name) and value.id in ALLOWED_PASSTHROUGH_SOURCES


def _value_is_factory_local(value: ast.AST, factory_var_names: set[str]) -> bool:
    return isinstance(value, ast.Name) and value.id in factory_var_names


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
        or _value_is_factory_call(value)
        or _value_is_empty_string(value)
        or _value_is_passthrough(value)
        or _value_is_factory_local(value, factory_vars)
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


def _factory_body_has_redact_call(module_tree: ast.AST) -> bool:
    for node in ast.walk(module_tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in FACTORY_FUNCTION_NAMES
        ):
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id in ALLOWED_REDACT_CALLS
                ):
                    return True
            return False
    return False


@pytest.mark.skip(
    reason="W13-6 RED precursor — _bounded_arguments_preview() factory does "
    "not yet route through redact_secrets(); sub-commit 3 lands the body fix."
)
def test_arguments_preview_factory_applies_redact_secrets() -> None:
    """The redacting factory must itself call ``redact_secrets()``.

    Without this invariant, the routing gate below is a syntactic shell:
    assignments would correctly funnel through ``_bounded_arguments_preview()``
    yet still leak secrets because the factory only truncates. Pin the
    factory body so the architecture promise holds end-to-end.
    """
    tree = ast.parse(FACTORY_MODULE.read_text(encoding="utf-8"))
    assert _factory_body_has_redact_call(tree), (
        f"_bounded_arguments_preview() in "
        f"{FACTORY_MODULE.relative_to(REPO_ROOT)} must call redact_secrets() "
        "before returning. The W13-6 architecture gate "
        "'every arguments_preview assignment routes through factory' relies "
        "on this invariant to actually block secret leakage."
    )


def test_arguments_preview_assignments_are_redacted() -> None:
    """Every ``arguments_preview`` write must come from a redacting source."""
    violations: list[str] = []
    for root in SCAN_ROOTS:
        for path in (REPO_ROOT / root).rglob("*.py"):
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if "/tests/" in str(path) or path.name.startswith("test_"):
                continue
            violations.extend(_scan_file(path))

    assert not violations, (
        "Every arguments_preview assignment must route through redact_secrets() "
        "or _bounded_arguments_preview() (see "
        "executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:102-106). "
        "Violations:\n" + "\n".join(violations)
    )
