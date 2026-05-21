"""Execution-step helpers for marketplace sandbox analysis."""

from __future__ import annotations

import threading
from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepName,
    AnalysisJobStepStatus,
)
from appcore.contracts.schemas import AnalyzeRequest
from appcore.logging import get_extrace_logger
from executor.control import ExecutorControl, ExecutorError
from packages.analysis_contracts import redact_multiline_secrets, redact_secrets
from workflows.marketplace.trigger_service import TriggerPlan

from .analysis_errors import AnalysisCancelledError, TriggerPlanError

logger = get_extrace_logger("extrace.workflows.marketplace.analysis_execution")


ProgressCallback = Callable[
    [
        AnalysisJobStepName,
        AnalysisJobStepStatus,
        str,
        str | None,
        dict[str, int] | None,
    ],
    None,
]


class StepReporter:
    """Thin progress adapter for marketplace analysis steps."""

    def __init__(self, progress_callback: ProgressCallback | None) -> None:
        self._progress_callback = progress_callback

    def emit(
        self,
        step_name: AnalysisJobStepName,
        status: AnalysisJobStepStatus,
        message: str,
        error_code: str | None = None,
        progress: dict[str, int] | None = None,
    ) -> None:
        if self._progress_callback is not None:
            self._progress_callback(step_name, status, message, error_code, progress)


def raise_if_cancelled(cancel_check: Callable[[], bool] | None) -> None:
    """Raise ``AnalysisCancelledError`` when ``cancel_check`` reports a signal.

    W13-3 (Codex H4): the analysis worker polls this at every major phase
    boundary in ``execute_analysis_request`` (ensure_vsix, reset_sandbox,
    install_extension, build_triggers, run_monitoring) so cancellation does
    not have to wait for the 5-second heartbeat tick — the worker drops
    out of its current step within milliseconds of the cancel signal,
    bounded by the next phase boundary at worst. ``cancel_check`` is the
    same lambda the heartbeat thread uses; ``None`` is a no-op so the
    helper is safe in code paths where cancellation is not wired (tests,
    local scripts).
    """
    if cancel_check is not None and cancel_check():
        raise AnalysisCancelledError("Analysis cancelled by user.")


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
    # W10-7 (closes [FOLLOWUP w8-6-output-signals-redaction]) and
    # [FOLLOWUP marketplace-installer-tail-multiline-redaction]: installer
    # stderr/stdout is extension-derived text that lands in the operator job log.
    # Collapse cross-line spans before tailing so a 500-char boundary cannot
    # split a PEM block away from its BEGIN marker.
    sanitized_output = redact_multiline_secrets(output)
    tail = redact_secrets(sanitized_output[-500:].strip())
    return f"{base} Installer output (tail): {tail}"


def _run_monitoring_heartbeat(
    stop_event: threading.Event,
    reporter: StepReporter,
    *,
    report_path: str,
    total_initial: int,
    load_report_payload: Callable[[str], dict[str, object] | None],
    cancel_check: Callable[[], bool] | None = None,
    on_cancel: Callable[[], None] | None = None,
    interval_s: float = 5.0,
) -> None:
    cancel_emitted = False
    while not stop_event.wait(interval_s):
        if cancel_check is not None and cancel_check():
            if not cancel_emitted and on_cancel is not None:
                cancel_emitted = True
                try:
                    on_cancel()
                except (
                    ExecutorError,
                    RuntimeError,
                    OSError,
                    ValueError,
                    AttributeError,
                ):
                    logger.exception(
                        "on_cancel handler failed in monitoring heartbeat."
                    )
            break

        try:
            payload = load_report_payload(report_path) or {}
        except (OSError, ValueError):
            payload = {}
        raw_traces = payload.get("scenario_traces") or []
        traces: list[dict[str, object]] = (
            list(raw_traces) if isinstance(raw_traces, list) else []
        )
        done = 0
        for trace in traces:
            if not isinstance(trace, dict):
                continue
            if str(trace.get("status", "")) in {"completed", "failed"}:
                done += 1
        total = max(total_initial, len(traces))
        if total:
            reporter.emit(
                "run_monitoring",
                "running",
                f"Scenario {done}/{total} complete.",
                progress={"completed": done, "total": total},
            )
        else:
            reporter.emit(
                "run_monitoring",
                "running",
                "Sandbox automation is still running inside the executor.",
            )


