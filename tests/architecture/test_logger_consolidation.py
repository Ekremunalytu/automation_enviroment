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
LOGGING_MODULE_PATH = REPO_ROOT / "appcore" / "logging.py"
HOST_MODULE_PATH = REPO_ROOT / "executor" / "host.py"
RUN_ID_ENV_LITERAL = "EXTRACE_EPOCH_RUN_ID"


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
        f"({APPROVED_PREFIXES}). See ADR 0010. Violations:\n" + "\n".join(violations)
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
    call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call))
    assert _string_literal_first_arg(call) == "extrace.executor.host"


def test_string_literal_first_arg_returns_none_for_name_arg() -> None:
    src = "get_extrace_logger(some_var)\n"
    tree = ast.parse(src)
    call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call))
    assert _string_literal_first_arg(call) is None


# ---------------------------------------------------------------------------
# Invariant 3 (W14-5 sub-commit 2) — LogContextFilter body stamps run_id
# from the canonical env var literal so the structured-field contract
# holds even if the constant import is refactored.
# ---------------------------------------------------------------------------


def _function_body_references_run_id_env_literal(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Constant) and node.value == RUN_ID_ENV_LITERAL:
            return True
        if isinstance(node, ast.Name) and node.id == "RUN_ID_ENV_VAR":
            return True
    return False


def _function_body_sets_record_run_id(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "run_id"
                and isinstance(target.value, ast.Name)
                and target.value.id == "record"
            ):
                return True
    return False


def test_stamp_record_body_stamps_run_id_from_env_literal() -> None:
    """The ``_stamp_record`` helper in ``appcore/logging.py`` is the
    single chokepoint shared by the W14-5 ``LogContextFilter.filter``
    method and the ``_make_extrace_log_record_factory`` LogRecord
    factory wrapper. Both call sites delegate to ``_stamp_record``;
    if a future refactor inlines them or drops the env var reference,
    this gate fires before silent regression lands.
    """
    tree = ast.parse(LOGGING_MODULE_PATH.read_text(encoding="utf-8"))
    stamp_fn: ast.FunctionDef | None = None
    for stmt in tree.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "_stamp_record":
            stamp_fn = stmt
            break
    assert stamp_fn is not None, (
        "_stamp_record() helper must exist in appcore/logging.py — "
        "it is the single chokepoint for the W14-5 structured-field "
        "contract shared by the filter form and the LogRecord factory."
    )

    assert _function_body_references_run_id_env_literal(stamp_fn), (
        "_stamp_record() must reference EXTRACE_EPOCH_RUN_ID "
        "(via RUN_ID_ENV_VAR constant or string literal) so run-ID "
        "stamping cannot silently drop. W14-5 sub-commit 2 invariant."
    )
    assert _function_body_sets_record_run_id(stamp_fn), (
        "_stamp_record() must assign to record.run_id so "
        "the structured-field contract on the LogRecord is satisfied. "
        "W14-5 sub-commit 2 invariant."
    )


def test_log_context_filter_and_factory_both_route_through_stamp_record() -> None:
    """The ``LogContextFilter.filter`` method and the
    ``_make_extrace_log_record_factory`` closure must both delegate
    to ``_stamp_record`` so the structured-field contract has exactly
    one chokepoint. Inlining either path would diverge the W14-5
    contract from the central helper.
    """
    tree = ast.parse(LOGGING_MODULE_PATH.read_text(encoding="utf-8"))

    def _delegates_to_stamp_record(func: ast.FunctionDef) -> bool:
        for node in ast.walk(func):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_stamp_record"
            ):
                return True
        return False

    filter_method: ast.FunctionDef | None = None
    factory_outer: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "filter"
            and any(
                isinstance(parent_class, ast.ClassDef)
                and parent_class.name == "LogContextFilter"
                for parent_class in ast.walk(tree)
                if isinstance(parent_class, ast.ClassDef) and node in parent_class.body
            )
        ):
            filter_method = node
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "_make_extrace_log_record_factory"
        ):
            factory_outer = node

    assert filter_method is not None, (
        "LogContextFilter.filter must exist in appcore/logging.py."
    )
    assert factory_outer is not None, (
        "_make_extrace_log_record_factory must exist in appcore/logging.py."
    )
    assert _delegates_to_stamp_record(filter_method), (
        "LogContextFilter.filter must call _stamp_record(record) so "
        "the structured-field contract stays in a single chokepoint."
    )
    assert _delegates_to_stamp_record(factory_outer), (
        "_make_extrace_log_record_factory must call _stamp_record(record) "
        "inside the wrapper so the factory and the filter form share "
        "the same stamping logic."
    )


# ---------------------------------------------------------------------------
# Invariant 4 (W14-5 sub-commit 2 — M5 byproduct) — _run_docker_exec
# propagates EXTRACE_EPOCH_RUN_ID across the docker exec boundary.
# ---------------------------------------------------------------------------


def test_run_docker_exec_propagates_run_id_env() -> None:
    tree = ast.parse(HOST_MODULE_PATH.read_text(encoding="utf-8"))
    run_docker_exec: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_run_docker_exec":
            run_docker_exec = node
            break
    assert run_docker_exec is not None, (
        "executor.host._run_docker_exec must exist — the docker exec "
        "wrapper is the M5 propagation seam."
    )

    body_text = ast.unparse(run_docker_exec)
    assert "RUN_ID_ENV_VAR" in body_text or RUN_ID_ENV_LITERAL in body_text, (
        "_run_docker_exec must reference EXTRACE_EPOCH_RUN_ID "
        "(via RUN_ID_ENV_VAR constant or literal) so the host-side "
        "run-ID propagates across the docker exec boundary. "
        "W14-5 sub-commit 2 — closes "
        "[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]."
    )
    assert "env_args" in body_text or "-e" in body_text, (
        "_run_docker_exec must inject the run-ID into the docker exec "
        "argv (typically by appending to ``env_args`` so it becomes a "
        "``-e EXTRACE_EPOCH_RUN_ID=...`` arg). W14-5 sub-commit 2."
    )
