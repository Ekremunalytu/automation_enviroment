"""Execution-step helpers for marketplace sandbox analysis."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepName,
    AnalysisJobStepStatus,
)
from appcore.contracts.schemas import AnalyzeRequest
from executor.control import ExecutorControl, ExecutorError
from workflows.marketplace.trigger_service import TriggerPlan

from .analysis_errors import TriggerPlanError

logger = logging.getLogger(__name__)


class StepReporter:
    """Thin progress adapter for marketplace analysis steps."""

    def __init__(
        self,
        progress_callback: Callable[
            [AnalysisJobStepName, AnalysisJobStepStatus, str, str | None],
            None,
        ]
        | None,
    ) -> None:
        self._progress_callback = progress_callback

    def emit(
        self,
        step_name: AnalysisJobStepName,
        status: AnalysisJobStepStatus,
        message: str,
        error_code: str | None = None,
    ) -> None:
        if self._progress_callback is not None:
            self._progress_callback(step_name, status, message, error_code)


def monitoring_failure_message(exc: ExecutorError) -> str:
    detail = str(exc).strip()
    if not detail:
        return "Sandbox automation failed before the report could be finalized."
    return f"Sandbox automation failed before the report could be finalized: {detail}"


def install_failure_message(exc: ExecutorError) -> str:
    """Surface the ``code --install-extension`` CLI stderr tail in the job log.

    ``ExecutorError`` carries the CLI's stderr/stdout in ``exc.output`` but
    ``str(exc)`` is just the rc/command line — without this helper the
    operator only sees ``rc=1`` and has no signal for whether the failure is
    a bad VSIX, a stale singleton lock, or an IPC race.
    """
    base = "Extension installation failed inside the sandbox."
    output = (exc.output or "").strip()
    if not output:
        return base
    tail = output[-500:].strip()
    return f"{base} Installer output (tail): {tail}"


def _run_monitoring_heartbeat(
    stop_event: threading.Event,
    reporter: StepReporter,
    *,
    interval_s: float = 30.0,
) -> None:
    while not stop_event.wait(interval_s):
        reporter.emit(
            "run_monitoring",
            "running",
            "Sandbox automation is still running inside the executor.",
        )


def reset_sandbox(
    reporter: StepReporter,
    executor_control: ExecutorControl,
) -> None:
    reporter.emit(
        "reset_sandbox",
        "running",
        "Resetting executor sandbox to a clean baseline.",
    )
    try:
        executor_control.reset_sandbox()
    except ExecutorError:
        reporter.emit(
            "reset_sandbox",
            "failed",
            "Sandbox reset failed before extension installation.",
        )
        raise
    reporter.emit("reset_sandbox", "completed", "Sandbox reset completed.")


def install_extension(
    request: AnalyzeRequest,
    reporter: StepReporter,
    executor_control: ExecutorControl,
) -> str:
    reporter.emit(
        "install_extension",
        "running",
        "Installing extension in the executor sandbox.",
    )
    try:
        install_output = executor_control.install_extension(
            request.publisher,
            request.name,
            request.version,
        )
    except ExecutorError as exc:
        reporter.emit(
            "install_extension",
            "failed",
            install_failure_message(exc),
        )
        raise
    reporter.emit("install_extension", "completed", "Extension installed in sandbox.")
    return install_output


def build_triggers(
    db: Session,
    request: AnalyzeRequest,
    reporter: StepReporter,
    *,
    build_trigger_payload_func: Callable[[Session, AnalyzeRequest], object],
    trigger_plan_type: type[TriggerPlan],
) -> TriggerPlan:
    reporter.emit(
        "build_triggers",
        "running",
        "Resolving activation events and contribution metadata.",
    )
    try:
        trigger_plan = build_trigger_payload_func(db, request)
    except (SQLAlchemyError, OSError, ValueError) as exc:
        logger.warning(
            "Failed to build trigger payload for %s.%s: %s",
            request.publisher,
            request.name,
            exc,
        )
        reporter.emit(
            "build_triggers",
            "failed",
            "Trigger payload build failed before sandbox automation started.",
            "trigger_build_failed",
        )
        raise TriggerPlanError(
            "trigger_build_failed",
            f"Failed to build trigger payload: {exc}",
        ) from exc
    if not isinstance(trigger_plan, trigger_plan_type):
        raise TypeError("build_trigger_payload must return TriggerPlan.")
    reporter.emit("build_triggers", "completed", trigger_plan.message)
    return trigger_plan


def run_monitoring(
    request: AnalyzeRequest,
    report_name: str,
    trigger_plan: TriggerPlan,
    reporter: StepReporter,
    executor_control: ExecutorControl,
    *,
    trigger_payload_exists: Callable[[str | None], bool],
    load_report_payload: Callable[[str], dict[str, object] | None],
    validate_trigger_plan_report: Callable[[str, dict[str, object] | None], None],
    build_report_messages: Callable[
        [str, dict[str, object] | None],
        tuple[str, str],
    ],
) -> tuple[str, str]:
    reporter.emit(
        "run_monitoring",
        "running",
        "Reloading VS Code under monitoring and executing automation scenarios.",
    )
    report_container_path = f"/results/{report_name}"
    payload_exists = trigger_payload_exists(trigger_plan.trigger_container_path)
    effective_scenario = request.scenario
    if (
        not effective_scenario
        and trigger_plan.trigger_container_path
        and not payload_exists
        and trigger_plan.selected_scenarios
    ):
        effective_scenario = trigger_plan.selected_scenarios[0]
    heartbeat_stop = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_run_monitoring_heartbeat,
        args=(heartbeat_stop, reporter),
        daemon=True,
        name="analysis-run-monitoring-heartbeat",
    )
    heartbeat_thread.start()
    try:
        automation_output = executor_control.run_automation(
            report_path=report_container_path,
            scenario=effective_scenario,
            trigger_container_path=trigger_plan.trigger_container_path,
            skip_automation=trigger_plan.skip_automation,
            reload_before_run=True,
            target_extension_id=f"{request.publisher}.{request.name}",
        )
    except ExecutorError as exc:
        reporter.emit(
            "run_monitoring",
            "failed",
            monitoring_failure_message(exc),
        )
        raise
    finally:
        heartbeat_stop.set()
        heartbeat_thread.join(timeout=1.0)

    report_payload = load_report_payload(report_name)
    if trigger_plan.trigger_container_path is not None and payload_exists:
        try:
            validate_trigger_plan_report(report_name, report_payload)
        except TriggerPlanError as exc:
            reporter.emit(
                "run_monitoring",
                "failed",
                str(exc),
                exc.error_code,
            )
            raise

    monitoring_message, finalize_message = build_report_messages(
        report_name,
        report_payload,
    )
    reporter.emit("run_monitoring", "completed", monitoring_message)
    reporter.emit("finalize_report", "completed", finalize_message)
    return automation_output, finalize_message


__all__ = [
    "StepReporter",
    "build_triggers",
    "install_extension",
    "install_failure_message",
    "monitoring_failure_message",
    "reset_sandbox",
    "run_monitoring",
]
