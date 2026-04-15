"""Helpers for automation and log health computation."""

from __future__ import annotations

import json
import re
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
    "chat_tool_verification_incomplete": (
        "Some official chat/tool attempts remained unresolved after harness verification."
    ),
    "strong_target_attribution_missing": "No strong target-owned telemetry supported attribution.",
}

_HARNESS_MARKER_RE = re.compile(r"\[extrace-harness\]\s+(?P<payload>\{.*\})")
_CHAT_TOOL_FAMILIES = {"onChatParticipant", "onLanguageModelTool"}


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


def _harness_trace_records_by_attempt(
    report: Any,
) -> dict[str, list[dict[str, Any]]]:
    raw_output = str(getattr(report, "extension_host_output", "") or "")
    traces: dict[str, list[dict[str, Any]]] = {}
    for line in raw_output.splitlines():
        marker_match = _HARNESS_MARKER_RE.search(line)
        if marker_match is None:
            continue
        try:
            payload = json.loads(marker_match.group("payload"))
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        attempt_id = str(payload.get("attempt_id", "")).strip()
        if not attempt_id:
            continue
        traces.setdefault(attempt_id, []).append(payload)
    return traces


def _attempt_contracts(attempt: Any) -> set[str]:
    return {
        str(contract).strip()
        for contract in getattr(attempt, "verification_contract", []) or []
        if str(contract).strip()
    }


def _is_chat_tool_attempt(attempt: Any) -> bool:
    return str(getattr(attempt, "event_family", "")).strip() in _CHAT_TOOL_FAMILIES


def _is_harness_attempt(attempt: Any) -> bool:
    return str(getattr(attempt, "executor_action", "")).startswith("harness:") or (
        "automation_trace" in _attempt_contracts(attempt)
    )


def _official_unresolved_chat_tool_attempts(report: Any) -> list[Any]:
    return [
        attempt
        for attempt in getattr(report, "event_attempts", []) or []
        if getattr(attempt, "official", False)
        and _is_chat_tool_attempt(attempt)
        and str(getattr(attempt, "status", "")).strip() != "verified"
    ]


def _attempt_has_harness_completion_trace(
    attempt: Any,
    harness_traces: dict[str, list[dict[str, Any]]],
) -> bool:
    attempt_id = str(getattr(attempt, "attempt_id", "")).strip()
    if not attempt_id:
        return False
    return any(
        str(item.get("phase", "")).strip() in {"complete", "failed"}
        for item in harness_traces.get(attempt_id, [])
    )


def _activation_exact_matches(
    activation_event: str,
    family: str,
    target_activation_events: list[str],
) -> list[str]:
    if activation_event:
        return [
            event for event in target_activation_events if event == activation_event
        ]
    if family:
        return [event for event in target_activation_events if event == family]
    return []


def _activation_prefix_matches(
    activation_event: str,
    family: str,
    target_activation_events: list[str],
) -> list[str]:
    if activation_event:
        return [
            event
            for event in target_activation_events
            if event == activation_event or event.startswith(f"{activation_event}:")
        ]
    if family:
        return [
            event
            for event in target_activation_events
            if event == family or event.startswith(f"{family}:")
        ]
    return []


def _unique_evidence_items(existing: list[str], additions: list[str]) -> list[str]:
    return [item for item in additions if item and item not in existing]


def _mark_unverified_harness_attempt(
    attempt: Any,
    *,
    execution_closed: bool,
) -> None:
    attempt.status = "attempted_only"
    attempt.verification_status = "attempted_only"
    if execution_closed:
        detail = (
            "Harness stimulus executed but target verification remained unresolved."
        )
    else:
        detail = "Harness stimulus execution could not be confirmed through extension-host markers."
    if not str(getattr(attempt, "failure_reason_code", "")).strip():
        attempt.failure_reason_code = "harness_verification_unconfirmed"
    if not str(getattr(attempt, "result_details", "")).strip():
        attempt.result_details = detail


def _mark_attempt_verified(
    attempt: Any,
    *,
    activation_matches: list[str],
    runtime_capability_evidence: list[str],
    execution_closed: bool,
) -> None:
    attempt.status = "verified"
    attempt.verification_status = "verified"
    if activation_matches:
        attempt.evidence.extend(
            _unique_evidence_items(attempt.evidence, activation_matches)
        )
    if runtime_capability_evidence:
        attempt.evidence.extend(
            _unique_evidence_items(
                attempt.evidence,
                [
                    f"capability:{capability}"
                    for capability in runtime_capability_evidence
                ],
            )
        )
    if execution_closed:
        harness_item = f"harness_trace:{getattr(attempt, 'attempt_id', '')}"
        attempt.evidence.extend(
            _unique_evidence_items(attempt.evidence, [harness_item])
        )


