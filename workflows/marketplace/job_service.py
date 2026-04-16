"""DB-backed orchestration helpers for marketplace analysis jobs."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from copy import deepcopy
from typing import Any, TypeVar
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobCreateSnapshot,
    AnalysisJobFailure,
    AnalysisJobPersistedRecord,
    AnalysisJobStepName,
    AnalysisJobStepRecord,
    AnalysisJobStepStatus,
    AnalysisJobStepUpdate,
    AnalysisJobUpdate,
)
from appcore.contracts.schemas import (
    AnalyzeJobStatusResponse,
    AnalyzeRequest,
    AnalyzeResponse,
)
from appcore.db.session import SessionLocal
from appcore.storage.crud import (
    complete_analysis_job,
    create_analysis_job,
    fail_analysis_job,
    get_active_analysis_job,
    get_analysis_job,
    recover_interrupted_analysis_jobs,
    update_analysis_job,
    update_analysis_job_step,
)
from appcore.storage.models import AnalysisJob

_PROCESS_BOOT_ID = uuid4().hex
T = TypeVar("T")


class ActiveAnalysisJobError(RuntimeError):
    """Raised when a new analysis job is requested while another job is active."""

    def __init__(self, active_job: dict[str, Any]) -> None:
        super().__init__("Another sandbox analysis is already in progress.")
        self.active_job = deepcopy(active_job)


def now() -> float:
    return time.time()


def empty_job_steps() -> list[AnalysisJobStepRecord]:
    return [
        AnalysisJobStepRecord(
            name="reset_sandbox",
            status="pending",
            message="Waiting for sandbox cleanup.",
        ),
        AnalysisJobStepRecord(
            name="install_extension",
            status="pending",
            message="Queued.",
        ),
        AnalysisJobStepRecord(
            name="build_triggers",
            status="pending",
            message="Waiting for activation metadata.",
        ),
        AnalysisJobStepRecord(
            name="run_monitoring",
            status="pending",
            message="Waiting for sandbox automation.",
        ),
        AnalysisJobStepRecord(
            name="finalize_report",
            status="pending",
            message="Waiting for report export.",
        ),
    ]


def build_report_name(request: AnalyzeRequest, run_id: str) -> str:
    return (
        f"activation_report_{request.publisher}.{request.name}-"
        f"{request.version}-{run_id[:12]}.json"
    )


def create_job_snapshot(
    request: AnalyzeRequest,
    *,
    owner_boot_id: str | None = None,
    owner_pid: int | None = None,
) -> dict[str, Any]:
    created_at = now()
    job_id = uuid4().hex
    snapshot = AnalysisJobCreateSnapshot(
        job_id=job_id,
        owner_boot_id=owner_boot_id or _PROCESS_BOOT_ID,
        owner_pid=owner_pid or os.getpid(),
        status="queued",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        scenario=request.scenario,
        analysis_profile=request.analysis_profile,
        current_step=None,
        message="Queued for sandbox analysis.",
        steps=empty_job_steps(),
        report_path=build_report_name(request, job_id),
        install_output=None,
        automation_output=None,
        error_detail=None,
        error_code=None,
        created_at=created_at,
        started_at=None,
        finished_at=None,
        updated_at=created_at,
    )
    return snapshot.model_dump(mode="python")


def _run_in_session(
    db: Session | None,
    operation: Callable[[Session], T],
) -> T:
    if db is not None:
        return operation(db)

    session = SessionLocal()
    try:
        return operation(session)
    finally:
        session.close()


def _persisted_snapshot(job: AnalysisJob) -> dict[str, Any]:
    record = AnalysisJobPersistedRecord.model_validate(job, from_attributes=True)
    return record.model_dump(mode="python")


def _public_snapshot(job: AnalysisJob) -> dict[str, Any]:
    persisted = _persisted_snapshot(job)
    response_fields = AnalyzeJobStatusResponse.model_fields
    payload = {
        field_name: persisted[field_name]
        for field_name in response_fields
        if field_name in persisted
    }
    response = AnalyzeJobStatusResponse.model_validate(payload)
    return response.model_dump(mode="python")


def store_job(job: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    snapshot = AnalysisJobCreateSnapshot.model_validate(job)

    def operation(session: Session) -> dict[str, Any]:
        stored = create_analysis_job(session, snapshot)
        return _persisted_snapshot(stored)

    return _run_in_session(db, operation)


def reserve_job(
    request: AnalyzeRequest,
    db: Session | None = None,
) -> dict[str, Any]:
    snapshot = AnalysisJobCreateSnapshot.model_validate(create_job_snapshot(request))

    def operation(session: Session) -> dict[str, Any]:
        active_job = get_active_analysis_job(session)
        if active_job is not None:
            raise ActiveAnalysisJobError(_public_snapshot(active_job))

        try:
            stored = create_analysis_job(session, snapshot)
        except IntegrityError:
            active_job = get_active_analysis_job(session)
            if active_job is not None:
                raise ActiveAnalysisJobError(_public_snapshot(active_job)) from None
            raise
        return _public_snapshot(stored)

    return _run_in_session(db, operation)


def get_job_snapshot(job_id: str, db: Session | None = None) -> dict[str, Any]:
    def operation(session: Session) -> dict[str, Any]:
        job = get_analysis_job(session, job_id)
        if job is None:
            raise KeyError(job_id)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def get_persisted_job_snapshot(
    job_id: str,
    db: Session | None = None,
) -> dict[str, Any]:
    def operation(session: Session) -> dict[str, Any]:
        job = get_analysis_job(session, job_id)
        if job is None:
            raise KeyError(job_id)
        return _persisted_snapshot(job)

    return _run_in_session(db, operation)


def get_active_job_snapshot(db: Session | None = None) -> dict[str, Any] | None:
    def operation(session: Session) -> dict[str, Any] | None:
        active_job = get_active_analysis_job(session)
        if active_job is None:
            return None
        return _public_snapshot(active_job)

    return _run_in_session(db, operation)


def get_active_persisted_job_snapshot(
    db: Session | None = None,
) -> dict[str, Any] | None:
    def operation(session: Session) -> dict[str, Any] | None:
        active_job = get_active_analysis_job(session)
        if active_job is None:
            return None
        return _persisted_snapshot(active_job)

    return _run_in_session(db, operation)


def update_job(
    job_id: str,
    db: Session | None = None,
    **updates: Any,
) -> dict[str, Any]:
    update = AnalysisJobUpdate.model_validate(updates)

    def operation(session: Session) -> dict[str, Any]:
        job = update_analysis_job(session, job_id, update)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def update_job_step(
    job_id: str,
    step_name: AnalysisJobStepName,
    status: AnalysisJobStepStatus,
    message: str,
    *,
    db: Session | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    step_update = AnalysisJobStepUpdate(
        step_name=step_name,
        status=status,
        message=message,
        error_code=error_code,
    )

    def operation(session: Session) -> dict[str, Any]:
        job = update_analysis_job_step(session, job_id, step_update)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def fail_job(
    job_id: str,
    detail: str,
    *,
    db: Session | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    failure = AnalysisJobFailure(detail=detail, error_code=error_code)

    def operation(session: Session) -> dict[str, Any]:
        job = fail_analysis_job(session, job_id, failure)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def complete_job(
    job_id: str,
    result: AnalyzeResponse,
    *,
    db: Session | None = None,
) -> dict[str, Any]:
    update = AnalysisJobUpdate(
        status="completed",
        current_step=None,
        message=result.message,
        report_path=result.report_path,
        install_output=result.install_output,
        automation_output=result.automation_output,
        finished_at=now(),
    )

    def operation(session: Session) -> dict[str, Any]:
        job = complete_analysis_job(session, job_id, update)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def recover_interrupted_jobs(db: Session | None = None) -> int:
    detail = "Analysis job was interrupted by an API restart. Start a new run."

    def operation(session: Session) -> int:
        return recover_interrupted_analysis_jobs(session, _PROCESS_BOOT_ID, detail)

    return _run_in_session(db, operation)


__all__ = [
    "ActiveAnalysisJobError",
    "build_report_name",
    "complete_job",
    "create_job_snapshot",
    "empty_job_steps",
    "fail_job",
    "get_active_job_snapshot",
    "get_active_persisted_job_snapshot",
    "get_job_snapshot",
    "get_persisted_job_snapshot",
    "now",
    "recover_interrupted_jobs",
    "reserve_job",
    "store_job",
    "update_job",
    "update_job_step",
]
