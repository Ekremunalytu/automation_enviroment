"""W15-1 architecture gate: pin the sync ``POST /api/marketplace/analyze``
endpoint and the async ``run_analysis_job`` worker to the same closed
error taxonomy.

Background. Codex 2026-05-10 audit M10 flagged that the two analyze
surfaces handled different exception classes: the sync entry caught only
``FileNotFoundError`` / ``ActivationReportLoadError`` / ``TriggerPlanError``
/ ``ExecutorError``, while the async path additionally caught
``OSError`` / ``SQLAlchemyError`` / ``ValueError`` / ``TypeError`` /
``AttributeError``. The same request shape could therefore receive two
different status codes depending on whether it went through the sync
endpoint or the async job worker (sync bubbled the extra classes to a
FastAPI default 500; async funnelled them through ``fail_job``).

W15-1 introduces three module-level tuples in
``workflows/marketplace/analysis_service.py``:

- ``ANALYZE_RECOVERABLE_ERROR_TYPES`` — exceptions the async path treats
  as recoverable failures (``fail_job`` then ``return``).
- ``ANALYZE_PROGRAMMING_ERROR_TYPES`` — exceptions the async path treats
  as programming-class failures (``fail_job`` then ``raise`` so the
  worker thread surfaces the bug).
- ``ANALYZE_ERROR_TYPES`` — the union; what the sync entry catches as
  one except clause via the
  :func:`analyze_error_to_http_response` helper.

This gate parses ``analysis_service.py`` and ``router.py`` and asserts:

1. The three tuples exist and ``ANALYZE_ERROR_TYPES`` is the
   concatenation of the other two (no drift between the source-of-truth
   and the union).
2. ``analyze_extension`` (sync) has exactly one ``except`` clause whose
   exception expression is the name ``ANALYZE_ERROR_TYPES`` — no
   open-coded class list, no ``except Exception``.
3. ``run_analysis_job`` (async) references both
   ``ANALYZE_RECOVERABLE_ERROR_TYPES`` and
   ``ANALYZE_PROGRAMMING_ERROR_TYPES`` in its except clauses — pinning
   the worker to the same source-of-truth tuples.
4. The helper :func:`analyze_error_to_http_response` is defined and has
   a status branch for every class in ``ANALYZE_ERROR_TYPES`` (no class
   silently maps to the unmapped-class ``AssertionError`` fallback).

Modeled on the W14-5 ``test_logger_consolidation.py`` AST gate pattern.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SERVICE_PATH = (
    REPO_ROOT / "workflows" / "marketplace" / "analysis_service.py"
)
ROUTER_PATH = REPO_ROOT / "workflows" / "marketplace" / "router.py"

ANALYZE_ERROR_TYPES_NAME = "ANALYZE_ERROR_TYPES"
RECOVERABLE_TYPES_NAME = "ANALYZE_RECOVERABLE_ERROR_TYPES"
PROGRAMMING_TYPES_NAME = "ANALYZE_PROGRAMMING_ERROR_TYPES"
HELPER_NAME = "analyze_error_to_http_response"
SYNC_ENDPOINT_NAME = "analyze_extension"
ASYNC_WORKER_NAME = "run_analysis_job"

# The exception classes that must each have an explicit status branch in
# the helper. Subset of ``ANALYZE_ERROR_TYPES`` plus ``ActivationReportLoadError``
# (a ``ValueError`` subclass that must be matched before the generic
# ``ValueError`` branch). Names checked as ``ast.Name.id`` against
# isinstance calls.
EXPECTED_HELPER_BRANCH_NAMES: frozenset[str] = frozenset(
    {
        "ExecutorError",
        "FileNotFoundError",
        "ActivationReportLoadError",
        "TriggerPlanError",
        "OSError",
        "SQLAlchemyError",
        "ValueError",
        "TypeError",
        "AttributeError",
    }
)


# ---------------------------------------------------------------------------
# Shared AST helpers
# ---------------------------------------------------------------------------


def _module_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _find_assign_value(tree: ast.Module, target_name: str) -> ast.expr | None:
    """Return the RHS expression of ``target_name = ...`` at module level."""
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Name)
                and target.id == target_name
                and node.value is not None
            ):
                return node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    return node.value
    return None


def _tuple_member_names(node: ast.expr) -> tuple[str, ...]:
    """Return the names of a tuple literal's members; empty if not a literal."""
    if isinstance(node, ast.Tuple):
        names: list[str] = []
        for elt in node.elts:
            if isinstance(elt, ast.Name):
                names.append(elt.id)
        return tuple(names)
    return ()


