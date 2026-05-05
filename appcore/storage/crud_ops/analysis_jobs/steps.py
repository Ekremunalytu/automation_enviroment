"""Step-level helpers for persisted marketplace analysis jobs.

Owns the JSON serialization helpers (`_job_steps`, `_write_steps`) plus the
single public step-update entry point. Lifecycle helpers in
`appcore.storage.crud_ops.analysis_jobs.lifecycle` import the serialization
pair from here; this module never imports from `lifecycle` (W11-8 cycle break).
"""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepRecord,
    AnalysisJobStepUpdate,
)
from appcore.storage.models import AnalysisJob


def _job_steps(job: AnalysisJob) -> list[AnalysisJobStepRecord]:
    steps = [AnalysisJobStepRecord.model_validate(step) for step in job.steps or []]
    return steps


def _write_steps(job: AnalysisJob, steps: list[AnalysisJobStepRecord]) -> None:
    job.steps = [step.model_dump(mode="python") for step in steps]


def update_analysis_job_step(
    db: Session,
    job_id: str,
    step_update: AnalysisJobStepUpdate,
) -> AnalysisJob:
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id)
    job = db.scalars(stmt).first()
    if job is None:
        raise KeyError(job_id)

    steps = _job_steps(job)

    if step_update.status in {"completed", "skipped", "cancelled"}:
        next_progress = None
    else:
        next_progress = step_update.progress

    for index, step in enumerate(steps):
        if step.name == step_update.step_name:
            steps[index] = step.model_copy(
                update={
                    "status": step_update.status,
                    "message": step_update.message,
                    "error_code": step_update.error_code,
                    "progress": next_progress,
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
    elif step_update.status in {"failed", "cancelled"}:
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


__all__ = [
    "update_analysis_job_step",
]
