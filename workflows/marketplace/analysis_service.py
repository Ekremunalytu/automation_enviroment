"""Sandbox analysis orchestration for marketplace workflow."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.api.config import settings
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


class TriggerPlanError(RuntimeError):
    """Raised when trigger planning fails closed."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def _load_report_payload(report_name: str) -> dict[str, object] | None:
    report_path = Path(settings.project.OUTPUT_DIR) / report_name
    if not report_path.exists():
        return None
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _build_report_messages(
    report_name: str,
    payload: dict[str, object] | None = None,
) -> tuple[str, str]:
    payload = payload if payload is not None else _load_report_payload(report_name)
    if payload is None:
        return (
            "Sandbox automation finished, but report health details were unavailable.",
            f"Report exported to {report_name}.",
        )

    automation_health = payload.get("automation_health")
    if not isinstance(automation_health, dict):
        return (
            "Sandbox automation finished, but the report did not contain "
            "automation health metadata.",
            f"Report exported to {report_name}.",
        )

    status = str(automation_health.get("status", "unknown"))
    trigger_requested = bool(automation_health.get("trigger_requested", False))
    trigger_loaded = bool(automation_health.get("trigger_loaded", False))
    trigger_applied = bool(automation_health.get("trigger_applied", False))
    target_count = int(automation_health.get("target_activation_count", 0) or 0)
    failed_scenarios = automation_health.get("failed_scenarios", [])
    failed_count = len(failed_scenarios) if isinstance(failed_scenarios, list) else 0
    summary = payload.get("summary")
    scenarios_run = []
    if isinstance(summary, dict) and isinstance(summary.get("scenarios_run"), list):
        scenarios_run = [str(item) for item in summary["scenarios_run"]]

    monitoring_message = (
        f"Sandbox automation finished with {status} health; "
        "trigger requested="
        f"{trigger_requested}, loaded={trigger_loaded}, "
        f"applied={trigger_applied}; "
        f"executed scenarios=[{', '.join(scenarios_run) or 'none'}]."
    )
    finalize_message = (
        f"Report exported to {report_name}; health={status}; "
        f"target activations={target_count}; failed scenarios={failed_count}."
    )
    return monitoring_message, finalize_message


def _validate_trigger_plan_report(
    report_name: str,
    payload: dict[str, object] | None,
) -> None:
    if payload is None:
        raise TriggerPlanError(
            "trigger_load_failed",
            (
                "Sandbox automation finished but trigger-plan health details were "
                f"missing for {report_name}."
            ),
        )

    automation_health = payload.get("automation_health")
    if not isinstance(automation_health, dict):
        raise TriggerPlanError(
            "trigger_load_failed",
            "Sandbox automation report did not contain trigger-plan health metadata.",
        )

    if not bool(automation_health.get("trigger_loaded", False)):
        raise TriggerPlanError(
            "trigger_load_failed",
            "Executor could not load the trigger payload inside the sandbox.",
        )

    if not bool(automation_health.get("trigger_applied", False)):
        raise TriggerPlanError(
            "trigger_apply_failed",
            "Executor did not apply the trigger payload during sandbox automation.",
        )

    execution_mode = str(payload.get("trigger_execution_mode", "")).strip()
    if execution_mode != "layered_passes":
        raise TriggerPlanError(
            "trigger_apply_failed",
            (
                "Executor loaded the trigger payload but did not run layered passes; "
                f"execution mode was {execution_mode or 'unknown'}."
            ),
        )

    stimulus_passes = payload.get("stimulus_passes")
    finalized_stimulus_pass = False
    if isinstance(stimulus_passes, list):
        finalized_stimulus_pass = any(
            isinstance(item, dict)
            and str(item.get("status", "")).strip() in {"completed", "failed"}
            for item in stimulus_passes
        )
    if not finalized_stimulus_pass:
        raise TriggerPlanError(
            "trigger_apply_failed",
            (
                "Executor loaded the trigger payload but did not finalize any "
                "layered stimulus pass."
            ),
        )

    event_attempts = payload.get("event_attempts")
    attempted_pass_recorded = False
    if isinstance(event_attempts, list):
        attempted_pass_recorded = any(
            isinstance(item, dict)
            and isinstance(item.get("attempted_passes"), list)
            and any(str(pass_name).strip() for pass_name in item["attempted_passes"])
            for item in event_attempts
        )
    if not attempted_pass_recorded:
        raise TriggerPlanError(
            "trigger_apply_failed",
            (
                "Executor loaded the trigger payload but did not record any "
                "attempted layered event pass."
            ),
        )


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
    progress_callback: Callable[[str, str, str, str | None], None] | None = None,
    report_name: str | None = None,
) -> AnalyzeResponse:
    def report(
        step_name: str,
        status: str,
        message: str,
        error_code: str | None = None,
    ) -> None:
        if progress_callback is not None:
            progress_callback(step_name, status, message, error_code)

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
    trigger_message = "No trigger payload requested; default sandbox flow will run."
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
            "failed",
            "Trigger payload build failed before sandbox automation started.",
            "trigger_build_failed",
        )
        raise TriggerPlanError(
            "trigger_build_failed",
            f"Failed to build trigger payload: {exc}",
        ) from exc

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
    report_payload = _load_report_payload(report_name)
    if trigger_container_path is not None:
        try:
            _validate_trigger_plan_report(report_name, report_payload)
        except TriggerPlanError as exc:
            report(
                "run_monitoring",
                "failed",
                str(exc),
                exc.error_code,
            )
            raise
    monitoring_message, finalize_message = _build_report_messages(
        report_name,
        report_payload,
    )
    report("run_monitoring", "completed", monitoring_message)
    report("finalize_report", "completed", finalize_message)

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

    def progress_update(
        step: str,
        status: str,
        message: str,
        error_code: str | None = None,
    ) -> None:
        update_job_step(
            job_id,
            step,
            status,
            message,
            error_code=error_code,
        )

    try:
        result = execute_analysis_request(
            request,
            db,
            progress_callback=progress_update,
            report_name=report_name,
        )
    except (
        FileNotFoundError,
        ExecutorError,
        TriggerPlanError,
        OSError,
        SQLAlchemyError,
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        fail_job(job_id, str(exc), error_code=getattr(exc, "error_code", None))
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
    "TriggerPlanError",
    "ensure_vsix_exists",
    "execute_analysis_request",
    "map_executor_error",
    "run_analysis_job",
]