def _find_function(
    tree: ast.Module, name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        ):
            return node
    return None


def _except_handler_type_names(handler: ast.ExceptHandler) -> tuple[str, ...]:
    """Return the names referenced in an ``except (...)`` clause type expr."""
    expr = handler.type
    if expr is None:
        return ()
    if isinstance(expr, ast.Name):
        return (expr.id,)
    if isinstance(expr, ast.Tuple):
        return tuple(elt.id for elt in expr.elts if isinstance(elt, ast.Name))
    return ()


# ---------------------------------------------------------------------------
# Invariant 1 — the three tuples exist and the union decomposition holds
# ---------------------------------------------------------------------------


def test_analyze_error_types_decomposition_invariant() -> None:
    """``ANALYZE_ERROR_TYPES == ANALYZE_RECOVERABLE_ERROR_TYPES +
    ANALYZE_PROGRAMMING_ERROR_TYPES`` — the source-of-truth union must
    track the two subset tuples so the sync and async paths cannot
    silently diverge.
    """
    tree = _module_tree(ANALYSIS_SERVICE_PATH)
    recoverable_expr = _find_assign_value(tree, RECOVERABLE_TYPES_NAME)
    programming_expr = _find_assign_value(tree, PROGRAMMING_TYPES_NAME)
    union_expr = _find_assign_value(tree, ANALYZE_ERROR_TYPES_NAME)

    assert recoverable_expr is not None, (
        f"{RECOVERABLE_TYPES_NAME} module-level assignment missing in "
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}; W15-1 invariant."
    )
    assert programming_expr is not None, (
        f"{PROGRAMMING_TYPES_NAME} module-level assignment missing in "
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}; W15-1 invariant."
    )
    assert union_expr is not None, (
        f"{ANALYZE_ERROR_TYPES_NAME} module-level assignment missing in "
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}; W15-1 invariant."
    )

    recoverable_names = _tuple_member_names(recoverable_expr)
    programming_names = _tuple_member_names(programming_expr)
    assert recoverable_names, (
        f"{RECOVERABLE_TYPES_NAME} must be a tuple literal of exception class "
        f"names so the AST gate can statically reason about taxonomy drift."
    )
    assert programming_names, (
        f"{PROGRAMMING_TYPES_NAME} must be a tuple literal of exception class "
        f"names so the AST gate can statically reason about taxonomy drift."
    )

    # The union must be expressed as ``RECOVERABLE + PROGRAMMING`` (BinOp
    # over the two tuple names) so the decomposition is mechanically
    # verifiable. Tolerate either operand order.
    assert isinstance(union_expr, ast.BinOp) and isinstance(union_expr.op, ast.Add), (
        f"{ANALYZE_ERROR_TYPES_NAME} must be a BinOp Add over "
        f"{RECOVERABLE_TYPES_NAME} and {PROGRAMMING_TYPES_NAME} so the "
        "decomposition cannot drift."
    )
    left = union_expr.left
    right = union_expr.right
    left_id = left.id if isinstance(left, ast.Name) else None
    right_id = right.id if isinstance(right, ast.Name) else None
    operands = {left_id, right_id}
    assert operands == {RECOVERABLE_TYPES_NAME, PROGRAMMING_TYPES_NAME}, (
        f"{ANALYZE_ERROR_TYPES_NAME} must reference exactly "
        f"{RECOVERABLE_TYPES_NAME} and {PROGRAMMING_TYPES_NAME}; got "
        f"operands {operands!r}."
    )

    overlap = set(recoverable_names) & set(programming_names)
    assert not overlap, (
        f"Exception classes appear in both {RECOVERABLE_TYPES_NAME} and "
        f"{PROGRAMMING_TYPES_NAME}: {sorted(overlap)}. Each class must "
        "belong to exactly one async-side semantics bucket."
    )


