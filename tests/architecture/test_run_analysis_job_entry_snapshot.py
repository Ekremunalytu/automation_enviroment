"""W13-13 architecture gate: production ``run_analysis_job`` must open with a row-lock snapshot.

W13-13 closes the worker-entry seam in W13-3's two-phase cancel
contract. Pre-W13-13 the worker thread spawned by
``router.start_analysis_job`` began with an unconditional
``job_service.update_job(job_id, status="running", ...)`` as its first
DB action. A cancel that landed between the ``reserve_job`` commit
(``router.py:243``) and the worker thread reaching ``run_analysis_job``
flipped the row to ``cancelling`` under ``with_for_update()`` — and the
unguarded ``update_job`` write then silently overwrote that drain
state back to ``running``. The cancel intent was lost; ``cancel_check``
returned False for the rest of the scan; the analysis ran to
completion against the user's explicit cancel.

Path B (locked-in by the W13-13 tracker) takes a
``select(AnalysisJob).where(...).with_for_update()`` row-level lock at
worker entry, branches on observed status, and either finalizes the
``cancelling`` row directly or atomically transitions ``queued ->
running`` under the lock before proceeding. This gate pins two AST
invariants so a future refactor cannot silently re-open the cancel
race:

1. **INV1 — first-DB-action is the lock.** ``run_analysis_job``'s first
   DB-touching statement (anywhere in source order) must be the one
   that bears a ``with_for_update()`` call. Re-introducing a naive
   ``job_service.update_job(status="running")`` or any other CRUD
   helper call before the lock acquire would reopen the W13-13 race;
   the gate fails immediately.

2. **INV2 — direct lifecycle helper, NOT the wrapper.** The ``cancelling``
   branch of the entry block must call ``finalize_cancelled_analysis_job``
   (the lifecycle CRUD helper, imported by name from
   ``appcore.storage.crud_ops.analysis_jobs.lifecycle``) and not the
   ``job_service.finalize_cancelled_job`` wrapper. Rationale: the
   wrapper opens its own ``SessionLocal()`` via ``_run_in_session``
   which would deadlock against the row lock held by the entry-block
   ``db``. The W13-3 exception handler downstream keeps using the
   wrapper because by then the entry-block transaction has committed.
   The call MUST appear before any ``execute_analysis_request`` call
   in source order so the cancel-finalize is reachable from the
   entry-block branch.

Together they ensure that (a) the unconditional ``update_job`` race
cannot creep back in and (b) the lifecycle-helper deadlock-avoidance
asymmetry survives renames or refactors. The behavioral coverage in
``tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py``
pins the observable row state; this gate is the structural enforcer.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SERVICE_PATH = (
    REPO_ROOT / "workflows" / "marketplace" / "analysis_service.py"
)

# CRUD-helper names whose appearance BEFORE the ``with_for_update()`` lock
# would reopen the W13-13 race. Both bare names (``update_job``) and
# attribute accesses (``job_service.update_job``) are caught — the AST
# walk in ``_call_target_name`` resolves either to the trailing identifier.
_DB_TOUCH_NAMES = frozenset(
    {
        "update_job",
        "update_analysis_job",
        "complete_job",
        "complete_analysis_job",
        "fail_job",
        "fail_analysis_job",
        "finalize_cancelled_job",
        # NOTE: finalize_cancelled_analysis_job is INTENTIONALLY omitted —
        # it IS allowed in the entry block (it's the W13-13 cancel-finalize
        # path under the row lock). INV2 pins its required position.
        "cancel_job",
        "cancel_analysis_job",
        "get_job_snapshot",
        "get_persisted_job_snapshot",
        "store_job",
        "reserve_job",
    }
)


def _find_function(tree: ast.AST, name: str, source_path: Path) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(
        f"{source_path.relative_to(REPO_ROOT)}: "
        f"function {name!r} missing — W13-13 entry block removed?"
    )


def _call_target_name(call: ast.Call) -> str | None:
    """Resolve the trailing identifier of a ``Call``'s callable.

    For ``foo()`` returns ``"foo"``; for ``ns.foo()`` returns ``"foo"``;
    for ``stmt.filter(...).with_for_update()`` returns ``"with_for_update"``.
    Returns ``None`` for callables that don't end in a plain attribute or
    name (e.g. ``func()()``).
    """
    target = call.func
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def _first_index_matching(
    statements: list[ast.stmt],
    predicate,
) -> int | None:
    for index, stmt in enumerate(statements):
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and predicate(node):
                return index
    return None


def test_run_analysis_job_takes_with_for_update_before_any_other_db_call() -> None:
    """INV1: the first DB-touching statement in ``run_analysis_job`` must bear ``with_for_update()``.

    Walks the function body in source order. The earliest statement
    that contains a ``Call`` to ``with_for_update`` must appear at or
    before the earliest statement that contains a ``Call`` to any of
    the legacy CRUD helpers listed in ``_DB_TOUCH_NAMES``. Reopening
    the W13-13 race would require re-introducing one of those calls
    ahead of the lock, which this assertion blocks.

    Architecture-gate scope. We pin source-order on the function-level
    statements (``func.body``) rather than walking every nested call.
    The W13-13 race lives at the entry seam, and source-order on the
    top-level statement list is what the human reader (and PR
    reviewer) actually sees — the gate intentionally matches that
    granularity.
    """
    tree = ast.parse(ANALYSIS_SERVICE_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "run_analysis_job", ANALYSIS_SERVICE_PATH)

    first_lock_idx = _first_index_matching(
        func.body,
        lambda call: _call_target_name(call) == "with_for_update",
    )
    first_other_db_idx = _first_index_matching(
        func.body,
        lambda call: (_call_target_name(call) or "") in _DB_TOUCH_NAMES,
    )

    assert first_lock_idx is not None, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "run_analysis_job must call ``select(...).with_for_update()`` at "
        "worker entry to close the cancel-race seam (W13-13). The lock "
        "is what makes the queued -> running transition atomic with "
        "respect to cancel_analysis_job's queued -> cancelling write."
    )

    if first_other_db_idx is not None:
        assert first_lock_idx <= first_other_db_idx, (
            f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
            "run_analysis_job: the ``with_for_update()`` snapshot lock "
            f"(body index {first_lock_idx}) must precede the first CRUD "
            f"helper call (body index {first_other_db_idx}). Without "
            "this ordering a cancel that lands in the reserve_job -> "
            "worker-entry window would be overwritten by the wrapper's "
            "naive UPDATE — re-opening Codex F3."
        )


def test_run_analysis_job_calls_lifecycle_finalize_helper_before_execute() -> None:
    """INV2: the entry block must call ``finalize_cancelled_analysis_job`` directly, BEFORE execute.

    The ``cancelling`` branch under the row lock calls the lifecycle
    helper imported by name from
    ``appcore.storage.crud_ops.analysis_jobs.lifecycle``. The W13-13
    asymmetry is deliberate: using the ``job_service.finalize_cancelled_job``
    wrapper here would deadlock because the wrapper opens its own
    ``SessionLocal()`` via ``_run_in_session`` which collides with the
    row lock held by the entry-block ``db``.

    The architecture invariant is structural: somewhere BEFORE the
    first call to ``execute_analysis_request`` in source order, the
    function body must contain a call whose target name resolves to
    ``finalize_cancelled_analysis_job`` (the bare lifecycle helper
    name). If a future refactor swaps it for the wrapper or drops it
    entirely, the W13-13 cancel-at-worker-entry path silently regresses
    (a cancel that arrives in the reserve_job -> worker-entry window
    would proceed to ``execute_analysis_request`` instead of finalizing).
    """
    tree = ast.parse(ANALYSIS_SERVICE_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "run_analysis_job", ANALYSIS_SERVICE_PATH)

    execute_idx = _first_index_matching(
        func.body,
        lambda call: _call_target_name(call) == "execute_analysis_request",
    )
    assert execute_idx is not None, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "run_analysis_job: ``execute_analysis_request`` callsite missing — "
        "downstream W13-13 invariant cannot be evaluated."
    )

    finalize_idx = _first_index_matching(
        func.body[:execute_idx + 1],
        lambda call: _call_target_name(call) == "finalize_cancelled_analysis_job",
    )

    assert finalize_idx is not None and finalize_idx <= execute_idx, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "run_analysis_job must call ``finalize_cancelled_analysis_job`` "
        "(the lifecycle CRUD helper imported by name, NOT the "
        "``job_service.finalize_cancelled_job`` wrapper) in the entry "
        f"block at or before the ``execute_analysis_request`` callsite "
        f"(body index {execute_idx}). Swapping in the wrapper would "
        "deadlock against the entry-block row lock; dropping the call "
        "would let a cancel that arrives in the reserve_job -> worker-"
        "entry window proceed to a real scan instead of finalizing the "
        "drain — re-opening Codex F3."
    )
