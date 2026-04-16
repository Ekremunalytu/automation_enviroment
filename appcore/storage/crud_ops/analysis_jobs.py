"""Read/write helpers for persisted marketplace analysis jobs."""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    ACTIVE_ANALYSIS_JOB_STATUSES,
    AnalysisJobCreateSnapshot,
    AnalysisJobFailure,
    AnalysisJobStepRecord,
    AnalysisJobStepUpdate,
    AnalysisJobUpdate,
)
from appcore.storage.models import AnalysisJob


def _get_analysis_job_or_raise(db: Session, job_id: str) -> AnalysisJob:
    job = get_analysis_job(db, job_id)
    if job is None:
        raise KeyError(job_id)
    return job


def _job_steps(job: AnalysisJob) -> list[AnalysisJobStepRecord]:
    steps = [AnalysisJobStepRecord.model_validate(step) for step in job.steps or []]
    return steps


def _write_steps(job: AnalysisJob, steps: list[AnalysisJobStepRecord]) -> None:
    job.steps = [step.model_dump(mode="python") for step in steps]


def _interrupt_job(
    job: AnalysisJob, detail: str, error_code: str | None = None
) -> None:
    steps = _job_steps(job)
    current_step = job.current_step
    failed_index: int | None = None

    if current_step is not None:
        for index, step in enumerate(steps):
            if step.name == current_step:
                steps[index] = step.model_copy(
                    update={
                        "status": "failed",
                        "message": detail,
                        "error_code": error_code,
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
                            "Skipped because "
                            f"{current_step.replace('_', ' ')} was interrupted."
                        ),
                    }
                )

    _write_steps(job, steps)
    finished_at = time.time()
    job.status = "failed"
    job.message = detail
    job.error_detail = detail
    job.error_code = error_code
    job.finished_at = finished_at
    job.updated_at = finished_at


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


def update_analysis_job_step(
    db: Session,
    job_id: str,
    step_update: AnalysisJobStepUpdate,
) -> AnalysisJob:
    job = _get_analysis_job_or_raise(db, job_id)
    steps = _job_steps(job)

    for index, step in enumerate(steps):
        if step.name == step_update.step_name:
            steps[index] = step.model_copy(
                update={
                    "status": step_update.status,
                    "message": step_update.message,
                    "error_code": step_update.error_code,
                }
            )
            break
    else:
        raise ValueError(
            f"Stored analysis job is missing canonical step {step_update.step_name}."
        )

    if step_update.status == "running":
        job.current_step = step_update.step_name
    elif step_update.status in {"completed", "skipped"}:
        if job.current_step == step_update.step_name:
            job.current_step = None
    elif step_update.status == "failed":
        job.current_step = step_update.step_name

    _write_steps(job, steps)
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
    job = _get_analysis_job_or_raise(db, job_id)
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
    job = _get_analysis_job_or_raise(db, job_id)

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
    "complete_analysis_job",
    "create_analysis_job",
    "fail_analysis_job",
    "get_active_analysis_job",
    "get_analysis_job",
    "recover_interrupted_analysis_jobs",
    "update_analysis_job",
    "update_analysis_job_step",
]
