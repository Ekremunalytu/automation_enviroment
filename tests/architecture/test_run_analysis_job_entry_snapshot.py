"""W13-13 + W16-2 architecture gate: worker-entry dispatches to the CRUD facade.

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
running`` under the lock before proceeding. **W16-2 (AGENTS.md:57
facade compliance)** moved that primitive out of
``workflows.marketplace.analysis_service`` and into the lifecycle CRUD
facade at
``appcore.storage.crud_ops.analysis_jobs.lifecycle.claim_queued_analysis_job_at_worker_entry``.
This gate now pins two AST invariants on the post-W16-2 facade boundary
so a future refactor cannot silently re-open the cancel race:

1. **INV1 — first DB action is the facade call.** ``run_analysis_job``'s
   first DB-touching statement (anywhere in source order) must be the
   call to ``claim_queued_analysis_job_at_worker_entry``. Re-introducing
   a naive ``job_service.update_job(status="running")`` or any other
   CRUD helper call before the facade call would reopen the W13-13 race
   AND restore the AGENTS.md:57 violation that W16-2 closed; the gate
   fails immediately.

2. **INV2 — facade holds the lock + finalizes directly.** The lifecycle
   helper ``claim_queued_analysis_job_at_worker_entry`` must itself
   contain a ``with_for_update()`` row lock call AND a direct call to
   ``finalize_cancelled_analysis_job`` (the lifecycle CRUD helper, not
   the ``job_service.finalize_cancelled_job`` wrapper). Rationale: the
   wrapper opens its own ``SessionLocal()`` via ``_run_in_session``
   which would deadlock against the row lock held inside the facade.
   The W13-3 exception handler in ``analysis_service.run_analysis_job``
   keeps using the wrapper because by then the entry-block transaction
   has committed and released the lock — but the facade body itself
   MUST stay on the lifecycle helper.

Together they ensure that (a) the unconditional ``update_job`` race
cannot creep back in, (b) the lifecycle-helper deadlock-avoidance
asymmetry survives renames or refactors, and (c) the AGENTS.md:57
facade boundary cannot be re-broken. The behavioral coverage in
``tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py``
pins the observable row state; this gate is the structural enforcer.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SERVICE_PATH = REPO_ROOT / "workflows" / "marketplace" / "analysis_service.py"
LIFECYCLE_PATH = (
    REPO_ROOT / "appcore" / "storage" / "crud_ops" / "analysis_jobs" / "lifecycle.py"
)

# CRUD-helper names whose appearance BEFORE the facade call
# ``claim_queued_analysis_job_at_worker_entry`` would reopen the W13-13
# race. Both bare names (``update_job``) and attribute accesses
# (``job_service.update_job``) are caught — the AST walk in
# ``_call_target_name`` resolves either to the trailing identifier.
#
# ``claim_queued_analysis_job_at_worker_entry`` is INTENTIONALLY omitted:
# it IS the allowed first DB action under W16-2. ``finalize_cancelled_analysis_job``
# is INTENTIONALLY omitted from the caller-side list because, post-W16-2,
# analysis_service no longer calls it directly (the lifecycle facade owns
# that call). INV2 enforces its presence inside the facade.
_DB_TOUCH_NAMES = frozenset(
    {
        "update_job",
        "update_analysis_job",
        "complete_job",
        "complete_analysis_job",
        "fail_job",
        "fail_analysis_job",
        "finalize_cancelled_job",
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
        f"function {name!r} missing — W13-13 / W16-2 entry block removed?"
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


def test_run_analysis_job_dispatches_to_claim_facade_at_worker_entry() -> None:
    """INV1: ``run_analysis_job`` first DB action MUST be the claim facade call.

    Walks the function body in source order. The earliest statement
    containing a call to ``claim_queued_analysis_job_at_worker_entry``
    must appear at or before the earliest statement containing a call
    to any of the legacy CRUD helpers in ``_DB_TOUCH_NAMES``.
    Re-introducing a direct ``select(...).with_for_update()`` /
    ``job_service.update_job(...)`` ahead of the facade would reopen the
    W13-13 race AND restore the AGENTS.md:57 violation that W16-2 closed.

    Architecture-gate scope. We pin source-order on the function-level
    statements (``func.body``) rather than walking every nested call.
    The W13-13 race lives at the entry seam, and source-order on the
    top-level statement list is what the human reader (and PR
    reviewer) actually sees — the gate intentionally matches that
    granularity.
    """
    tree = ast.parse(ANALYSIS_SERVICE_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "run_analysis_job", ANALYSIS_SERVICE_PATH)

    first_claim_idx = _first_index_matching(
        func.body,
        lambda call: (
            _call_target_name(call) == "claim_queued_analysis_job_at_worker_entry"
        ),
    )
    assert first_claim_idx is not None, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "run_analysis_job MUST call "
        "``claim_queued_analysis_job_at_worker_entry`` at worker entry "
        "(W16-2). This is the lifecycle CRUD facade that owns the "
        "W13-13 row lock + cancel-aware branch + ``queued -> running`` "
        "atomic commit. Pre-W16-2 the equivalent logic lived inline; "
        "the W16-2 refactor moved it behind the facade for AGENTS.md:57 "
        "compliance."
    )

    first_other_db_idx = _first_index_matching(
        func.body,
        lambda call: (_call_target_name(call) or "") in _DB_TOUCH_NAMES,
    )
    if first_other_db_idx is not None:
        assert first_claim_idx <= first_other_db_idx, (
            f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
            "run_analysis_job: the claim facade call (body index "
            f"{first_claim_idx}) MUST precede the first secondary CRUD "
            f"helper call (body index {first_other_db_idx}). The facade "
            "owns the row lock + cancel-aware branch; any direct CRUD "
            "before it would reopen the W13-13 race and restore the "
            "AGENTS.md:57 violation closed by W16-2."
        )


def test_claim_facade_holds_lock_and_calls_finalize_directly() -> None:
    """INV2: ``claim_queued_analysis_job_at_worker_entry`` MUST hold the row lock AND call the finalize helper.

    Post-W16-2 the W13-13 cancel-race close-gate lives inside the
    lifecycle facade. The helper body MUST contain:

    1. A call whose target resolves to ``with_for_update`` — the row
       lock that makes the ``queued -> cancelling`` (cancel_analysis_job)
       and ``queued -> running`` (this facade's queued branch) writes
       mutually exclusive.
    2. A call whose target resolves to ``finalize_cancelled_analysis_job``
       — the in-place finalize used on the ``cancelling`` branch under
       the held lock. Swapping in ``job_service.finalize_cancelled_job``
       (the wrapper) would deadlock because the wrapper opens its own
       ``SessionLocal()`` via ``_run_in_session``.

    Dropping either AST call site silently reopens Codex F3.
    """
    tree = ast.parse(LIFECYCLE_PATH.read_text(encoding="utf-8"))
    func = _find_function(
        tree,
        "claim_queued_analysis_job_at_worker_entry",
        LIFECYCLE_PATH,
    )

    has_lock = (
        _first_index_matching(
            func.body,
            lambda call: _call_target_name(call) == "with_for_update",
        )
        is not None
    )
    assert has_lock, (
        f"{LIFECYCLE_PATH.relative_to(REPO_ROOT)}: "
        "claim_queued_analysis_job_at_worker_entry MUST contain a "
        "``with_for_update()`` call. Without the row lock the "
        "``queued -> running`` and ``queued -> cancelling`` writes are "
        "no longer mutually exclusive — re-opening Codex F3."
    )

    has_finalize = (
        _first_index_matching(
            func.body,
            lambda call: _call_target_name(call) == "finalize_cancelled_analysis_job",
        )
        is not None
    )
    assert has_finalize, (
        f"{LIFECYCLE_PATH.relative_to(REPO_ROOT)}: "
        "claim_queued_analysis_job_at_worker_entry MUST contain a "
        "``finalize_cancelled_analysis_job()`` call in its "
        "``cancelling`` branch. Swapping in "
        "``job_service.finalize_cancelled_job`` would deadlock against "
        "the row lock held above; dropping the call would let a cancel "
        "proceed to a real scan — re-opening Codex F3."
    )
