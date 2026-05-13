"""W14-5 architecture gate: enforce the ``extrace.*`` logger factory
across the executor and workflows subtrees.

Two invariants:

1. **No raw ``logging.getLogger(...)`` calls** under ``executor/``,
   ``workflows/marketplace/``, or ``workflows/security_settings/``
   (the consolidation scope from W14-5 sub-commit 1). The only
   exempt module is the factory itself (``appcore/logging.py``)
   which intentionally delegates to ``logging.getLogger`` after
   validating the namespace.
2. **Every ``get_extrace_logger(...)`` call** in the scanned subtrees
   passes a string literal whose value starts with one of the
   approved prefixes (``extrace.executor.``, ``extrace.workflows.``,
   ``extrace.appcore.``, ``extrace.packages.``).

Modeled on the W14-2 / W14-4 AST gate pattern: parse → walk → collect
violations → assert with a formatted report.

The closed taxonomy is documented in
``documents/adrs/0010-extrace-executor-logger-consolidation.md``;
adding a new prefix requires updating both this gate and that ADR.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNED_DIRS: tuple[str, ...] = (
    "executor",
    "workflows/marketplace",
    "workflows/security_settings",
)
EXEMPT_PATHS: frozenset[str] = frozenset({"appcore/logging.py"})
APPROVED_PREFIXES: tuple[str, ...] = (
    "extrace.executor.",
    "extrace.workflows.",
    "extrace.appcore.",
    "extrace.packages.",
)
FACTORY_FUNCTION_NAME = "get_extrace_logger"


def _is_logging_get_logger_call(node: ast.Call) -> bool:
    """Match ``logging.getLogger(...)`` (Attribute) or bare ``getLogger(...)``
    (Name) — both forms after ``import logging`` or
    ``from logging import getLogger``."""
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr != "getLogger":
            return False
        return isinstance(func.value, ast.Name) and func.value.id == "logging"
    if isinstance(func, ast.Name):
        return func.id == "getLogger"
    return False


def _is_factory_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == FACTORY_FUNCTION_NAME
    if isinstance(func, ast.Attribute):
        return func.attr == FACTORY_FUNCTION_NAME
    return False


def _string_literal_first_arg(node: ast.Call) -> str | None:
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _iter_scanned_files() -> list[Path]:
    paths: list[Path] = []
    for scanned in SCANNED_DIRS:
        paths.extend(sorted((REPO_ROOT / scanned).rglob("*.py")))
    return paths


def _module_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


# ---------------------------------------------------------------------------
# Invariant 1 — no raw logging.getLogger(...) under the consolidation scope
# ---------------------------------------------------------------------------


def test_no_raw_logging_get_logger_in_consolidation_scope() -> None:
    violations: list[str] = []
    for module_path in _iter_scanned_files():
        rel = _module_label(module_path)
        if rel in EXEMPT_PATHS:
            continue
        try:
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_logging_get_logger_call(node):
                violations.append(f"{rel}:{node.lineno}")
    assert not violations, (
        "Direct logging.getLogger(...) / bare getLogger(...) calls are "
        "forbidden under executor/, workflows/marketplace/, and "
        "workflows/security_settings/ (W14-5 §11.10 GOAL). Use "
        "`appcore.logging.get_extrace_logger(...)` so the structured-field "
        "contract (run_id, executor_fingerprint) holds. Violations:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Invariant 2 — every get_extrace_logger(...) call uses a string-literal name
# starting with an approved prefix
# ---------------------------------------------------------------------------


def test_factory_call_sites_use_approved_prefix_literal() -> None:
    violations: list[str] = []
    for module_path in _iter_scanned_files():
        rel = _module_label(module_path)
        if rel in EXEMPT_PATHS:
            continue
        try:
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and _is_factory_call(node)):
                continue
            literal = _string_literal_first_arg(node)
            if literal is None:
                violations.append(
                    f"{rel}:{node.lineno} (non-literal logger name; "
                    "the gate cannot verify the namespace statically)"
                )
                continue
            if not literal.startswith(APPROVED_PREFIXES):
                violations.append(
                    f"{rel}:{node.lineno} (name {literal!r} not in "
                    f"approved prefix list {APPROVED_PREFIXES})"
                )
    assert not violations, (
        "get_extrace_logger(...) calls must pass a string literal starting "
        "with one of the approved area prefixes "
        f"({APPROVED_PREFIXES}). See ADR 0010. Violations:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Vacuous-truth guard — at least one production site uses the factory so the
# gate above does not pass trivially when no callers exist.
# ---------------------------------------------------------------------------


def test_at_least_one_factory_call_site_exists() -> None:
    """If migration is reverted or the factory becomes unused, this guard
    flips RED so the consolidation invariant cannot pass vacuously."""
    call_count = 0
    for module_path in _iter_scanned_files():
        if _module_label(module_path) in EXEMPT_PATHS:
            continue
        try:
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_factory_call(node):
                call_count += 1
    assert call_count >= 6, (
        "Expected at least 6 production sites to call get_extrace_logger "
        "(W14-5 sub-commit 1 migrates 6 logger sites in workflows/marketplace "
        "and workflows/security_settings); the gate above would pass "
        f"vacuously without callers. Counted {call_count}."
    )


# ---------------------------------------------------------------------------
# Self-tests on the detector helpers
# ---------------------------------------------------------------------------


def _scan(source: str, predicate) -> list[int]:
    tree = ast.parse(source)
    out: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and predicate(node):
            out.append(node.lineno)
    return out


def test_detector_flags_attribute_form_logging_get_logger() -> None:
    src = "import logging\nlogger = logging.getLogger(__name__)\n"
    assert _scan(src, _is_logging_get_logger_call) == [2]


def test_detector_flags_bare_get_logger() -> None:
    src = "from logging import getLogger\nlogger = getLogger(__name__)\n"
    assert _scan(src, _is_logging_get_logger_call) == [2]


def test_detector_ignores_unrelated_logging_attribute() -> None:
    """``logging.INFO`` etc. are constants, not invocations — the
    detector must not false-fire on attribute access without a call."""
    src = "import logging\nlevel = logging.INFO\n"
    assert _scan(src, _is_logging_get_logger_call) == []


def test_detector_matches_factory_call_via_attribute() -> None:
    src = "from appcore import logging as _l\n_l.get_extrace_logger('extrace.appcore.test')\n"
    assert _scan(src, _is_factory_call) == [2]


def test_string_literal_first_arg_returns_value() -> None:
    src = "get_extrace_logger('extrace.executor.host')\n"
    tree = ast.parse(src)
    call = next(
        node for node in ast.walk(tree) if isinstance(node, ast.Call)
    )
    assert _string_literal_first_arg(call) == "extrace.executor.host"


def test_string_literal_first_arg_returns_none_for_name_arg() -> None:
    src = "get_extrace_logger(some_var)\n"
    tree = ast.parse(src)
    call = next(
        node for node in ast.walk(tree) if isinstance(node, ast.Call)
    )
    assert _string_literal_first_arg(call) is None
