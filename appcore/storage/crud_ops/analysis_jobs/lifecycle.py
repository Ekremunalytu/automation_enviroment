"""Lifecycle helpers for persisted marketplace analysis jobs.

Owns create/cancel/complete/fail + recovery + read paths plus the shared
`JobNotCancellableError` and the terminal-status set. Imports the JSON
serialization pair (`_job_steps` / `_write_steps`) from
`appcore.storage.crud_ops.analysis_jobs.steps` — the dependency direction is
strictly `lifecycle -> steps` to keep the subpackage acyclic (W11-8).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    ACTIVE_ANALYSIS_JOB_STATUSES,
    AnalysisJobCreateSnapshot,
    AnalysisJobFailure,
    AnalysisJobUpdate,
)
from appcore.storage.crud_ops.analysis_jobs.steps import _job_steps, _write_steps
from appcore.storage.models import AnalysisJob


class JobNotCancellableError(RuntimeError):
    """Raised when a cancel request targets a job already in a terminal state."""

    def __init__(self, job_id: str, status: str) -> None:
        super().__init__(
            f"Analysis job {job_id} is in terminal status "
            f"{status!r} and cannot be cancelled."
        )
        self.job_id = job_id
        self.status = status


# ES-3b (ADR 0016 §Decision 1): `rejected_static` is the terminal state a job
# enters when the static pre-check gate BLOCKs an extension. It joins the
# terminal set here (deferred from ES-1b) so the cancel/complete/fail guards
# treat a rejected job as immutable and `reserve_job` admits the next job once
# the gate releases the single-active slot. It is NOT in
# `ACTIVE_ANALYSIS_JOB_STATUSES`, so the partial unique index is unchanged.
_TERMINAL_JOB_STATUSES: frozenset[str] = frozenset(
    {"completed", "failed", "cancelled", "rejected_static"}
)


def _get_analysis_job_or_raise(db: Session, job_id: str) -> AnalysisJob:
    job = get_analysis_job(db, job_id)
    if job is None:
        raise KeyError(job_id)
    return job


def _interrupt_job(
    job: AnalysisJob,
    detail: str,
    error_code: str | None = None,
    *,
    terminal_status: Literal["failed", "cancelled"] = "failed",
    terminal_step_status: Literal["failed", "cancelled"] = "failed",
) -> None:
    steps = _job_steps(job)
    current_step = job.current_step
    interrupted_index: int | None = None
    skipped_reason_verb = (
        "was cancelled" if terminal_status == "cancelled" else "was interrupted"
    )

    if current_step is not None:
        for index, step in enumerate(steps):
            if step.name == current_step:
                steps[index] = step.model_copy(
                    update={
                        "status": terminal_step_status,
                        "message": detail,
                        "error_code": error_code,
                        "progress": None,
                    }
                )
                interrupted_index = index
                break

    if interrupted_index is not None and current_step is not None:
        for index, step in enumerate(
            steps[interrupted_index + 1 :], start=interrupted_index + 1
        ):
            if step.status == "pending":
                steps[index] = step.model_copy(
                    update={
                        "status": "skipped",
                        "message": (
                            "Skipped because "
                            f"{current_step.replace('_', ' ')} {skipped_reason_verb}."
                        ),
                    }
                )

    _write_steps(job, steps)
    finished_at = time.time()
    job.status = terminal_status
    job.message = detail
    job.error_detail = detail
    job.error_code = error_code
    job.finished_at = finished_at
    job.updated_at = finished_at


def cancel_analysis_job(
    db: Session,
    job_id: str,
    detail: str = "Cancelled by user.",
    *,
    error_code: str = "cancelled_by_user",
) -> AnalysisJob:
    """Signal a drain on a running job.

    W13-3 (Codex H4): cancel is two-phased. This call flips a running
    job to the non-terminal ``cancelling`` state, records
    ``requested_cancel_at``, but does NOT touch step records or
    ``finished_at`` — the worker thread is still draining the shared
    executor + ``/results/``. ``finalize_cancelled_analysis_job`` (called
    by the analysis service exception handler once the worker observes
    ``AnalysisCancelledError``) performs the terminal transition.

    Idempotent on ``cancelling``: a second cancel returns the existing
    snapshot unchanged so a UI double-click cannot regress
    ``requested_cancel_at``. Terminal states still raise
    ``JobNotCancellableError`` (closing the cancel-after-finish race
    landed pre-W13).
    """
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
    job = db.scalars(stmt).first()
    if job is None:
        raise KeyError(job_id)

    if job.status in _TERMINAL_JOB_STATUSES:
        raise JobNotCancellableError(job_id, job.status)

    if job.status == "cancelling":
        # Idempotent: drain was already signalled. Do not reset
        # ``requested_cancel_at`` so the audit trail keeps the original
        # signal timestamp.
        return job

    now = time.time()
    job.status = "cancelling"
    job.message = detail
    job.error_detail = detail
    job.error_code = error_code
    job.requested_cancel_at = now
    job.updated_at = now

    try:
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise


def finalize_cancelled_analysis_job(
    db: Session,
    job_id: str,
    detail: str = "Cancelled by user.",
    *,
    error_code: str = "cancelled_by_user",
) -> AnalysisJob:
    """Complete the two-phase cancel: ``cancelling`` -> terminal ``cancelled``.

    W13-3 (Codex H4): the worker thread observes ``AnalysisCancelledError``,
    drains its in-flight step, and the analysis service exception handler
    calls this to finalize the row — step records are marked cancelled,
    trailing pending steps go to skipped, ``finished_at`` is set, and the
    partial-unique-index lock is released so ``reserve_job`` can admit
    the next job.

    Only valid from the ``cancelling`` state; any other source state
    raises ``JobNotCancellableError`` so the two-phase contract cannot be
    short-circuited (e.g. a worker successfully completing AFTER the
    cancel signal must not be allowed to overwrite the drain with
    ``completed``).
    """
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
    job = db.scalars(stmt).first()
    if job is None:
        raise KeyError(job_id)

    if job.status != "cancelling":
        raise JobNotCancellableError(job_id, job.status)

    _interrupt_job(
        job,
        detail,
        error_code=error_code,
        terminal_status="cancelled",
        terminal_step_status="cancelled",
    )

    try:
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise


class WorkerEntryOutcome(Enum):
    """Result classification for ``claim_queued_analysis_job_at_worker_entry``.

    W16-2 (AGENTS.md:57 hard rule compliance): the five outcomes form a
    complete partition over the row's observable state at worker entry.
    Callers MUST treat every non-``CLAIMED`` outcome as a terminal-exit
    signal — the worker thread MUST NOT proceed with analysis execution.
    """

    CLAIMED = "claimed"
    ALREADY_TERMINAL = "already_terminal"
    ROW_MISSING = "row_missing"
    CANCELLING_FINALIZED = "cancelling_finalized"
    CANCELLING_RACE = "cancelling_race"


@dataclass(frozen=True)
class WorkerEntryClaim:
    """Outcome + row snapshot returned by the worker-entry CRUD primitive.

    ``job`` is the row as observed under the SELECT...FOR UPDATE lock
    (or ``None`` for ``ROW_MISSING``). For ``CLAIMED`` it is the
    post-commit in-place row with ``status='running'`` and ``started_at``
    stamped. ``report_path`` is the report name to use for downstream
    instrumentation; populated for ``CLAIMED`` (with the caller-supplied
    fallback if the row had none) and mirrors ``job.report_path`` for
    the other non-missing outcomes.
    """

    outcome: WorkerEntryOutcome
    job: AnalysisJob | None
    report_path: str | None


def claim_queued_analysis_job_at_worker_entry(
    db: Session,
    job_id: str,
    *,
    fallback_report_name: str,
    cancel_detail: str = "Cancelled before worker started.",
) -> WorkerEntryClaim:
    """W13-13 (CLOSE-GATE codex-second-opinion-F3) worker-entry CAS primitive.

    Lifted out of
    ``workflows.marketplace.analysis_service.run_analysis_job`` at W16-2
    so the worker-entry seam no longer issues
    ``select(AnalysisJob).where(...).with_for_update()`` + ``db.commit()``
    directly from a workflow module (AGENTS.md:57 — writes route through
    the CRUD facade). Behavior is byte-identical with the pre-W16-2
    inline implementation; the W13-13 behavioral suite
    (``tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py``)
    and the W13-13 architecture gate
    (``tests/architecture/test_run_analysis_job_entry_snapshot.py``,
    updated at W16-2 to enforce the facade boundary instead of the
    inline AST shape) both pin the contract.

    Sequence under the caller-supplied ``db`` session:

    * Take ``select(AnalysisJob).where(AnalysisJob.job_id == job_id)
      .with_for_update()`` row lock.
    * Row missing -> ``WorkerEntryOutcome.ROW_MISSING``
      (``job=None``).
    * Row in ``_TERMINAL_JOB_STATUSES`` -> ``ALREADY_TERMINAL`` (no
      mutation).
    * Row in ``"cancelling"`` -> call
      ``finalize_cancelled_analysis_job(db, job_id, cancel_detail)``
      under the held lock; on success return ``CANCELLING_FINALIZED``;
      on ``JobNotCancellableError`` / ``KeyError`` (concurrent writer
      drove the row terminal under the same lock window) return
      ``CANCELLING_RACE``. The caller MUST treat both as terminal-exit.
    * Row in ``"queued"`` -> stamp ``status='running'``, ``started_at``,
      ``message``, ``report_path``, ``updated_at`` and ``db.commit()``
      under the lock. Returns ``CLAIMED``.

    Lock-asymmetry note (preserved from the pre-W16-2 docstring on
    ``run_analysis_job``): the ``cancelling`` branch must call the
    lifecycle helper ``finalize_cancelled_analysis_job`` directly, not
    the ``job_service.finalize_cancelled_job`` wrapper. The wrapper
    opens its own ``SessionLocal()`` via ``_run_in_session`` which would
    deadlock against the row lock held on this ``db``. The downstream
    W13-3 exception handler still uses the wrapper because by then the
    entry-block transaction has already committed and released the lock.
    """
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
    job = db.scalars(stmt).first()
    if job is None:
        return WorkerEntryClaim(
            outcome=WorkerEntryOutcome.ROW_MISSING,
            job=None,
            report_path=None,
        )
    if job.status in _TERMINAL_JOB_STATUSES:
        return WorkerEntryClaim(
            outcome=WorkerEntryOutcome.ALREADY_TERMINAL,
            job=job,
            report_path=job.report_path,
        )
    if job.status == "cancelling":
        try:
            finalize_cancelled_analysis_job(db, job_id, cancel_detail)
            return WorkerEntryClaim(
                outcome=WorkerEntryOutcome.CANCELLING_FINALIZED,
                job=job,
                report_path=job.report_path,
            )
        except (JobNotCancellableError, KeyError):
            return WorkerEntryClaim(
                outcome=WorkerEntryOutcome.CANCELLING_RACE,
                job=job,
                report_path=job.report_path,
            )
    # status == "queued" by elimination: ACTIVE statuses are
    # queued/running/cancelling; running/cancelling already returned
    # above and the schema's ACTIVE set is closed. Atomic transition
    # under the held lock.
    report_name = job.report_path or fallback_report_name
    now = time.time()
    job.status = "running"
    job.started_at = now
    job.message = "Starting sandbox analysis."
    job.report_path = report_name
    job.updated_at = now
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return WorkerEntryClaim(
        outcome=WorkerEntryOutcome.CLAIMED,
        job=job,
        report_path=report_name,
    )


def create_analysis_job(
    db: Session,
    snapshot: AnalysisJobCreateSnapshot,
) -> AnalysisJob:
    db_job = AnalysisJob(**snapshot.model_dump(mode="python"))
    try:
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except SQLAlchemyError:
        db.rollback()
        raise


def get_analysis_job(db: Session, job_id: str) -> AnalysisJob | None:
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    return db.scalars(stmt).first()


def get_active_analysis_job(db: Session) -> AnalysisJob | None:
    stmt = (
        select(AnalysisJob)
        .where(AnalysisJob.status.in_(ACTIVE_ANALYSIS_JOB_STATUSES))
        .order_by(AnalysisJob.created_at.desc())
    )
    return db.scalars(stmt).first()


def update_analysis_job(
    db: Session,
    job_id: str,
    update: AnalysisJobUpdate,
) -> AnalysisJob:
    job = _get_analysis_job_or_raise(db, job_id)

    for field_name, value in update.model_dump(exclude_unset=True).items():
        setattr(job, field_name, value)
    job.updated_at = time.time()

    try:
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise


def fail_analysis_job(
    db: Session,
    job_id: str,
    failure: AnalysisJobFailure,
) -> AnalysisJob:
    # W14-4: acquire row-level exclusive lock before the status check so
    # concurrent fail/complete writers cannot both pass their guards and
    # overwrite each other's terminal write (race window documented in
    # `test_analysis_jobs_concurrency.py:171` pre-W14-4). Mirrors the
    # `cancel_analysis_job` / `finalize_cancelled_analysis_job` lock
    # discipline at lifecycle.py:128 and :181.
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
    job = db.scalars(stmt).first()
    if job is None:
        raise KeyError(job_id)
    # W13-3: a worker that hits a hard error during drain must not flip a
    # cancelling row into `failed` — the cancel signal is authoritative,
    # the row goes terminal through finalize_cancelled_analysis_job.
    if job.status == "cancelling":
        raise JobNotCancellableError(job_id, job.status)
    # W14-4: a row already in a terminal state must not be re-failed —
    # the second writer would silently overwrite the original terminal
    # detail. Mirrors the cancel guard at lifecycle.py:133.
    if job.status in _TERMINAL_JOB_STATUSES:
        raise JobNotCancellableError(job_id, job.status)
    steps = _job_steps(job)
    current_step = job.current_step
    failed_index: int | None = None

    if current_step is not None:
        for index, step in enumerate(steps):
            if step.name == current_step:
                steps[index] = step.model_copy(
                    update={
                        "status": "failed",
                        "message": failure.detail,
                        "error_code": failure.error_code,
                        "progress": None,
                    }
                )
                failed_index = index
                break

    if failed_index is not None and current_step is not None:
        for index, step in enumerate(steps[failed_index + 1 :], start=failed_index + 1):
            if step.status == "pending":
                steps[index] = step.model_copy(
                    update={
                        "status": "skipped",
                        "message": (
                            f"Skipped because {current_step.replace('_', ' ')} failed."
                        ),
                    }
                )

    _write_steps(job, steps)
    finished_at = time.time()
    job.status = "failed"
    job.message = failure.detail
    job.error_detail = failure.detail
    job.error_code = failure.error_code
    job.finished_at = finished_at
    job.updated_at = finished_at

    try:
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise


def complete_analysis_job(
    db: Session,
    job_id: str,
    update: AnalysisJobUpdate,
) -> AnalysisJob:
    # W14-4: acquire row-level exclusive lock before the status check so a
    # concurrent cancel/fail writer cannot pass its own guard and overwrite
    # the completion. Mirrors the `cancel_analysis_job` /
    # `finalize_cancelled_analysis_job` lock discipline at
    # lifecycle.py:128 and :181.
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
    job = db.scalars(stmt).first()
    if job is None:
        raise KeyError(job_id)

    # W13-3: a worker that finished the happy-path AFTER receiving the
    # cancel signal must not promote the row to `completed`. The cancel
    # signal is authoritative; the row goes terminal through
    # finalize_cancelled_analysis_job.
    if job.status == "cancelling":
        raise JobNotCancellableError(job_id, job.status)
    # W14-4: a row already in a terminal state must not be re-completed —
    # the second writer would silently overwrite the original terminal
    # detail. Mirrors the cancel guard at lifecycle.py:133.
    if job.status in _TERMINAL_JOB_STATUSES:
        raise JobNotCancellableError(job_id, job.status)

    for field_name, value in update.model_dump(exclude_unset=True).items():
        setattr(job, field_name, value)
    job.status = "completed"
    job.updated_at = time.time()

    try:
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise


def recover_interrupted_analysis_jobs(
    db: Session,
    current_boot_id: str,
    detail: str,
) -> int:
    stmt = select(AnalysisJob).where(
        AnalysisJob.status.in_(ACTIVE_ANALYSIS_JOB_STATUSES),
        AnalysisJob.owner_boot_id != current_boot_id,
    )
    jobs = list(db.scalars(stmt).all())
    if not jobs:
        return 0

    for job in jobs:
        _interrupt_job(job, detail)

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return len(jobs)


# S2 (W23 B3): the error_code stamped on a job the stale-running reaper fails.
# Lets the report / triage surface distinguish a heartbeat-recovered wedge from
# an ordinary analysis failure.
STALE_HEARTBEAT_REAP_ERROR_CODE = "stale_heartbeat_reaped"


def touch_analysis_job_heartbeat(
    db: Session,
    job_id: str,
    *,
    now: float | None = None,
) -> int:
    """Stamp ``last_heartbeat_at`` on a ``running`` job (S2 / W23 B3).

    Targeted single-row UPDATE — no ``with_for_update`` lock and no read-back:
    the heartbeat is an idempotent liveness ping written every few seconds from
    a dedicated worker thread, so it must stay cheap and must not contend with
    the terminal-write lock discipline. Scoped to ``status == 'running'`` so a
    tick that races a completion / cancellation is a harmless no-op (rowcount 0)
    rather than resurrecting a heartbeat on a terminal row. Returns the affected
    row count (0 when the job is gone or no longer running).
    """
    ts = time.time() if now is None else now
    result = db.execute(
        update(AnalysisJob)
        .where(AnalysisJob.job_id == job_id, AnalysisJob.status == "running")
        .values(last_heartbeat_at=ts)
    )
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    # Session.execute(update(...)) returns a CursorResult at runtime; the typed
    # surface is the base Result which doesn't expose rowcount.
    return cast("CursorResult[Any]", result).rowcount


def reap_stale_running_analysis_jobs(
    db: Session,
    current_boot_id: str,
    *,
    stale_after_s: float,
    detail: str,
    now: float | None = None,
) -> int:
    """Fail same-boot ``running`` jobs whose heartbeat has gone stale (S2 / W23 B3).

    Closes the gap ``recover_interrupted_analysis_jobs`` cannot: that sweep only
    reaps rows from a *different* boot (``owner_boot_id != current_boot_id``), so
    a worker that hangs or crashes out of the closed analyze taxonomy *within the
    same API boot* keeps its row ``running`` and holds the single-active slot
    until an API restart. This reaper targets exactly those rows.

    Staleness uses ``COALESCE(last_heartbeat_at, started_at)`` so a row claimed
    but not yet heartbeat-stamped is still recoverable after the timeout from its
    claim. Each candidate is re-selected ``with_for_update`` and re-checked under
    the lock before ``_interrupt_job`` writes the terminal ``failed`` state, so a
    worker that heartbeated or finished between the scan and the lock is never
    falsely reaped (mirrors the ``fail_analysis_job`` lock discipline). Only
    ``running`` is targeted — ``cancelling`` rows are owned by the two-phase
    cancel contract, and ``queued`` rows have no worker to be stale.

    Returns the number of rows reaped.
    """
    ref = time.time() if now is None else now
    cutoff = ref - stale_after_s
    effective = func.coalesce(AnalysisJob.last_heartbeat_at, AnalysisJob.started_at)
    candidate_stmt = select(AnalysisJob.job_id).where(
        AnalysisJob.status == "running",
        AnalysisJob.owner_boot_id == current_boot_id,
        effective.is_not(None),
        effective < cutoff,
    )
    candidate_ids = list(db.scalars(candidate_stmt).all())
    if not candidate_ids:
        return 0

    reaped = 0
    for job_id in candidate_ids:
        locked_stmt = (
            select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
        )
        job = db.scalars(locked_stmt).first()
        if (
            job is None
            or job.status != "running"
            or job.owner_boot_id != current_boot_id
        ):
            # Worker drove the row terminal (or it vanished) between the scan
            # and the lock — nothing to reap.
            continue
        effective_ts = (
            job.last_heartbeat_at
            if job.last_heartbeat_at is not None
            else job.started_at
        )
        if effective_ts is None or effective_ts >= cutoff:
            # Worker heartbeated under the lock window — no longer stale.
            continue
        _interrupt_job(job, detail, error_code=STALE_HEARTBEAT_REAP_ERROR_CODE)
        reaped += 1

    if reaped:
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
    return reaped


__all__ = [
    "STALE_HEARTBEAT_REAP_ERROR_CODE",
    "JobNotCancellableError",
    "WorkerEntryClaim",
    "WorkerEntryOutcome",
    "cancel_analysis_job",
    "claim_queued_analysis_job_at_worker_entry",
    "complete_analysis_job",
    "create_analysis_job",
    "fail_analysis_job",
    "finalize_cancelled_analysis_job",
    "get_active_analysis_job",
    "get_analysis_job",
    "reap_stale_running_analysis_jobs",
    "recover_interrupted_analysis_jobs",
    "touch_analysis_job_heartbeat",
    "update_analysis_job",
]
