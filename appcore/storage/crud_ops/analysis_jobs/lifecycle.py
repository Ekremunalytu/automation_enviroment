"""Lifecycle helpers for persisted marketplace analysis jobs.

Owns create/cancel/complete/fail + recovery + read paths plus the shared
`JobNotCancellableError` and the terminal-status set. Imports the JSON
serialization pair (`_job_steps` / `_write_steps`) from
`appcore.storage.crud_ops.analysis_jobs.steps` — the dependency direction is
strictly `lifecycle -> steps` to keep the subpackage acyclic (W11-8).
"""

from __future__ import annotations

import time
from typing import Literal

from sqlalchemy import select
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


_TERMINAL_JOB_STATUSES: frozenset[str] = frozenset({"completed", "failed", "cancelled"})


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


__all__ = [
    "JobNotCancellableError",
    "cancel_analysis_job",
    "complete_analysis_job",
    "create_analysis_job",
    "fail_analysis_job",
    "finalize_cancelled_analysis_job",
    "get_active_analysis_job",
    "get_analysis_job",
    "recover_interrupted_analysis_jobs",
    "update_analysis_job",
]