# ---------------------------------------------------------------------------
# Invariant 2 — sync ``analyze_extension`` uses the union tuple as its
# single except clause
# ---------------------------------------------------------------------------


def test_sync_analyze_endpoint_uses_canonical_error_tuple() -> None:
    """The sync endpoint must catch ``ANALYZE_ERROR_TYPES`` in a single
    except clause — no open-coded class list, no ``except Exception``,
    no multi-handler taxonomy that could drift from the async worker.
    """
    tree = _module_tree(ROUTER_PATH)
    fn = _find_function(tree, SYNC_ENDPOINT_NAME)
    assert fn is not None, (
        f"{SYNC_ENDPOINT_NAME} must exist in "
        f"{ROUTER_PATH.relative_to(REPO_ROOT)} — it is the sync entry "
        "for POST /api/marketplace/analyze."
    )

    try_nodes = [n for n in ast.walk(fn) if isinstance(n, ast.Try)]
    assert len(try_nodes) == 1, (
        f"{SYNC_ENDPOINT_NAME} must have exactly one ``try`` block over "
        f"``execute_analysis_request`` (W15-1 invariant); found {len(try_nodes)}."
    )
    try_node = try_nodes[0]
    assert len(try_node.handlers) == 1, (
        f"{SYNC_ENDPOINT_NAME} must have exactly one except clause over "
        f"``{ANALYZE_ERROR_TYPES_NAME}`` (W15-1 invariant); found "
        f"{len(try_node.handlers)} handlers — open-coded class lists are "
        "forbidden because they drift from the async worker taxonomy."
    )
    handler = try_node.handlers[0]
    type_names = _except_handler_type_names(handler)
    assert type_names == (ANALYZE_ERROR_TYPES_NAME,), (
        f"{SYNC_ENDPOINT_NAME}'s single except clause must reference the "
        f"name ``{ANALYZE_ERROR_TYPES_NAME}`` (not an open-coded tuple). "
        f"Got {type_names!r}."
    )


# ---------------------------------------------------------------------------
# Invariant 3 — async ``run_analysis_job`` references both subset tuples
# ---------------------------------------------------------------------------


def test_async_worker_references_both_subset_tuples() -> None:
    """The async worker must catch ``ANALYZE_RECOVERABLE_ERROR_TYPES`` and
    ``ANALYZE_PROGRAMMING_ERROR_TYPES`` in two of its except clauses so
    the sync entry's union tuple cannot diverge from the worker's
    semantics.
    """
    tree = _module_tree(ANALYSIS_SERVICE_PATH)
    fn = _find_function(tree, ASYNC_WORKER_NAME)
    assert fn is not None, (
        f"{ASYNC_WORKER_NAME} must exist in "
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}."
    )

    referenced: set[str] = set()
    for handler in ast.walk(fn):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        for name in _except_handler_type_names(handler):
            if name in {RECOVERABLE_TYPES_NAME, PROGRAMMING_TYPES_NAME}:
                referenced.add(name)

    missing = {RECOVERABLE_TYPES_NAME, PROGRAMMING_TYPES_NAME} - referenced
    assert not missing, (
        f"{ASYNC_WORKER_NAME} must reference {sorted(missing)} in its "
        "except clauses so the worker stays pinned to the same source-"
        "of-truth tuples as the sync entry. W15-1 invariant."
    )


