"""Static-gate terminal transition for marketplace analysis jobs (ES-3b, ADR 0016).

``reject_analysis_job_static`` mirrors ``finalize_cancelled_analysis_job`` in
``lifecycle.py``: a row-locked terminal transition that drives a job into the
``rejected_static`` state when the static pre-check gate BLOCKs an extension
(ADR 0016 §Decision 1, block-and-warn). Like the cancel finalizer it reuses the
shared JSON serialization pair from ``steps`` (dependency direction
``static_gate -> steps``) and ``lifecycle``'s ``JobNotCancellableError`` +
``_TERMINAL_JOB_STATUSES`` (``static_gate -> lifecycle``; acyclic — ``lifecycle``
never imports ``static_gate``, preserving the W11-8 subpackage invariant).
"""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.storage.crud_ops.analysis_jobs.lifecycle import (
    _TERMINAL_JOB_STATUSES,
    JobNotCancellableError,
)
from appcore.storage.crud_ops.analysis_jobs.steps import _job_steps, _write_steps
from appcore.storage.models import AnalysisJob

_GATE_BLOCK_SKIP_MESSAGE = (
    "Skipped because the static pre-check gate blocked the extension."
)


def reject_analysis_job_static(
    db: Session,
    job_id: str,
    detail: str,
    *,
    error_code: str = "static_gate_blocked",
    static_report_path: str | None = None,
) -> AnalysisJob:
    """Terminal transition for a static-gate BLOCK -> terminal ``rejected_static``.

    ES-3b (ADR 0016 §Decision 1): the static pre-check gate BLOCKed the
    extension before any sandbox spin. The in-flight ``decision_gate`` step (the
    step that produced the verdict) is marked ``completed`` — it ran to a
    decision; the rejection is carried at the job level by the terminal
    ``rejected_static`` status, not by a step failure. Every trailing ``pending``
    step (the skipped dynamic sandbox stages) goes to ``skipped``,
    ``static_report_path`` records the persisted combined-bundle JSON, and
    ``finished_at`` is set so the single-active slot releases (``rejected_static``
    is terminal, never active — ``reserve_job`` can admit the next job).

    Mirrors ``finalize_cancelled_analysis_job``'s lock discipline: a
    ``select(...).with_for_update()`` row lock guards the read-modify-write so a
    concurrent terminal writer cannot race the transition, and a row already in
    a terminal state raises ``JobNotCancellableError`` so a late writer cannot
    regress the rejection.
    """
    stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
    job = db.scalars(stmt).first()
    if job is None:
        raise KeyError(job_id)
    if job.status in _TERMINAL_JOB_STATUSES:
        raise JobNotCancellableError(job_id, job.status)

    steps = _job_steps(job)
    current_step = job.current_step
    # The gate step that produced the BLOCK verdict ran to completion — mark it
    # completed (only when still in-flight), not failed.
    if current_step is not None:
        for index, step in enumerate(steps):
            if step.name == current_step and step.status == "running":
                steps[index] = step.model_copy(
                    update={
                        "status": "completed",
                        "message": detail,
                        "error_code": error_code,
                        "progress": None,
                    }
                )
                break
    # Every remaining pending step is a skipped dynamic sandbox stage.
    for index, step in enumerate(steps):
        if step.status == "pending":
            steps[index] = step.model_copy(
                update={"status": "skipped", "message": _GATE_BLOCK_SKIP_MESSAGE}
            )
    _write_steps(job, steps)

    finished_at = time.time()
    job.status = "rejected_static"
    job.current_step = None
    job.message = detail
    job.error_detail = detail
    job.error_code = error_code
    if static_report_path is not None:
        job.static_report_path = static_report_path
    job.finished_at = finished_at
    job.updated_at = finished_at

    try:
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise


__all__ = ["reject_analysis_job_static"]
