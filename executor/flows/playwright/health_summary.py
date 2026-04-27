"""Helpers for automation, log, and run-quality summaries."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from typing import Any

try:
    from .annotation import has_strong_target_attribution, target_stream_entries
    from .health_runtime_facts import (
        covered_scenarios_from_attempts,
        official_unresolved_chat_tool_attempts,
    )
except ImportError:  # pragma: no cover - top-level executor import mode
    from annotation import has_strong_target_attribution, target_stream_entries
    from health_runtime_facts import (
        covered_scenarios_from_attempts,
        official_unresolved_chat_tool_attempts,
    )

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
    "fatal_ui_crash": ("VS Code renderer crashed; remaining scenarios were aborted."),
    "skipped_scenarios_present": "One or more requested scenarios were skipped.",
    "extra_trigger_failures_present": "One or more extra trigger actions failed.",
    "ui_blockers_present": "UI blockers interrupted part of the run.",
    "verification_gap_present": "Some attempted capabilities could not be verified.",
    "chat_tool_verification_incomplete": (
        "Some official chat/tool attempts remained unresolved after harness verification."
    ),
    "strong_target_attribution_missing": "No strong target-owned telemetry supported attribution.",
    "official_unresolved_present": (
        "Official activation events remained unresolved after verification."
    ),
    # W8-0: typed sub-reasons that replace the generic
    # "harness_command_unavailable" bucket. Each surfaces a distinct
    # actionable failure mode of the harness ready-marker handshake.
    "harness_ready_marker_missing": "Harness ready marker never appeared.",
    "harness_ready_marker_stale": ("Harness ready marker belonged to a previous run."),
    "harness_ready_marker_invalid": "Harness ready marker was unreadable.",
    "harness_activation_timeout": (
        "Harness extension activation did not complete in time."
    ),
}

_SCENARIO_ZERO_REASON = (
    "No automation scenario was required for this non-executable fixture."
)


def automation_reason_to_text(code: str) -> str:
    return _REASON_LABELS.get(code, code.replace("_", " "))


def derive_verified_capabilities(report: Any) -> list[str]:
    target_id = getattr(report, "target_extension_id", "")
    if not target_id:
        return []

    target_activations = [
        entry
        for entry in getattr(report, "activated", [])
        if getattr(entry, "extension_id", "") == target_id
    ]
    target_file_events = getattr(report, "target_file_events", [])
    target_network_events = getattr(report, "target_network_events", [])
    verified: set[str] = set()

    if target_activations or target_file_events or target_network_events:
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
    if any(
        getattr(activation, "activation_event", "").startswith("onChatParticipant")
        or getattr(activation, "activation_event", "").startswith("onLanguageModelTool")
        for activation in target_activations
    ):
        verified.add("chat")
    if any(
        getattr(activation, "activation_event", "") == "onIssueReporterOpened"
        for activation in target_activations
    ):
        verified.add("window_ui")
    if any(
        getattr(activation, "activation_event", "").startswith("onSearch")
        for activation in target_activations
    ):
        verified.add("search_views")
    if any(
        getattr(activation, "activation_event", "").startswith("onTerminal")
        for activation in target_activations
    ):
        verified.add("terminal_tasks")
    return sorted(verified)


def count_target_activations(activations: list[Any], target_extension_id: str) -> int:
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
    execution_mode = str(getattr(report, "trigger_execution_mode", "")).strip()
    layered_execution = execution_mode == "layered_passes"
    target_extension_id = getattr(report, "target_extension_id", "")
    target_activation_count = count_target_activations(
        getattr(report, "activated", []),
        target_extension_id,
    )
    output_present = bool(str(getattr(report, "extension_host_output", "")).strip())
    target_stream_present = bool(target_stream_entries(report))
    executed_scenarios = [
        str(getattr(trace, "name", "")).strip()
        for trace in getattr(report, "scenario_traces", []) or []
        if str(getattr(trace, "name", "")).strip()
    ]
    covered_scenarios = (
        covered_scenarios_from_attempts(report) if layered_execution else []
    )
    requested_scenarios = [
        str(name).strip()
        for name in getattr(report, "requested_scenarios", []) or []
        if str(name).strip()
    ]
    failed_scenarios = sorted(set(getattr(report, "failed_scenarios", [])))
    skipped_scenarios = [
        str(getattr(item, "name", "")).strip()
        for item in getattr(report, "skipped_scenarios", []) or []
        if str(getattr(item, "name", "")).strip()
    ]
    extra_trigger_failures = sorted(set(getattr(report, "extra_trigger_failures", [])))
    strong_target_attribution = has_strong_target_attribution(report)
    unresolved_chat_tool_attempts = official_unresolved_chat_tool_attempts(report)
    reasons: list[str] = []

    if execution_mode == "skip_automation":
        return {
            "status": "healthy",
            "reasons": [],
            "trigger_requested": False,
            "trigger_loaded": False,
            "trigger_applied": False,
            "extension_host_log_present": extension_host_log_present,
            "extension_host_output_present": output_present,
            "target_stream_present": target_stream_present,
            "target_activation_count": 0,
            "failed_scenarios": [],
            "skipped_scenarios": [],
            "extra_trigger_failures": [],
            "extra_trigger_failure_count": 0,
            "extension_host_log_found": extension_host_log_found,
        }

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
    fatal_crash_traces = [
        trace
        for trace in getattr(report, "scenario_traces", []) or []
        if str(getattr(trace, "failure_reason_code", "") or "") == "fatal_ui_crash"
    ]
    if fatal_crash_traces:
        reasons.append("fatal_ui_crash")
    if skipped_scenarios:
        reasons.append("skipped_scenarios_present")
    if extra_trigger_failures:
        reasons.append("extra_trigger_failures_present")
    if getattr(report, "ui_blocker_entries", []):
        reasons.append("ui_blockers_present")
    # FOLLOWUP codex-automation-3: verification gap + chat-tool gap reasons
    # propagate regardless of execution mode. The W7 entry's "layered
    # run_quality label" fix limited these to non-layered runs, leaving
    # automation_health.status="healthy" while run_quality dropped to
    # medium for layered runs with the same evidence — operators reading
    # only the health chip got misplaced confidence.
    if getattr(report, "verification_gap", 0) > 0:
        reasons.append("verification_gap_present")
    if unresolved_chat_tool_attempts:
        reasons.append("chat_tool_verification_incomplete")
    official_event_coverage = getattr(report, "official_event_coverage", {}) or {}
    if int(official_event_coverage.get("unresolved", 0) or 0) > 0:
        reasons.append("official_unresolved_present")
    if (
        not target_stream_present
        and target_activation_count <= 0
        and not strong_target_attribution
    ):
        reasons.append("strong_target_attribution_missing")

    trigger_plan_incomplete = getattr(report, "trigger_plan_requested", False) and (
        not getattr(report, "trigger_plan_loaded", False)
        or not getattr(report, "trigger_plan_applied", False)
    )
    observed_scenario_coverage = executed_scenarios or covered_scenarios

    if (
        fatal_crash_traces
        or (
            requested_scenarios
            and not observed_scenario_coverage
            and not skipped_scenarios
        )
        or (
            not target_extension_id
            or trigger_plan_incomplete
            or not getattr(report, "target_extension_observed", False)
            or target_activation_count <= 0
            or (not target_stream_present and not strong_target_attribution)
        )
    ):
        status = "inconclusive"
    elif (requested_scenarios and skipped_scenarios) or (
        not extension_host_log_present
        or not output_present
        or not target_stream_present
        or failed_scenarios
        or extra_trigger_failures
        or getattr(report, "ui_blocker_entries", [])
        # FOLLOWUP codex-automation-3: partial-evidence signals demote to
        # ``degraded`` regardless of execution mode (was non-layered only).
        or getattr(report, "verification_gap", 0) > 0
        or unresolved_chat_tool_attempts
        or int(official_event_coverage.get("unresolved", 0) or 0) > 0
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
        "skipped_scenarios": skipped_scenarios,
        "extra_trigger_failures": extra_trigger_failures,
        "extra_trigger_failure_count": len(extra_trigger_failures),
        "extension_host_log_found": extension_host_log_found,
    }


def build_run_quality(
    report: Any,
    automation_health: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    execution_mode = str(getattr(report, "trigger_execution_mode", "")).strip()
    if execution_mode == "skip_automation":
        return "scenario_zero", [_SCENARIO_ZERO_REASON]
    health = automation_health or build_automation_health(
        report,
        extension_host_log_found=bool(getattr(report, "log_file_path", "")),
        extension_host_log_present=bool(getattr(report, "log_file_path", "")),
    )
    reasons = [automation_reason_to_text(code) for code in health.get("reasons", [])]
    status = health.get("status", "inconclusive")
    official_event_coverage = getattr(report, "official_event_coverage", {}) or {}
    official_unresolved = int(official_event_coverage.get("unresolved", 0) or 0)
    unresolved_chat_tool_attempts = official_unresolved_chat_tool_attempts(report)

    if status == "inconclusive":
        return "inconclusive", reasons
    if health.get("skipped_scenarios"):
        return "low", reasons
    # FOLLOWUP codex-automation-3: partial-evidence reasons (verification
    # gap, chat-tool unresolved, official unresolved) now demote
    # automation_health.status from "healthy" to "degraded". A layered
    # run that lands at "degraded" purely on partial-evidence signals
    # remains a medium-quality run — it would be misleading to return
    # "low" when no actual failures occurred.
    partial_evidence_reason_codes = {
        "verification_gap_present",
        "chat_tool_verification_incomplete",
        "official_unresolved_present",
    }
    health_reason_codes = set(health.get("reasons", []) or [])
    only_partial_evidence_degradation = (
        status == "degraded"
        and health_reason_codes
        and health_reason_codes.issubset(partial_evidence_reason_codes)
    )
    if execution_mode == "layered_passes":
        if status == "degraded" and not only_partial_evidence_degradation:
            return "low", reasons
        if (
            official_unresolved > 0
            or unresolved_chat_tool_attempts
            or getattr(report, "verification_gap", 0) > 0
        ):
            medium_reasons = list(reasons)
            if getattr(report, "verification_gap", 0) > 0:
                label = automation_reason_to_text("verification_gap_present")
                if label not in medium_reasons:
                    medium_reasons.append(label)
            if unresolved_chat_tool_attempts:
                label = automation_reason_to_text("chat_tool_verification_incomplete")
                if label not in medium_reasons:
                    medium_reasons.append(label)
            if official_unresolved > 0:
                label = automation_reason_to_text("official_unresolved_present")
                if label not in medium_reasons:
                    medium_reasons.append(label)
            return "medium", medium_reasons
        return "high", reasons
    if status == "degraded":
        if (
            unresolved_chat_tool_attempts
            or "chat_tool_verification_incomplete" in health.get("reasons", [])
            or "trigger_plan_not_loaded" in health.get("reasons", [])
            or "trigger_plan_not_applied" in health.get("reasons", [])
            or "scenario_failures_present" in health.get("reasons", [])
            or "extension_host_log_missing" in health.get("reasons", [])
            or getattr(report, "verification_gap", 0) >= 3
        ):
            return "low", reasons
        return "medium", reasons
    if official_unresolved > 0:
        return "medium", reasons
    return "high", reasons


def summarize_event_attempts_for_report(report: Any, *, track: str) -> dict[str, Any]:
    attempts = [
        attempt
        for attempt in getattr(report, "event_attempts", [])
        if getattr(attempt, "track", "") == track
    ]
    verified = [
        attempt for attempt in attempts if getattr(attempt, "status", "") == "verified"
    ]
    attempted_only = [
        attempt
        for attempt in attempts
        if getattr(attempt, "status", "") == "attempted_only"
    ]
    failed = [
        attempt for attempt in attempts if getattr(attempt, "status", "") == "failed"
    ]
    blocked = [
        attempt for attempt in attempts if getattr(attempt, "status", "") == "blocked"
    ]
    return {
        "track": track,
        "declared": len(attempts),
        "verified": len(verified),
        "attempted_only": len(attempted_only),
        "failed": len(failed),
        "blocked": len(blocked),
        "unresolved": max(len(attempts) - len(verified), 0),
        "declared_events": [
            str(getattr(attempt, "activation_event", ""))
            for attempt in attempts
            if str(getattr(attempt, "activation_event", "")).strip()
        ],
    }
