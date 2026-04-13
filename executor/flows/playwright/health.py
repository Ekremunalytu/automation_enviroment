"""Helpers for automation and log health computation."""

from __future__ import annotations

from typing import Any

from annotation import has_strong_target_attribution, target_stream_entries

_REASON_LABELS = {
    "missing_target_extension_id": "Target extension context was missing.",
    "trigger_plan_not_loaded": "The executor could not load the trigger payload.",
    "trigger_plan_not_applied": "The trigger plan was not applied during the run.",
    "target_extension_not_observed": "The target extension was not observed during this run.",
    "target_activation_missing": "The target extension did not produce an activation entry.",
    "extension_host_log_missing": "Extension Host logs were missing or produced no new data.",
    "extension_host_output_missing": "Extension Host output was empty.",
    "target_stream_missing": "The target extension did not produce a dedicated log stream.",
    "scenario_failures_present": "One or more automation scenarios failed.",
    "extra_trigger_failures_present": "One or more extra trigger actions failed.",
    "ui_blockers_present": "UI blockers interrupted part of the run.",
    "verification_gap_present": "Some attempted capabilities could not be verified.",
    "strong_target_attribution_missing": "No strong target-owned telemetry supported attribution.",
}


def automation_reason_to_text(code: str) -> str:
    return _REASON_LABELS.get(code, code.replace("_", " "))


def count_target_activations(
    activations: list[Any],
    target_extension_id: str,
) -> int:
    if not target_extension_id:
        return 0
    return sum(
        1
        for entry in activations
        if getattr(entry, "extension_id", "") == target_extension_id
    )


def is_background_activation(activation_event: str) -> bool:
    if not activation_event:
        return False
    return activation_event in {
        "*",
        "onStartupFinished",
        "workspaceContains",
        "onView:explorer",
        "onView:search",
        "onView:output",
    } or activation_event.startswith("onLanguage")


def derive_verified_capabilities(report: Any) -> list[str]:
    target_id = getattr(report, "target_extension_id", "")
    if not target_id:
        return []

    target_activations = [
        entry
        for entry in getattr(report, "activated", [])
        if getattr(entry, "extension_id", "") == target_id
    ]
    target_running = any(
        getattr(entry, "extension_id", "") == target_id
        for entry in getattr(report, "running_extensions", [])
    )
    target_file_events = getattr(report, "target_file_events", [])
    target_network_events = getattr(report, "target_network_events", [])
    verified: set[str] = set()

    if target_running or target_activations:
        verified.add("window_ui")
    if any(
        getattr(activation, "activation_event", "").startswith("onCommand")
        for activation in target_activations
    ):
        verified.add("commands")
    if any(
        getattr(activation, "activation_event", "").startswith("onLanguage")
        for activation in target_activations
    ) or any(
        getattr(event, "scenario_name", "")
        in {"coding_session", "project_exploration", "refactor_workflow"}
        for event in target_file_events
    ):
        verified.add("languages_editor")
    if target_file_events:
        verified.add("workspace_fs")
    if any(
        getattr(activation, "activation_event", "").startswith(
            ("onDebug", "onDebugResolve")
        )
        for activation in target_activations
    ) or any(
        getattr(event, "scenario_name", "") == "debug_session"
        for event in target_file_events
    ):
        verified.add("debug")
    if any(
        getattr(activation, "activation_event", "")
        in {"onTaskType", "onTerminalProfile"}
        for activation in target_activations
    ) or any(
        getattr(event, "scenario_name", "") == "terminal_usage"
        for event in target_file_events
    ):
        verified.add("terminal_tasks")
    if any(
        getattr(activation, "activation_event", "") == "onView:scm"
        for activation in target_activations
    ):
        verified.add("scm")
    if any(
        getattr(activation, "activation_event", "") == "onView:search"
        for activation in target_activations
    ):
        verified.add("search_views")
    if any(
        getattr(activation, "activation_event", "") == "onConfiguration"
        for activation in target_activations
    ) or any(
        getattr(event, "scenario_name", "") == "settings_modification"
        for event in target_file_events
    ):
        verified.add("settings")
    if any(
        getattr(activation, "activation_event", "") == "onNotebook"
        for activation in target_activations
    ):
        verified.add("notebooks")
    if any(
        getattr(activation, "activation_event", "") == "onCustomEditor"
        for activation in target_activations
    ):
        verified.add("custom_editors")
    if any(
        getattr(activation, "activation_event", "") in {"onUri", "onWalkthrough"}
        for activation in target_activations
    ):
        verified.add("uri_walkthrough")
    if any(
        getattr(activation, "activation_event", "").startswith(
            "onAuthenticationRequest"
        )
        for activation in target_activations
    ):
        verified.add("authentication")
    if any(
        getattr(activation, "activation_event", "").startswith("onWebviewPanel")
        for activation in target_activations
    ):
        verified.add("webview")
    if target_network_events and "workspace_fs" in verified:
        verified.add("commands")

    return sorted(verified)


