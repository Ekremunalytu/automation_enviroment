"""W13-4 (cancellation lifecycle hardening): concurrent + recovery
behavioral coverage for the W13-3 two-phase cancel.

Three vectors landed under W13-3 architecture-gate AST invariants but
without behavioral runtime evidence:

1. **Cancel ↔ complete DB-level race.** ``cancel_analysis_job`` and
   ``complete_analysis_job`` both acquire row-level locks via
   ``with_for_update()``. The post-W13-3 contract requires: cancel
   wins (row lands in ``cancelling``) and the racing complete raises
   ``JobNotCancellableError``. ``test_complete_analysis_job_rejected_from_cancelling``
   in ``test_analysis_jobs_lifecycle.py:431`` covers the *sequential*
   shape; this file pins the *concurrent* serialization.
2. **Concurrent cancel + finalize idempotency.** UI double-clicks +
   worker exception-handler retry can both call cancel and finalize
   in flight. Contract: every cancel returns the same draining
   snapshot (no ``requested_cancel_at`` regression); exactly one
   finalize wins, the rest raise ``JobNotCancellableError``
   (which the worker exception handler swallows in production —
   ``analysis_service.run_analysis_job`` lines 247-255).
3. **Stuck-`cancelling` boot_id sweep.** If the worker crashes
   between observing the cancel signal and the finalize call, the
   row stays ``cancelling``. ``recover_interrupted_jobs`` (boot_id
   mismatch on next API boot) is the documented design intent —
   ``cancelling`` is non-terminal, so it falls into the
   ``recover_interrupted_analysis_jobs`` predicate and lands as
   ``failed`` (intent-recorded-but-not-delivered). Tracker
   ``W13-test-expansion-observability.md`` Per-Item Detail → W13-3
   row 433 and runbook ``analysis-job-stuck.md`` § Stuck in
   cancelling pin this contract.

W13-4.2 lands these as ``@pytest.mark.skip`` RED precursors. W13-4.4
removes the skip on race + concurrent (both depend on the existing
``with_for_update()`` lock + ``JobNotCancellableError`` guards in
``lifecycle.py:128,181``); W13-4.5 removes the skip on the recovery
test (depends on the existing ``recover_interrupted_analysis_jobs``
sweep wired into ``ACTIVE_ANALYSIS_JOB_STATUSES``, which W13-3
extended to include ``cancelling``).

W14-4 [FOLLOWUP analysis-jobs-race] extends the W13-3 lock discipline
to ``complete_analysis_job`` and ``fail_analysis_job``: both now
acquire ``with_for_update()`` and gate against
``_TERMINAL_JOB_STATUSES`` so the cancel ↔ complete and complete ↔
fail races land an exactly-one-winner contract (no more silently-
overwritten terminal writes). The new ``complete vs fail`` concurrent
case plus the sequential double-complete / double-fail rejections at
the bottom of this file pin the post-fix surface.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from appcore.contracts.schema_defs.analysis_jobs import (
    ANALYSIS_JOB_STEP_NAMES,
    AnalysisJobCreateSnapshot,
    AnalysisJobFailure,
    AnalysisJobStepRecord,
    AnalysisJobUpdate,
)
from appcore.storage.crud_ops.analysis_jobs import lifecycle
from appcore.storage.models import AnalysisJob

pytestmark = pytest.mark.requires_db


# ES-3b: canonical 7-step order from the contract (see lifecycle test note).
_CANONICAL_STEPS = ANALYSIS_JOB_STEP_NAMES


def _empty_steps() -> list[AnalysisJobStepRecord]:
    return [
        AnalysisJobStepRecord(name=name, status="pending", message="Queued.")
        for name in _CANONICAL_STEPS
    ]


def _snapshot(
    *,
    status: str = "running",
    current_step: str | None = "run_monitoring",
    boot_id: str = "boot-test",
    job_id: str | None = None,
) -> AnalysisJobCreateSnapshot:
    now = time.time()
    return AnalysisJobCreateSnapshot(
        job_id=job_id or uuid4().hex,
        owner_boot_id=boot_id,
        owner_pid=1234,
        status=status,  # type: ignore[arg-type]
        publisher="ms-python",
        name="python",
        version="2026.5.0",
        scenario=None,
        analysis_profile=None,
        current_step=current_step,  # type: ignore[arg-type]
        message="Concurrency fixture row.",
        steps=_empty_steps(),
        report_path="activation_report.json",
        install_output=None,
        automation_output=None,
        error_detail=None,
        error_code=None,
        created_at=now,
        started_at=now,
        finished_at=None,
        updated_at=now,
    )


def _force_step_running(db: Session, job: AnalysisJob, step_name: str) -> None:
    """Set a step row to ``running`` (W13-3 cancel keeps step records untouched
    so ``cancelling`` row test fixtures must put the step into ``running``
    explicitly — ``_persist_active`` in ``test_analysis_jobs_lifecycle.py``
    uses the same pattern via ``flag_modified``).
    """
    steps: list[dict[str, Any]] = list(job.steps)
    for index, step in enumerate(steps):
        if step["name"] == step_name:
            step["status"] = "running"
            step["message"] = "concurrency-fixture: forced running"
            steps[index] = step
            break
    job.steps = steps
    flag_modified(job, "steps")
    db.commit()
    db.refresh(job)


@pytest.fixture
def concurrent_session_factory(
    test_engine: Any,
) -> Generator[sessionmaker[Session], None, None]:
    """Yield a per-thread sessionmaker bound to the live test engine.

    Concurrent writes must escape the per-test transaction-rollback
    isolation that ``db_session`` provides — each thread needs its own
    real commit-capable session against the same DB. Cleanup deletes
    every ``analysis_jobs`` row touched during the test so ``test_engine``
    teardown semantics stay intact.
    """
    factory = sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False, future=True
    )
    yield factory
    cleanup = factory()
    try:
        cleanup.execute(delete(AnalysisJob))
        cleanup.commit()
    finally:
        cleanup.close()


def _persist_running_for_concurrency(
    factory: sessionmaker[Session],
) -> str:
    """Create a ``running`` job through its own session/commit and return its id."""
    session = factory()
    try:
        snapshot = _snapshot()
        job = lifecycle.create_analysis_job(session, snapshot)
        _force_step_running(session, job, "run_monitoring")
        return job.job_id
    finally:
        session.close()


def test_cancel_vs_complete_concurrent_write_final_state_is_consistent(
    concurrent_session_factory: sessionmaker[Session],
) -> None:
    """``cancel`` and ``complete`` racing on the same row: final state stays consistent.

    Sequential ordering (sequential cancel → complete) is already pinned
    by ``test_complete_analysis_job_rejected_from_cancelling`` in
    ``test_analysis_jobs_lifecycle.py:431``. This test exercises the
    *concurrent* shape: two ThreadPoolExecutor workers race
    ``cancel_analysis_job`` and ``complete_analysis_job`` on the same
    row.

    **W14-4 post-fix contract.** ``complete_analysis_job`` now acquires
    ``with_for_update()`` (``lifecycle.py:319`` post-W14-4) and gates
    against ``_TERMINAL_JOB_STATUSES`` in addition to the existing
    ``cancelling`` guard, mirroring the cancel lock discipline at
    ``lifecycle.py:128``. Exactly one writer commits a state change;
    the other observes the new status under the lock and raises
    ``JobNotCancellableError``. Pre-W14-4 the loser's write was
    silently overwritten because complete used a plain ``SELECT``.
    """
    job_id = _persist_running_for_concurrency(concurrent_session_factory)

    def _cancel() -> tuple[str, Exception | None]:
        session = concurrent_session_factory()
        try:
            try:
                lifecycle.cancel_analysis_job(session, job_id)
                return ("cancel:ok", None)
            except lifecycle.JobNotCancellableError as exc:
                return ("cancel:rejected", exc)
        finally:
            session.close()

    def _complete() -> tuple[str, Exception | None]:
        session = concurrent_session_factory()
        try:
            try:
                # Mirror the service-layer ``job_service.complete_job``
                # contract (lines 361-381) which always sets
                # ``finished_at=now()`` — lifecycle.complete_analysis_job
                # itself only touches fields the caller passes in.
                lifecycle.complete_analysis_job(
                    session,
                    job_id,
                    AnalysisJobUpdate(
                        message="late completion", finished_at=time.time()
                    ),
                )
                return ("complete:ok", None)
            except lifecycle.JobNotCancellableError as exc:
                return ("complete:rejected", exc)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_cancel), pool.submit(_complete)]
        outcomes = {fut.result()[0] for fut in as_completed(futures)}

    # W14-4: exactly-one-winner contract. ``with_for_update()`` plus the
    # ``_TERMINAL_JOB_STATUSES`` / ``cancelling`` guards on both
    # writers serialize them so one observes the other's commit under
    # the lock and raises. ``{cancel:ok, complete:ok}`` is impossible
    # post-fix (pre-W14-4 it was the silently-overwritten race shape).
    assert outcomes in (
        {"cancel:ok", "complete:rejected"},
        {"cancel:rejected", "complete:ok"},
    ), f"expected exactly one winner, got {outcomes}"

    # Final state invariant: exactly one of the contracted terminal/draining
    # states; ``cancelling`` never has ``finished_at`` (W13-3 invariant);
    # terminal states always do.
    inspect = concurrent_session_factory()
    try:
        final = lifecycle.get_analysis_job(inspect, job_id)
        assert final is not None
        assert final.status in {"cancelling", "completed"}, (
            f"unexpected final status {final.status!r}"
        )
        if final.status == "cancelling":
            assert final.finished_at is None, (
                "cancelling never sets finished_at (W13-3 two-phase contract)"
            )
        else:
            assert final.finished_at is not None, (
                f"{final.status} terminal must populate finished_at"
            )
    finally:
        inspect.close()


def test_concurrent_cancel_finalize_idempotent(
    concurrent_session_factory: sessionmaker[Session],
) -> None:
    """3 cancel + 3 finalize threads on a draining row: 1 finalize wins, rest no-op.

    The W13-3 idempotency contract: ``cancel_analysis_job`` on a row
    already in ``cancelling`` returns the existing snapshot unchanged
    (no ``requested_cancel_at`` regression); ``finalize_cancelled_analysis_job``
    raises ``JobNotCancellableError`` on any non-cancelling source state,
    which means exactly one finalize promotes the row to terminal
    ``cancelled``.
    """
    job_id = _persist_running_for_concurrency(concurrent_session_factory)

    # Drive into cancelling first (single-thread setup).
    setup = concurrent_session_factory()
    try:
        first_drain = lifecycle.cancel_analysis_job(setup, job_id)
        original_requested_at = first_drain.requested_cancel_at  # type: ignore[attr-defined]
        assert first_drain.status == "cancelling"
        assert original_requested_at is not None
    finally:
        setup.close()

    def _cancel() -> str:
        session = concurrent_session_factory()
        try:
            job = lifecycle.cancel_analysis_job(session, job_id)
            return f"cancel:{job.status}"
        except lifecycle.JobNotCancellableError as exc:
            return f"cancel:rejected:{exc.status}"
        finally:
            session.close()

    def _finalize() -> str:
        session = concurrent_session_factory()
        try:
            job = lifecycle.finalize_cancelled_analysis_job(session, job_id)
            return f"finalize:{job.status}"
        except lifecycle.JobNotCancellableError as exc:
            return f"finalize:rejected:{exc.status}"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_cancel) for _ in range(3)] + [
            pool.submit(_finalize) for _ in range(3)
        ]
        outcomes = [fut.result() for fut in as_completed(futures)]

    finalize_wins = [o for o in outcomes if o == "finalize:cancelled"]
    finalize_rejects = [o for o in outcomes if o.startswith("finalize:rejected:")]
    cancel_results = [o for o in outcomes if o.startswith("cancel:")]

    # Exactly one finalize promotes; the other two race-loser finalizes
    # see status != "cancelling" (already cancelled by the winner) and
    # raise JobNotCancellableError.
    assert len(finalize_wins) == 1, f"expected 1 finalize winner, got {outcomes}"
    assert len(finalize_rejects) == 2, f"expected 2 finalize rejects, got {outcomes}"

    # Cancels are race-tolerant: each one either sees `cancelling`
    # (returns no-op snapshot) or sees terminal `cancelled` (raises).
    for outcome in cancel_results:
        assert outcome in {"cancel:cancelling", "cancel:rejected:cancelled"}, outcome

    # Final row is terminal cancelled; requested_cancel_at survived from setup.
    inspect = concurrent_session_factory()
    try:
        final = lifecycle.get_analysis_job(inspect, job_id)
        assert final is not None
        assert final.status == "cancelled"
        assert final.finished_at is not None
        assert final.requested_cancel_at == pytest.approx(  # type: ignore[attr-defined]
            original_requested_at
        )
    finally:
        inspect.close()


def test_recover_interrupted_jobs_finalizes_stuck_cancelling_to_failed(
    db_session: Session,
) -> None:
    """A stuck-``cancelling`` row from a dead boot is swept to ``failed``.

    W13-3 design intent (tracker line 433): ``cancelling`` is
    non-terminal so ``recover_interrupted_analysis_jobs`` predicate
    (``status in ACTIVE_ANALYSIS_JOB_STATUSES AND owner_boot_id !=
    current_boot_id``) catches it on next API boot and ``_interrupt_job``
    transitions it to ``failed`` (not ``cancelled``). Rationale: cancel
    intent was *recorded* but not *delivered* — the worker died
    mid-drain. The runbook
    ``documents/runbooks/analysis-job-stuck.md`` § Stuck in cancelling
    documents this contract for operators; this test pins it.
    """
    snapshot = _snapshot(boot_id="dead-boot-uuid")
    job = lifecycle.create_analysis_job(db_session, snapshot)
    _force_step_running(db_session, job, "run_monitoring")

    # Drive into cancelling (worker would have done this before crashing).
    drained = lifecycle.cancel_analysis_job(db_session, job.job_id)
    assert drained.status == "cancelling"
    assert drained.requested_cancel_at is not None  # type: ignore[attr-defined]

    # Simulate API restart: new boot_id sweeps anything non-terminal
    # owned by the old boot.
    recovered = lifecycle.recover_interrupted_analysis_jobs(
        db_session,
        current_boot_id="fresh-boot-uuid",
        detail="Analysis job was interrupted by an API restart. Start a new run.",
    )
    assert recovered == 1

    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    # Documented design intent: stuck cancelling is recovered to
    # `failed`, not `cancelled`. If this assertion ever flips to
    # `cancelled` (e.g. a status-sweep helper is added that finalizes
    # cancelling rows distinctly from boot_id sweep), update the runbook
    # § Stuck in cancelling Step 2 SQL example to match.
    assert refetched.status == "failed"
    assert refetched.error_detail == (
        "Analysis job was interrupted by an API restart. Start a new run."
    )
    # `_interrupt_job` finalizes step records on recovery (running → failed,
    # trailing pending → skipped) regardless of source state. ES-3b:
    # run_monitoring is index 5 in the canonical 7-step order.
    assert refetched.steps[5]["status"] == "failed"
    assert refetched.finished_at is not None


# ---------------------------------------------------------------------------
# W14-4 [FOLLOWUP analysis-jobs-race]
# ---------------------------------------------------------------------------


def test_concurrent_complete_vs_fail_exactly_one_winner(
    concurrent_session_factory: sessionmaker[Session],
) -> None:
    """W14-4: ``complete`` and ``fail`` racing on the same ``running`` row
    serialize through ``with_for_update()``; exactly one commits the
    terminal transition, the other observes the new terminal status
    under the lock and raises ``JobNotCancellableError``.

    Pre-W14-4 both functions used a plain ``SELECT`` and the loser's
    write was silently overwritten. The post-fix lock + terminal guard
    at ``lifecycle.py:260`` (fail) and ``lifecycle.py:319`` (complete)
    closes this race window. Mirrors ``test_cancel_vs_complete_…``
    above for the symmetric writer pair.
    """
    job_id = _persist_running_for_concurrency(concurrent_session_factory)

    def _complete() -> str:
        session = concurrent_session_factory()
        try:
            lifecycle.complete_analysis_job(
                session,
                job_id,
                AnalysisJobUpdate(message="happy completion", finished_at=time.time()),
            )
            return "complete:ok"
        except lifecycle.JobNotCancellableError:
            return "complete:rejected"
        finally:
            session.close()

    def _fail() -> str:
        session = concurrent_session_factory()
        try:
            lifecycle.fail_analysis_job(
                session,
                job_id,
                AnalysisJobFailure(
                    detail="installer crashed", error_code="install_failed"
                ),
            )
            return "fail:ok"
        except lifecycle.JobNotCancellableError:
            return "fail:rejected"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_complete), pool.submit(_fail)]
        outcomes = {fut.result() for fut in as_completed(futures)}

    assert outcomes in (
        {"complete:ok", "fail:rejected"},
        {"complete:rejected", "fail:ok"},
    ), f"expected exactly one winner, got {outcomes}"

    inspect = concurrent_session_factory()
    try:
        final = lifecycle.get_analysis_job(inspect, job_id)
        assert final is not None
        assert final.status in {"completed", "failed"}, (
            f"unexpected final status {final.status!r}"
        )
        assert final.finished_at is not None
    finally:
        inspect.close()


def test_double_complete_rejected_after_completed(
    concurrent_session_factory: sessionmaker[Session],
) -> None:
    """W14-4 sequential: completing a row twice raises on the second call.

    Pre-W14-4 the second complete silently overwrote the first's
    ``finished_at`` and ``message``. The post-fix terminal-state guard
    at ``lifecycle.py:319`` raises ``JobNotCancellableError`` instead.
    """
    job_id = _persist_running_for_concurrency(concurrent_session_factory)

    first = concurrent_session_factory()
    try:
        finalized = lifecycle.complete_analysis_job(
            first,
            job_id,
            AnalysisJobUpdate(message="first", finished_at=time.time()),
        )
        assert finalized.status == "completed"
        original_finished_at = finalized.finished_at
        original_message = finalized.message
    finally:
        first.close()

    second = concurrent_session_factory()
    try:
        with pytest.raises(lifecycle.JobNotCancellableError) as exc_info:
            lifecycle.complete_analysis_job(
                second,
                job_id,
                AnalysisJobUpdate(message="second", finished_at=time.time()),
            )
        assert exc_info.value.status == "completed"
    finally:
        second.close()

    inspect = concurrent_session_factory()
    try:
        refetched = lifecycle.get_analysis_job(inspect, job_id)
        assert refetched is not None
        assert refetched.status == "completed"
        assert refetched.finished_at == original_finished_at
        assert refetched.message == original_message
    finally:
        inspect.close()


def test_double_fail_rejected_after_failed(
    concurrent_session_factory: sessionmaker[Session],
) -> None:
    """W14-4 sequential: failing a row twice raises on the second call.

    Symmetric to ``test_double_complete_rejected_after_completed`` —
    the post-fix terminal-state guard at ``lifecycle.py:260`` rejects
    the second fail; the row keeps the original ``error_detail`` /
    ``error_code`` from the first writer.
    """
    job_id = _persist_running_for_concurrency(concurrent_session_factory)

    first = concurrent_session_factory()
    try:
        finalized = lifecycle.fail_analysis_job(
            first,
            job_id,
            AnalysisJobFailure(detail="first failure", error_code="install_failed"),
        )
        assert finalized.status == "failed"
        original_detail = finalized.error_detail
        original_code = finalized.error_code
    finally:
        first.close()

    second = concurrent_session_factory()
    try:
        with pytest.raises(lifecycle.JobNotCancellableError) as exc_info:
            lifecycle.fail_analysis_job(
                second,
                job_id,
                AnalysisJobFailure(detail="second failure", error_code="other_error"),
            )
        assert exc_info.value.status == "failed"
    finally:
        second.close()

    inspect = concurrent_session_factory()
    try:
        refetched = lifecycle.get_analysis_job(inspect, job_id)
        assert refetched is not None
        assert refetched.status == "failed"
        assert refetched.error_detail == original_detail
        assert refetched.error_code == original_code
    finally:
        inspect.close()