def reconcile_event_attempts(report: Any) -> list[Any]:
    attempts = list(getattr(report, "event_attempts", []))
    if not attempts:
        return attempts

    target_id = getattr(report, "target_extension_id", "")
    target_activations = [
        entry
        for entry in getattr(report, "activated", [])
        if getattr(entry, "extension_id", "") == target_id
    ]
    target_activation_events = [
        str(getattr(entry, "activation_event", "")).strip()
        for entry in target_activations
        if str(getattr(entry, "activation_event", "")).strip()
    ]
    derived_verified_capabilities = set(derive_verified_capabilities(report))
    harness_traces = _harness_trace_records_by_attempt(report)

    for attempt in attempts:
        activation_event = str(getattr(attempt, "activation_event", "")).strip()
        family = str(getattr(attempt, "event_family", "")).strip()
        contracts = _attempt_contracts(attempt)
        if getattr(attempt, "status", "") == "failed":
            attempt.verification_status = "failed"
            continue
        if getattr(attempt, "status", "") == "blocked":
            attempt.verification_status = "blocked"
            continue

        attempted_passes = list(getattr(attempt, "attempted_passes", []) or [])
        capability_tags = {
            str(tag).strip()
            for tag in getattr(attempt, "capability_tags", []) or []
            if str(tag).strip()
        }
        exact_matches = _activation_exact_matches(
            activation_event,
            family,
            target_activation_events,
        )
        prefix_matches = _activation_prefix_matches(
            activation_event,
            family,
            target_activation_events,
        )
        runtime_capability_evidence = sorted(
            capability_tags & derived_verified_capabilities
        )
        execution_closed = _attempt_has_harness_completion_trace(
            attempt,
            harness_traces,
        )

        if not contracts:
            target_reaction_closed = bool(exact_matches or prefix_matches)
            if not target_reaction_closed and attempted_passes:
                target_reaction_closed = bool(runtime_capability_evidence)
            if target_reaction_closed:
                _mark_attempt_verified(
                    attempt,
                    activation_matches=exact_matches or prefix_matches,
                    runtime_capability_evidence=runtime_capability_evidence,
                    execution_closed=False,
                )
                continue
        else:
            execution_required = "automation_trace" in contracts
            target_reaction_required = bool(
                contracts
                & {
                    "activation_log_exact",
                    "activation_log_prefix",
                    "target_runtime_delta",
                }
            )
            target_reaction_closed = False
            activation_matches: list[str] = []

            if "activation_log_exact" in contracts and exact_matches:
                activation_matches = exact_matches
                target_reaction_closed = True
            if (
                not target_reaction_closed
                and "activation_log_prefix" in contracts
                and prefix_matches
            ):
                activation_matches = prefix_matches
                target_reaction_closed = True
            if (
                not target_reaction_closed
                and "target_runtime_delta" in contracts
                and attempted_passes
                and runtime_capability_evidence
            ):
                target_reaction_closed = True

            if (not execution_required or execution_closed) and (
                not target_reaction_required or target_reaction_closed
            ):
                _mark_attempt_verified(
                    attempt,
                    activation_matches=activation_matches,
                    runtime_capability_evidence=runtime_capability_evidence,
                    execution_closed=execution_required and execution_closed,
                )
                continue

        if getattr(attempt, "status", "") in {"running", "planned", "attempted_only"}:
            attempted_evidence = bool(attempted_passes or execution_closed)
            if attempted_evidence:
                if _is_harness_attempt(attempt):
                    _mark_unverified_harness_attempt(
                        attempt,
                        execution_closed=execution_closed,
                    )
                else:
                    attempt.status = "attempted_only"
                    attempt.verification_status = "attempted_only"
            elif getattr(attempt, "blocked_reason_code", ""):
                attempt.status = "blocked"
                attempt.verification_status = "blocked"
            else:
                attempt.status = "failed"
                attempt.verification_status = "failed"
    return attempts


def summarize_event_attempts_for_report(
    report: Any,
    *,
    track: str,
) -> dict[str, Any]:
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


