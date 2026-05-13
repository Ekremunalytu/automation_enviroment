"""Report and fixture helpers for marketplace analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from appcore.api.config import settings
from appcore.contracts.schemas import AnalysisBundle
from packages.analysis_contracts import ActivationReport, ExtensionIdentity
from packages.analysis_engine import run_detection

from .analysis_errors import ActivationReportLoadError, TriggerPlanError


def _safe_int_coerce(value: Any, *, default: int = 0) -> int:
    """Coerce an extension-controlled scalar to ``int``.

    Closes the M11 audit gap (`[FOLLOWUP
    codex-2026-05-10-M11-report-health-malformed-types]`):
    ``automation_health`` is parsed from JSON written inside the sandboxed
    analyzed extension; a malicious extension can place a non-numeric
    string, list, dict, ``NaN``, or out-of-range value where the report
    builder previously called ``int(...)`` directly. The raw ``int()``
    call raises ``ValueError`` / ``TypeError`` / ``OverflowError`` and the
    enclosing analysis job fails. Returning ``default`` on every coercion
    failure keeps ``build_report_messages`` total — the report is exported
    with a neutral count instead of the job blowing up.

    String inputs honor an explicit ``int(stripped)`` parse first, then
    fall back to ``int(float(stripped))`` so ``"3.0"`` / ``"3e2"`` shapes
    are still counted. ``NaN`` / ``±inf`` floats short-circuit to default
    before the cast (``int()`` raises ``ValueError`` on them). The single
    outer ``except (TypeError, ValueError, OverflowError)`` is the
    defense-in-depth net that catches every coercion failure the per-type
    branches don't pre-empt — including ``int(<list>)`` /
    ``int(<dict>)`` / ``int(<custom-class>)``.
    """
    if value is None:
        return default
    try:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return default
            try:
                return int(stripped)
            except ValueError:
                return int(float(stripped))
        if isinstance(value, float) and (
            not (value == value)  # noqa: PLR0124 — explicit NaN check
            or value in (float("inf"), float("-inf"))
        ):
            return default
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def load_report_payload(report_name: str) -> dict[str, object] | None:
    report_path = Path(settings.project.OUTPUT_DIR) / report_name
    if not report_path.exists():
        return None
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ActivationReportLoadError(
            f"Failed to read activation report {report_name}: {exc}"
        ) from exc
    except (ValueError, TypeError) as exc:
        raise ActivationReportLoadError(
            f"Activation report {report_name} is not valid JSON."
        ) from exc
    if not isinstance(payload, dict):
        raise ActivationReportLoadError(
            f"Activation report {report_name} must contain a JSON object."
        )
    return payload


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
    payload = load_report_payload(report_name)
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


def trigger_host_path(trigger_container_path: str | None) -> Path | None:
    if not trigger_container_path:
        return None
    return Path(settings.project.OUTPUT_DIR) / Path(trigger_container_path).name


def trigger_payload_exists(trigger_container_path: str | None) -> bool:
    host_path = trigger_host_path(trigger_container_path)
    return bool(host_path and host_path.exists())


def build_report_messages(
    report_name: str,
    payload: dict[str, object] | None = None,
) -> tuple[str, str]:
    payload = payload if payload is not None else load_report_payload(report_name)
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
    target_count = _safe_int_coerce(
        automation_health.get("target_activation_count"), default=0
    )
    failed_scenarios = automation_health.get("failed_scenarios", [])
    failed_count = len(failed_scenarios) if isinstance(failed_scenarios, list) else 0
    skipped_scenarios = automation_health.get("skipped_scenarios", [])
    skipped_count = len(skipped_scenarios) if isinstance(skipped_scenarios, list) else 0
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
        f"skipped scenarios={skipped_count}; "
        f"extra trigger failures={extra_trigger_failure_count}."
    )
    finalize_message = (
        f"Report exported to {report_name}; health={status}; "
        f"target activations={target_count}; failed scenarios={failed_count}; "
        f"skipped scenarios={skipped_count}; "
        f"extra trigger failures={extra_trigger_failure_count}."
    )
    return monitoring_message, finalize_message


def validate_trigger_plan_report(
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


__all__ = [
    "build_analysis_bundle_from_report_name",
    "build_report_messages",
    "load_report_payload",
    "run_local_analysis",
    "trigger_payload_exists",
    "validate_trigger_plan_report",
]