# ---------------------------------------------------------------------------
# Invariant 4 — helper has a status branch for every taxonomy class
# ---------------------------------------------------------------------------


def _collect_isinstance_class_names(fn: ast.FunctionDef) -> set[str]:
    """Return the set of class names referenced in ``isinstance(exc, ...)``
    calls inside the helper body. Both ``isinstance(exc, Cls)`` and
    ``isinstance(exc, (Cls1, Cls2))`` forms are walked.
    """
    names: set[str] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "isinstance"):
            continue
        if len(node.args) < 2:
            continue
        second = node.args[1]
        if isinstance(second, ast.Name):
            names.add(second.id)
        elif isinstance(second, ast.Tuple):
            for elt in second.elts:
                if isinstance(elt, ast.Name):
                    names.add(elt.id)
    return names


def test_helper_has_branch_for_every_taxonomy_class() -> None:
    """:func:`analyze_error_to_http_response` must have an isinstance
    branch for every class in ``ANALYZE_ERROR_TYPES`` plus
    ``ActivationReportLoadError`` (which must be matched before the
    generic ``ValueError`` branch). Drift between the helper and the
    tuple is the bug class W15-1 closes — the gate keeps them coupled.
    """
    tree = _module_tree(ANALYSIS_SERVICE_PATH)
    fn = _find_function(tree, HELPER_NAME)
    assert fn is not None and isinstance(fn, ast.FunctionDef), (
        f"{HELPER_NAME} must exist as a top-level function in "
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}."
    )

    branch_classes = _collect_isinstance_class_names(fn)
    missing = EXPECTED_HELPER_BRANCH_NAMES - branch_classes
    assert not missing, (
        f"{HELPER_NAME} is missing isinstance branches for: "
        f"{sorted(missing)}. Every class in ANALYZE_ERROR_TYPES (plus "
        "ActivationReportLoadError) must be explicitly mapped to a "
        "status code or the helper raises the unmapped-class "
        "AssertionError at runtime. W15-1 invariant."
    )


# ---------------------------------------------------------------------------
# Invariant 5 — vacuous-truth guard: the sync endpoint's single except
# handler body must dispatch through the helper, not an open-coded
# HTTPException. Without this, a refactor could keep the tuple-based
# except clause (passing invariant 2) while routing the exception to a
# hand-rolled status map that drifts from the helper.
# ---------------------------------------------------------------------------


def _walk_calls_in_handler_body(handler: ast.ExceptHandler) -> list[ast.Call]:
    """Walk only the handler body (not other handlers / try-else)."""
    calls: list[ast.Call] = []
    for stmt in handler.body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                calls.append(node)
    return calls


def test_sync_endpoint_handler_body_dispatches_through_helper() -> None:
    """``analyze_extension``'s except clause body must raise via
    :func:`analyze_error_to_http_response` (not an open-coded
    ``HTTPException(...)``). Invariant 2 only pins the *type expression*
    of the except clause; this invariant pins the *dispatch* — without
    it a refactor could keep the canonical tuple while routing the
    caught exception through a hand-rolled status map.
    """
    tree = _module_tree(ROUTER_PATH)
    fn = _find_function(tree, SYNC_ENDPOINT_NAME)
    assert fn is not None, f"{SYNC_ENDPOINT_NAME} must exist."

    try_nodes = [n for n in ast.walk(fn) if isinstance(n, ast.Try)]
    assert try_nodes, "Invariant 2 ensures this; defensive only."
    handler = try_nodes[0].handlers[0]

    helper_called = False
    open_coded_http_exceptions: list[int] = []
    for call in _walk_calls_in_handler_body(handler):
        func = call.func
        if isinstance(func, ast.Name) and func.id == HELPER_NAME:
            helper_called = True
        # Detect open-coded HTTPException(...) constructors. Direct call
        # of the ``HTTPException`` name only — ``raise X from exc``
        # appears as an outer Raise statement, not as a Call node here.
        if isinstance(func, ast.Name) and func.id == "HTTPException":
            open_coded_http_exceptions.append(call.lineno)

    assert helper_called, (
        f"{SYNC_ENDPOINT_NAME}'s except clause body must call "
        f"``{HELPER_NAME}(exc)`` so the sync surface dispatch stays "
        "pinned to the same status-map source-of-truth as the helper. "
        "W15-1 invariant 5 (vacuous-truth guard for invariant 2)."
    )
    assert not open_coded_http_exceptions, (
        f"{SYNC_ENDPOINT_NAME}'s except clause body raises HTTPException "
        f"directly at lines {open_coded_http_exceptions}; all status "
        f"mapping must flow through ``{HELPER_NAME}`` so the sync "
        "surface cannot drift from the helper's documented contract. "
        "W15-1 invariant 5."
    )


