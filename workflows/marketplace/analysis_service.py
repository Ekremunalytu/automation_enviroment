"""Sandbox analysis orchestration for marketplace workflow."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepName,
    AnalysisJobStepStatus,
)
from appcore.contracts.schemas import AnalysisBundle, AnalyzeRequest, AnalyzeResponse
from executor.control import (
    ExecutorControl,
    ExecutorError,
    default_executor_control,
)
from packages.analysis_contracts import ActivationReport, ExtensionIdentity
from packages.analysis_engine import run_detection
from workflows.marketplace import client as marketplace_client
from workflows.marketplace import job_service
from workflows.marketplace.trigger_service import TriggerPlan, build_trigger_payload

logger = logging.getLogger(__name__)


class TriggerPlanError(RuntimeError):
    """Raised when trigger planning fails closed."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def _coerce_trigger_plan(plan: object) -> TriggerPlan:
    if isinstance(plan, TriggerPlan):
        return plan
    if isinstance(plan, tuple) and len(plan) == 3:
        trigger_container_path, selected_scenarios, message = plan
        return TriggerPlan(
            trigger_container_path=(
                str(trigger_container_path) if trigger_container_path else None
            ),
            selected_scenarios=[str(item) for item in selected_scenarios or []],
            skip_automation=False,
            reason_code="legacy_trigger_plan",
            message=str(message),
        )
    raise TypeError(
        "build_trigger_payload must return TriggerPlan or legacy "
        "(trigger_container_path, selected_scenarios, message) tuple."
    )


def _monitoring_failure_message(exc: ExecutorError) -> str:
    detail = str(exc).strip()
    if not detail:
        return "Sandbox automation failed before the report could be finalized."
    return f"Sandbox automation failed before the report could be finalized: {detail}"


def _open_job_session() -> Session:
    from appcore.db.session import SessionLocal

    return SessionLocal()


def _load_report_payload(report_name: str) -> dict[str, object] | None:
    report_path = Path(settings.project.OUTPUT_DIR) / report_name
    if not report_path.exists():
        return None
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_local_report(fixture_path: Path) -> tuple[ActivationReport, str]:
    report_path = fixture_path / "activation_report.json"
    if not report_path.exists():
        raise FileNotFoundError(
            f"No offline activation report fixture found for {fixture_path}."
        )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(
            "Offline activation report fixture must contain a JSON object: "
            f"{report_path}"
        )
    return ActivationReport.model_validate(payload), report_path.name


def _load_fixture_identity(
    fixture_path: Path,
    activation_report: ActivationReport,
) -> ExtensionIdentity:
    package_json_path = fixture_path / "package.json"
    if package_json_path.exists():
        payload = json.loads(package_json_path.read_text(encoding="utf-8"))
        return ExtensionIdentity(
            publisher=str(payload.get("publisher", "unknown")),
            name=str(payload.get("name", "unknown")),
            version=str(payload.get("version", "unknown")),
        )

    summary = (
        activation_report.summary if isinstance(activation_report.summary, dict) else {}
    )
    version = str(summary.get("target_extension_version", "0.0.1"))
    publisher, separator, name = activation_report.target_extension_expected.partition(
        "."
    )
    if not separator:
        publisher = "unknown"
        name = activation_report.target_extension_expected or "unknown"
    return ExtensionIdentity(publisher=publisher, name=name, version=version)


def _infer_identity_from_report_name(
    report_name: str,
    activation_report: ActivationReport,
) -> ExtensionIdentity:
    summary = (
        activation_report.summary if isinstance(activation_report.summary, dict) else {}
    )
    version = str(summary.get("target_extension_version", "unknown"))
    expected = activation_report.target_extension_expected or "unknown.unknown"
    publisher, separator, name = expected.partition(".")
    if not separator:
        publisher = "unknown"
        name = expected or "unknown"

    if report_name.startswith("activation_report_"):
        remainder = report_name.removeprefix("activation_report_").removesuffix(".json")
        try:
            extension_id, parsed_version, _ = remainder.rsplit("-", 2)
        except ValueError:
            extension_id = ""
        else:
            parsed_publisher, parsed_separator, parsed_name = extension_id.partition(
                "."
            )
            if parsed_separator:
                publisher = parsed_publisher
                name = parsed_name
                version = parsed_version
    return ExtensionIdentity(publisher=publisher, name=name, version=version)


def build_analysis_bundle_from_report_name(
    report_name: str,
    *,
    analyzed_extension: ExtensionIdentity | None = None,
) -> AnalysisBundle | None:
    payload = _load_report_payload(report_name)
    if payload is None:
        return None
    try:
        activation_report = ActivationReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid activation report payload for {report_name}"
        ) from exc

    resolved_extension = analyzed_extension or _infer_identity_from_report_name(
        report_name,
        activation_report,
    )
    detection_report = run_detection(
        activation_report,
        activation_report_ref=report_name,
        analyzed_extension=resolved_extension,
    )
    return AnalysisBundle(
        activation_report=activation_report,
        detection_report=detection_report,
    )


def run_local_analysis(fixture_path: str | Path) -> AnalysisBundle:
    """Run the package-local detection engine against a stored fixture report."""

    resolved_fixture = Path(fixture_path).resolve()
    activation_report, report_name = _load_local_report(resolved_fixture)
    analyzed_extension = _load_fixture_identity(resolved_fixture, activation_report)
    return AnalysisBundle(
        activation_report=activation_report,
        detection_report=run_detection(
            activation_report,
            activation_report_ref=report_name,
            analyzed_extension=analyzed_extension,
        ),
    )