COORDINATOR_THREAD_NAME = "analysis-sandbox-reset-coordinator"
_COORDINATOR_POLL_INTERVAL_S = 0.1


def _run_reset_off_thread(
    executor_control: ExecutorControl,
    cancel_check: Callable[[], bool] | None,
) -> None:
    """ADR 0012 Option A1: run step-1 setup reset on a dedicated coordinator
    thread so the worker frame stays responsive to cancel within ~100ms
    (W13-3 boundary cadence) rather than blocking on reset duration. The
    cancel-path teardown reset on the heartbeat thread is unaffected and
    keeps the W17-2 smoke pin (`"harness-monitoring-heartbeat"` +
    `reload_window=True`) byte-identical.
    """
    done = threading.Event()
    holder: dict[str, BaseException | None] = {"exc": None}

    def _target() -> None:
        try:
            executor_control.reset_sandbox()
        except (
            ExecutorError,
            RuntimeError,
            OSError,
            ValueError,
            AttributeError,
        ) as exc:
            holder["exc"] = exc
        finally:
            done.set()

    thread = threading.Thread(
        target=_target,
        daemon=True,
        name=COORDINATOR_THREAD_NAME,
    )
    thread.start()
    while not done.wait(timeout=_COORDINATOR_POLL_INTERVAL_S):
        raise_if_cancelled(cancel_check)
    if holder["exc"] is not None:
        raise holder["exc"]


def reset_sandbox(
    reporter: StepReporter,
    executor_control: ExecutorControl,
    cancel_check: Callable[[], bool] | None = None,
) -> None:
    reporter.emit(
        "reset_sandbox",
        "running",
        "Resetting executor sandbox to a clean baseline.",
    )
    try:
        _run_reset_off_thread(executor_control, cancel_check)
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
    cancel_check: Callable[[], bool] | None = None,
    on_cancel_signal: Callable[[], None] | None = None,
    harness_python_secret: str | None = None,
) -> tuple[str, str]:
    total_scenarios = len(trigger_plan.selected_scenarios)
    reporter.emit(
        "run_monitoring",
        "running",
        "Reloading VS Code under monitoring and executing automation scenarios.",
        progress=(
            {"completed": 0, "total": total_scenarios} if total_scenarios else None
        ),
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
    cancel_triggered = threading.Event()

    def _heartbeat_on_cancel() -> None:
        cancel_triggered.set()
        if on_cancel_signal is not None:
            on_cancel_signal()
        try:
            executor_control.reset_sandbox(reload_window=True)
        except ExecutorError:
            logger.exception(
                "Sandbox reset during cancel did not complete cleanly; "
                "executor process will be killed by the next reset attempt."
            )

    heartbeat_stop = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_run_monitoring_heartbeat,
        args=(heartbeat_stop, reporter),
        kwargs={
            "report_path": report_name,
            "total_initial": total_scenarios,
            "load_report_payload": load_report_payload,
            "cancel_check": cancel_check,
            "on_cancel": _heartbeat_on_cancel,
        },
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
            harness_python_secret=harness_python_secret,
        )
    except ExecutorError as exc:
        if cancel_triggered.is_set():
            raise AnalysisCancelledError("Analysis cancelled by user.") from exc
        reporter.emit(
            "run_monitoring",
            "failed",
            monitoring_failure_message(exc),
        )
        raise
    finally:
        heartbeat_stop.set()
        heartbeat_thread.join(timeout=1.0)

    if cancel_triggered.is_set():
        raise AnalysisCancelledError("Analysis cancelled by user.")

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
    "COORDINATOR_THREAD_NAME",
    "StepReporter",
    "build_triggers",
    "install_extension",
    "install_failure_message",
    "monitoring_failure_message",
    "raise_if_cancelled",
    "reset_sandbox",
    "run_monitoring",
]