def reconcile_coverage_verification(
    report: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    coverage_tracks = getattr(report, "coverage_tracks", {}) or {}
    official_summary, official_matrix = _reconcile_track(
        coverage_tracks.get("official", {}).get(
            "summary",
            getattr(report, "coverage_summary", {}),
        ),
        coverage_tracks.get("official", {}).get(
            "matrix",
            getattr(report, "coverage_matrix", []),
        ),
        set(getattr(report, "official_attempted_capabilities", [])),
        set(getattr(report, "official_verified_capabilities", [])),
    )
    heuristic_summary, heuristic_matrix = _reconcile_track(
        coverage_tracks.get("heuristic", {}).get("summary", {}),
        coverage_tracks.get("heuristic", {}).get("matrix", []),
        set(getattr(report, "heuristic_attempted_capabilities", [])),
        set(getattr(report, "heuristic_verified_capabilities", [])),
    )
    return (
        official_summary,
        official_matrix,
        {
            "official": {
                "source": coverage_tracks.get("official", {}).get(
                    "source",
                    "official_activation_track",
                ),
                "selected_scenarios": coverage_tracks.get("official", {}).get(
                    "selected_scenarios",
                    [],
                ),
                "summary": official_summary,
                "matrix": official_matrix,
            },
            "heuristic": {
                "source": coverage_tracks.get("heuristic", {}).get(
                    "source",
                    "heuristic_workflow_track",
                ),
                "selected_scenarios": coverage_tracks.get("heuristic", {}).get(
                    "selected_scenarios",
                    [],
                ),
                "summary": heuristic_summary,
                "matrix": heuristic_matrix,
            },
        },
    )


def _reconcile_track(
    summary: dict[str, Any],
    matrix_entries: list[dict[str, Any]],
    attempted: set[str],
    verified: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    supported_capabilities = {
        str(entry.get("capability", "")).strip()
        for entry in matrix_entries
        if str(entry.get("support_status", entry.get("status", "unknown"))).strip()
        == "covered"
    }
    attempted = {
        capability
        for capability in attempted
        if not supported_capabilities or capability in supported_capabilities
    }
    verified = {
        capability
        for capability in verified
        if not supported_capabilities or capability in supported_capabilities
    }
    matrix: list[dict[str, Any]] = []
    for entry in matrix_entries:
        capability = str(entry.get("capability", "")).strip()
        next_entry = dict(entry)
        next_entry["support_status"] = entry.get(
            "support_status",
            entry.get("status", "unknown"),
        )
        supported = next_entry["support_status"] == "covered"
        if capability in verified and supported:
            verification_status = "verified"
        elif capability in attempted and supported:
            verification_status = "attempted_only"
        else:
            verification_status = "not_attempted"
        next_entry["verification_status"] = verification_status
        next_entry["attempted"] = supported and capability in attempted
        next_entry["verified"] = supported and capability in verified
        matrix.append(next_entry)

    next_summary = dict(summary)
    next_summary["attempted"] = len(attempted)
    next_summary["verified"] = len(verified)
    next_summary["attempted_capabilities"] = sorted(attempted)
    next_summary["verified_capabilities"] = sorted(verified)
    return next_summary, matrix


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
    extra_trigger_failures = sorted(set(getattr(report, "extra_trigger_failures", [])))
    strong_target_attribution = has_strong_target_attribution(report)
    unresolved_chat_tool_attempts = _official_unresolved_chat_tool_attempts(report)
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
    if extra_trigger_failures:
        reasons.append("extra_trigger_failures_present")
    if getattr(report, "ui_blocker_entries", []):
        reasons.append("ui_blockers_present")
    if getattr(report, "verification_gap", 0) > 0:
        reasons.append("verification_gap_present")
    if unresolved_chat_tool_attempts:
        reasons.append("chat_tool_verification_incomplete")
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

    if (
        not target_extension_id
        or trigger_plan_incomplete
        or not getattr(report, "target_extension_observed", False)
        or target_activation_count <= 0
        or (not target_stream_present and not strong_target_attribution)
    ):
        status = "inconclusive"
    elif (
        not extension_host_log_present
        or not output_present
        or not target_stream_present
        or failed_scenarios
        or extra_trigger_failures
        or getattr(report, "ui_blocker_entries", [])
        or getattr(report, "verification_gap", 0) > 0
        or unresolved_chat_tool_attempts
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
        "extra_trigger_failures": extra_trigger_failures,
        "extra_trigger_failure_count": len(extra_trigger_failures),
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
    official_event_coverage = getattr(report, "official_event_coverage", {}) or {}
    official_unresolved = int(official_event_coverage.get("unresolved", 0) or 0)
    unresolved_chat_tool_attempts = _official_unresolved_chat_tool_attempts(report)

    if status == "inconclusive":
        return "inconclusive", reasons
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