def _trigger_host_path(trigger_container_path: str | None) -> Path | None:
    if not trigger_container_path:
        return None
    return Path(settings.project.OUTPUT_DIR) / Path(trigger_container_path).name


def _trigger_payload_exists(trigger_container_path: str | None) -> bool:
    trigger_host_path = _trigger_host_path(trigger_container_path)
    return bool(trigger_host_path and trigger_host_path.exists())


def _run_monitoring_heartbeat(
    stop_event: threading.Event,
    reporter: _StepReporter,
    *,
    interval_s: float = 30.0,
) -> None:
    while not stop_event.wait(interval_s):
        reporter.emit(
            "run_monitoring",
            "running",
            "Sandbox automation is still running inside the executor.",
        )


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
    extra_trigger_failures = payload.get("extra_trigger_failures", [])
    if not isinstance(extra_trigger_failures, list):
        extra_trigger_failures = automation_health.get("extra_trigger_failures", [])
    extra_trigger_failure_count = (
        len(extra_trigger_failures) if isinstance(extra_trigger_failures, list) else 0
    )
    summary = payload.get("summary")
    scenarios_run = []
    if isinstance(summary, dict) and isinstance(summary.get("scenarios_run"), list):
        scenarios_run = [str(item) for item in summary["scenarios_run"]]

    monitoring_message = (
        f"Sandbox automation finished with {status} health; "
        "trigger requested="
        f"{trigger_requested}, loaded={trigger_loaded}, "
        f"applied={trigger_applied}; "
        f"executed scenarios=[{', '.join(scenarios_run) or 'none'}]; "
        f"extra trigger failures={extra_trigger_failure_count}."
    )
    finalize_message = (
        f"Report exported to {report_name}; health={status}; "
        f"target activations={target_count}; failed scenarios={failed_count}; "
        f"extra trigger failures={extra_trigger_failure_count}."
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


class _StepReporter:
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


def _reset_sandbox(
    reporter: _StepReporter,
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


def _install_extension(
    request: AnalyzeRequest,
    reporter: _StepReporter,
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
    except ExecutorError:
        reporter.emit(
            "install_extension",
            "failed",
            "Extension installation failed inside the sandbox.",
        )
        raise
    reporter.emit("install_extension", "completed", "Extension installed in sandbox.")
    return install_output


def _build_triggers(
    db: Session,
    request: AnalyzeRequest,
    reporter: _StepReporter,
) -> TriggerPlan:
    reporter.emit(
        "build_triggers",
        "running",
        "Resolving activation events and contribution metadata.",
    )
    try:
        trigger_plan = _coerce_trigger_plan(build_trigger_payload(db, request))
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

    reporter.emit("build_triggers", "completed", trigger_plan.message)
    return trigger_plan


def _run_monitoring(
    request: AnalyzeRequest,
    report_name: str,
    trigger_plan: TriggerPlan,
    reporter: _StepReporter,
    executor_control: ExecutorControl,
) -> tuple[str, str]:
    reporter.emit(
        "run_monitoring",
        "running",
        "Reloading VS Code under monitoring and executing automation scenarios.",
    )
    report_container_path = f"/results/{report_name}"
    trigger_payload_exists = _trigger_payload_exists(
        trigger_plan.trigger_container_path
    )
    effective_scenario = request.scenario
    if (
        not effective_scenario
        and trigger_plan.trigger_container_path
        and not trigger_payload_exists
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
            _monitoring_failure_message(exc),
        )
        raise
    finally:
        heartbeat_stop.set()
        heartbeat_thread.join(timeout=1.0)

    report_payload = _load_report_payload(report_name)
    if trigger_plan.trigger_container_path is not None and trigger_payload_exists:
        try:
            _validate_trigger_plan_report(report_name, report_payload)
        except TriggerPlanError as exc:
            reporter.emit(
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
    reporter.emit("run_monitoring", "completed", monitoring_message)
    reporter.emit("finalize_report", "completed", finalize_message)
    return automation_output, finalize_message


def execute_analysis_request(
    request: AnalyzeRequest,
    db: Session,
    progress_callback: Callable[
        [AnalysisJobStepName, AnalysisJobStepStatus, str, str | None],
        None,
    ]
    | None = None,
    report_name: str | None = None,
    executor_control: ExecutorControl | None = None,
) -> AnalyzeResponse:
    if executor_control is None:
        executor_control = default_executor_control
    reporter = _StepReporter(progress_callback)
    ensure_vsix_exists(request)
    _reset_sandbox(reporter, executor_control)
    install_output = _install_extension(request, reporter, executor_control)
    trigger_plan = _build_triggers(db, request, reporter)
    report_name = report_name or job_service.build_report_name(request, uuid4().hex)
    automation_output, finalize_message = _run_monitoring(
        request,
        report_name,
        trigger_plan,
        reporter,
        executor_control,
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
    message = str(exc)
    if "install" in message.lower():
        detail = f"Failed to install extension in executor: {message}"
    else:
        detail = f"Automation failed: {message}"
    return HTTPException(status_code=502, detail=detail)


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
    ) -> None:
        job_service.update_job_step(
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
    "ensure_vsix_exists",
    "execute_analysis_request",
    "map_executor_error",
    "run_analysis_job",
]
