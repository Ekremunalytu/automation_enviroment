"""Sandbox analysis orchestration for marketplace workflow."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from appcore.db.session import SessionLocal
from executor.host import (
    ExecutorError,
    install_extension_in_executor,
    reset_executor_sandbox_state,
    run_playwright_automation,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace.job_store import (
    build_report_name,
    fail_job,
    get_job_snapshot,
    now,
    update_job,
    update_job_step,
)
from workflows.marketplace.trigger_service import build_trigger_payload

logger = logging.getLogger(__name__)


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
    progress_callback: Callable[[str, str, str], None] | None = None,
    report_name: str | None = None,
) -> AnalyzeResponse:
    def report(step_name: str, status: str, message: str) -> None:
        if progress_callback is not None:
            progress_callback(step_name, status, message)

    ensure_vsix_exists(request)

    report(
        "reset_sandbox",
        "running",
        "Resetting executor sandbox to a clean baseline.",
    )
    try:
        reset_executor_sandbox_state()
    except ExecutorError:
        report(
            "reset_sandbox",
            "failed",
            "Sandbox reset failed before extension installation.",
        )
        raise
    report("reset_sandbox", "completed", "Sandbox reset completed.")

    report(
        "install_extension",
        "running",
        "Installing extension in the executor sandbox.",
    )
    try:
        install_output = install_extension_in_executor(
            request.publisher,
            request.name,
            request.version,
        )
    except ExecutorError:
        report(
            "install_extension",
            "failed",
            "Extension installation failed inside the sandbox.",
        )
        raise
    report("install_extension", "completed", "Extension installed in sandbox.")

    trigger_container_path: str | None = None
    report(
        "build_triggers",
        "running",
        "Resolving activation events and contribution metadata.",
    )
    try:
        trigger_container_path, _, trigger_message = build_trigger_payload(db, request)
        report("build_triggers", "completed", trigger_message)
    except (SQLAlchemyError, OSError, ValueError, TypeError, AttributeError) as exc:
        logger.warning(
            "Failed to build trigger payload for %s.%s: %s",
            request.publisher,
            request.name,
            exc,
        )
        report(
            "build_triggers",
            "completed",
            (
                "Trigger selection failed; continuing with degraded reliability "
                "and default sandbox flow."
            ),
        )

    report(
        "run_monitoring",
        "running",
        "Reloading VS Code under monitoring and executing automation scenarios.",
    )
    report_name = report_name or build_report_name(request, uuid4().hex)
    report_container_path = f"/results/{report_name}"
    try:
        automation_output = run_playwright_automation(
            report_path=report_container_path,
            scenario=request.scenario,
            trigger_container_path=trigger_container_path,
            reload_before_run=True,
            target_extension_id=f"{request.publisher}.{request.name}",
        )
    except ExecutorError:
        report(
            "run_monitoring",
            "failed",
            "Sandbox automation failed before the report could be finalized.",
        )
        raise
    report("run_monitoring", "completed", "Sandbox automation finished.")
    report("finalize_report", "completed", f"Report exported to {report_name}.")

    return AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            "installed and analyzed successfully."
        ),
        install_output=install_output,
        automation_output=automation_output,
        report_path=report_name,
    )


def map_executor_error(exc: ExecutorError) -> HTTPException:
    message = str(exc)
    if "install" in message.lower():
        detail = f"Failed to install extension in executor: {message}"
    else:
        detail = f"Automation failed: {message}"
    return HTTPException(status_code=502, detail=detail)


def run_analysis_job(job_id: str, request: AnalyzeRequest) -> None:
    report_name = get_job_snapshot(job_id)["report_path"] or build_report_name(
        request,
        job_id,
    )
    update_job(
        job_id,
        status="running",
        message="Starting sandbox analysis.",
        report_path=report_name,
        started_at=now(),
    )

    db = SessionLocal()
    try:
        result = execute_analysis_request(
            request,
            db,
            progress_callback=lambda step, status, message: update_job_step(
                job_id,
                step,
                status,
                message,
            ),
            report_name=report_name,
        )
    except (
        FileNotFoundError,
        ExecutorError,
        OSError,
        SQLAlchemyError,
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        fail_job(job_id, str(exc))
        return
    finally:
        db.close()

    update_job(
        job_id,
        status="completed",
        current_step=None,
        message=result.message,
        report_path=result.report_path,
        install_output=result.install_output,
        automation_output=result.automation_output,
        finished_at=now(),
    )


__all__ = [
    "ensure_vsix_exists",
    "execute_analysis_request",
    "map_executor_error",
    "run_analysis_job",
]
