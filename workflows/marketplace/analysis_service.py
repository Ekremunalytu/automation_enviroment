"""Sandbox analysis orchestration for marketplace workflow."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepName,
    AnalysisJobStepStatus,
)
from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from executor.control import (
    ExecutorControl,
    ExecutorError,
    default_executor_control,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace import job_service
from workflows.marketplace.analysis_errors import (
    AnalysisCancelledError,
    TriggerPlanError,
)
from workflows.marketplace.analysis_execution import (
    StepReporter as _StepReporter,
)
from workflows.marketplace.analysis_execution import (
    build_triggers as _build_triggers,
)
from workflows.marketplace.analysis_execution import (
    install_extension as _install_extension,
)
from workflows.marketplace.analysis_execution import (
    reset_sandbox as _reset_sandbox,
)
from workflows.marketplace.analysis_execution import (
    run_monitoring as _run_monitoring,
)
from workflows.marketplace.analysis_reports import (
    build_analysis_bundle_from_report_name,
    run_local_analysis,
)
from workflows.marketplace.analysis_reports import (
    build_report_messages as _build_report_messages,
)
from workflows.marketplace.analysis_reports import (
    load_report_payload as _load_report_payload,
)
from workflows.marketplace.analysis_reports import (
    trigger_payload_exists as _trigger_payload_exists,
)
from workflows.marketplace.analysis_reports import (
    validate_trigger_plan_report as _validate_trigger_plan_report,
)
from workflows.marketplace.trigger_service import TriggerPlan, build_trigger_payload

logger = logging.getLogger(__name__)


def _open_job_session() -> Session:
    from appcore.db.session import SessionLocal

    return SessionLocal()


def ensure_vsix_exists(request: AnalyzeRequest) -> Path:
    vsix_path = marketplace_client.get_vsix_path(
        request.publisher,
        request.name,
        request.version,
    )
    if not vsix_path.exists():
        raise FileNotFoundError(
            f"VSIX file not found: {vsix_path.name}. "
            "Download the extension first via /api/marketplace/download."
        )
    return vsix_path


def execute_analysis_request(
    request: AnalyzeRequest,
    db: Session,
    progress_callback: Callable[
        [
            AnalysisJobStepName,
            AnalysisJobStepStatus,
            str,
            str | None,
            dict[str, int] | None,
        ],
        None,
    ]
    | None = None,
    report_name: str | None = None,
    executor_control: ExecutorControl | None = None,
    cancel_check: Callable[[], bool] | None = None,
    on_cancel_signal: Callable[[], None] | None = None,
) -> AnalyzeResponse:
    if executor_control is None:
        executor_control = default_executor_control
    reporter = _StepReporter(progress_callback)
    ensure_vsix_exists(request)
    _reset_sandbox(reporter, executor_control)
    install_output = _install_extension(request, reporter, executor_control)
    trigger_plan = _build_triggers(
        db,
        request,
        reporter,
        build_trigger_payload_func=build_trigger_payload,
        trigger_plan_type=TriggerPlan,
    )
    report_name = report_name or job_service.build_report_name(request, uuid4().hex)
    automation_output, finalize_message = _run_monitoring(
        request,
        report_name,
        trigger_plan,
        reporter,
        executor_control,
        trigger_payload_exists=_trigger_payload_exists,
        load_report_payload=_load_report_payload,
        validate_trigger_plan_report=_validate_trigger_plan_report,
        build_report_messages=_build_report_messages,
        cancel_check=cancel_check,
        on_cancel_signal=on_cancel_signal,
    )

    return AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            f"installed and analyzed successfully. {finalize_message}"
        ),
        install_output=install_output,
        automation_output=automation_output,
        report_path=report_name,
    )


def map_executor_error(exc: ExecutorError) -> HTTPException:
    raw = str(exc)
    error_id = uuid4().hex[:8]
    if "install" in raw.lower():
        public_detail = "Failed to install extension in executor."
    else:
        public_detail = "Automation failed in sandbox."
    logger.warning("executor_error error_id=%s message=%s", error_id, raw)
    return HTTPException(
        status_code=502,
        detail=f"{public_detail} (error_id={error_id})",
    )


def run_analysis_job(job_id: str, request: AnalyzeRequest) -> None:
    report_name = job_service.get_job_snapshot(job_id)[
        "report_path"
    ] or job_service.build_report_name(
        request,
        job_id,
    )
    job_service.update_job(
        job_id,
        status="running",
        message="Starting sandbox analysis.",
        report_path=report_name,
        started_at=job_service.now(),
    )

    db = _open_job_session()

    def progress_update(
        step: AnalysisJobStepName,
        status: AnalysisJobStepStatus,
        message: str,
        error_code: str | None = None,
        progress: dict[str, int] | None = None,
    ) -> None:
        try:
            job_service.update_job_step(
                job_id,
                step,
                status,
                message,
                error_code=error_code,
                progress=progress,
            )
        except KeyError:
            # Job row vanished (very unlikely outside tests); swallow so the
            # automation thread doesn't crash on a missing snapshot.
            logger.warning("Progress update dropped: job %s no longer exists.", job_id)

    def cancel_check() -> bool:
        return job_service.is_job_cancelled(job_id)

    try:
        result = execute_analysis_request(
            request,
            db,
            progress_callback=progress_update,
            report_name=report_name,
            cancel_check=cancel_check,
        )
    except AnalysisCancelledError:
        return
    except (TypeError, AttributeError) as exc:
        job_service.fail_job(
            job_id,
            str(exc),
            error_code=getattr(exc, "error_code", None),
        )
        raise
    except (
        FileNotFoundError,
        ExecutorError,
        TriggerPlanError,
        OSError,
        SQLAlchemyError,
        ValueError,
    ) as exc:
        if job_service.is_job_cancelled(job_id):
            return
        job_service.fail_job(
            job_id,
            str(exc),
            error_code=getattr(exc, "error_code", None),
        )
        return
    finally:
        db.close()

    job_service.complete_job(job_id, result)


__all__ = [
    "TriggerPlanError",
    "build_analysis_bundle_from_report_name",
    "ensure_vsix_exists",
    "execute_analysis_request",
    "map_executor_error",
    "run_analysis_job",
    "run_local_analysis",
]