# ---------------------------------------------------------------------------
# Invariant 6 — the helper's ExecutorError branch must delegate to
# ``map_executor_error`` so the structured ``error_id`` + secret-
# redaction contract from W10-7 / W12-* is preserved. Without this
# invariant, a refactor could replace the delegation with a plain
# ``HTTPException(status_code=502, detail=str(exc))`` — same status,
# but the redaction guarantee is silently lost.
# ---------------------------------------------------------------------------


def test_helper_executor_branch_delegates_to_map_executor_error() -> None:
    """The ``ExecutorError`` branch of :func:`analyze_error_to_http_response`
    must call ``map_executor_error(exc)`` (not construct an HTTPException
    inline). ``map_executor_error`` enforces the
    [W10-7] secret-redacted detail + structured ``error_id`` contract;
    inlining the 502 mapping would silently regress it.
    """
    tree = _module_tree(ANALYSIS_SERVICE_PATH)
    fn = _find_function(tree, HELPER_NAME)
    assert fn is not None and isinstance(fn, ast.FunctionDef)

    # Locate the ``if isinstance(exc, ExecutorError):`` branch and walk
    # only its body. We do NOT scan the whole helper body because the
    # other branches MUST construct HTTPExceptions inline — that is the
    # documented status map. Only the ExecutorError branch is special.
    executor_branch_body: list[ast.stmt] | None = None
    for stmt in fn.body:
        if not isinstance(stmt, ast.If):
            continue
        test = stmt.test
        if not (isinstance(test, ast.Call) and isinstance(test.func, ast.Name)
                and test.func.id == "isinstance"):
            continue
        if len(test.args) < 2:
            continue
        second = test.args[1]
        if isinstance(second, ast.Name) and second.id == "ExecutorError":
            executor_branch_body = stmt.body
            break

    assert executor_branch_body is not None, (
        f"{HELPER_NAME} must have an ``if isinstance(exc, ExecutorError):`` "
        "branch as its first dispatch (so the W10-7 redaction contract "
        "is preserved before the generic 502 branches). Invariant 6."
    )

    delegates_to_map_executor_error = False
    open_coded_http_exception_lines: list[int] = []
    for stmt in executor_branch_body:
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                if func.id == "map_executor_error":
                    delegates_to_map_executor_error = True
                elif func.id == "HTTPException":
                    open_coded_http_exception_lines.append(node.lineno)

    assert delegates_to_map_executor_error, (
        f"{HELPER_NAME}'s ExecutorError branch must call "
        "``map_executor_error(exc)`` so the W10-7 secret-redacted "
        "detail + structured error_id contract is preserved. Inlining a "
        "plain HTTPException(502, str(exc)) would leak raw executor "
        "output through the response detail. W15-1 invariant 6."
    )
    assert not open_coded_http_exception_lines, (
        f"{HELPER_NAME}'s ExecutorError branch contains a direct "
        f"HTTPException(...) call at lines {open_coded_http_exception_lines}. "
        "The branch must delegate to ``map_executor_error`` rather than "
        "construct the response inline — bypassing the delegation drops "
        "the W10-7 redaction contract. W15-1 invariant 6."
    )