def reconcile_coverage_verification(
    report: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    attempted = set(getattr(report, "attempted_capabilities", []))
    verified = set(getattr(report, "verified_capabilities", []))
    matrix: list[dict[str, Any]] = []
    for entry in getattr(report, "coverage_matrix", []):
        capability = str(entry.get("capability", "")).strip()
        next_entry = dict(entry)
        next_entry["support_status"] = entry.get("status", "unknown")
        if capability in verified:
            verification_status = "verified"
        elif capability in attempted:
            verification_status = "attempted_only"
        else:
            verification_status = "not_attempted"
        next_entry["verification_status"] = verification_status
        next_entry["attempted"] = capability in attempted
        next_entry["verified"] = capability in verified
        matrix.append(next_entry)

    summary = dict(getattr(report, "coverage_summary", {}))
    summary["attempted"] = len(attempted)
    summary["verified"] = len(verified)
    summary["attempted_capabilities"] = sorted(attempted)
    summary["verified_capabilities"] = sorted(verified)
    return summary, matrix


def build_log_health(
    report: Any,
    *,
    extension_host_log_found: bool,
    extension_host_log_present: bool,
) -> dict[str, Any]:
    return {
        "extension_host_log_found": extension_host_log_found,
        "extension_host_output_present": bool(
            str(getattr(report, "extension_host_output", "")).strip()
        ),
        "target_extension_log_entries": len(target_stream_entries(report)),
        "total_activation_entries": len(getattr(report, "activated", [])),
        "extension_host_log_present": extension_host_log_present,
    }


def build_automation_health(
    report: Any,
    *,
    extension_host_log_found: bool,
    extension_host_log_present: bool,
) -> dict[str, Any]:
    target_extension_id = getattr(report, "target_extension_id", "")
    target_activation_count = count_target_activations(
        getattr(report, "activated", []),
        target_extension_id,
    )
    output_present = bool(str(getattr(report, "extension_host_output", "")).strip())
    target_stream_present = bool(target_stream_entries(report))
    failed_scenarios = sorted(set(getattr(report, "failed_scenarios", [])))
    strong_target_attribution = has_strong_target_attribution(report)
    reasons: list[str] = []

    if not target_extension_id:
        reasons.append("missing_target_extension_id")
    if getattr(report, "trigger_plan_requested", False) and not getattr(
        report, "trigger_plan_loaded", False
    ):
        reasons.append("trigger_plan_not_loaded")
    if getattr(report, "trigger_plan_requested", False) and not getattr(
        report, "trigger_plan_applied", False
    ):
        reasons.append("trigger_plan_not_applied")
    if not getattr(report, "target_extension_observed", False):
        reasons.append("target_extension_not_observed")
    if target_activation_count <= 0:
        reasons.append("target_activation_missing")
    if not extension_host_log_present:
        reasons.append("extension_host_log_missing")
    if not output_present:
        reasons.append("extension_host_output_missing")
    if not target_stream_present:
        reasons.append("target_stream_missing")
    if failed_scenarios:
        reasons.append("scenario_failures_present")
    if getattr(report, "extra_trigger_failures", []):
        reasons.append("extra_trigger_failures_present")
    if getattr(report, "ui_blocker_entries", []):
        reasons.append("ui_blockers_present")
    if getattr(report, "verification_gap", 0) > 0:
        reasons.append("verification_gap_present")
    if (
        not target_stream_present
        and target_activation_count <= 0
        and not strong_target_attribution
    ):
        reasons.append("strong_target_attribution_missing")

    if (
        not target_extension_id
        or not getattr(report, "target_extension_observed", False)
        or target_activation_count <= 0
        or (not target_stream_present and not strong_target_attribution)
    ):
        status = "inconclusive"
    elif (
        (
            getattr(report, "trigger_plan_requested", False)
            and (
                not getattr(report, "trigger_plan_loaded", False)
                or not getattr(report, "trigger_plan_applied", False)
            )
        )
        or not extension_host_log_present
        or not output_present
        or not target_stream_present
        or failed_scenarios
        or getattr(report, "extra_trigger_failures", [])
        or getattr(report, "ui_blocker_entries", [])
        or getattr(report, "verification_gap", 0) > 0
    ):
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "reasons": reasons,
        "trigger_requested": bool(getattr(report, "trigger_plan_requested", False)),
        "trigger_loaded": bool(getattr(report, "trigger_plan_loaded", False)),
        "trigger_applied": bool(getattr(report, "trigger_plan_applied", False)),
        "extension_host_log_present": extension_host_log_present,
        "extension_host_output_present": output_present,
        "target_stream_present": target_stream_present,
        "target_activation_count": target_activation_count,
        "failed_scenarios": failed_scenarios,
        "extension_host_log_found": extension_host_log_found,
    }


def build_run_quality(
    report: Any,
    automation_health: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    health = automation_health or build_automation_health(
        report,
        extension_host_log_found=bool(getattr(report, "log_file_path", "")),
        extension_host_log_present=bool(getattr(report, "log_file_path", "")),
    )
    reasons = [automation_reason_to_text(code) for code in health.get("reasons", [])]
    status = health.get("status", "inconclusive")

    if status == "inconclusive":
        return "inconclusive", reasons
    if status == "degraded":
        if (
            "trigger_plan_not_loaded" in health.get("reasons", [])
            or "trigger_plan_not_applied" in health.get("reasons", [])
            or "scenario_failures_present" in health.get("reasons", [])
            or "extension_host_log_missing" in health.get("reasons", [])
            or getattr(report, "verification_gap", 0) >= 3
        ):
            return "low", reasons
        return "medium", reasons
    return "high", reasons
