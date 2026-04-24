"""Shared runtime fact helpers for health reconciliation and summaries."""

from __future__ import annotations

from typing import Any

_CHAT_TOOL_FAMILIES = {"onChatParticipant", "onLanguageModelTool"}


def attempt_contracts(attempt: Any) -> set[str]:
    return {
        str(contract).strip()
        for contract in getattr(attempt, "verification_contract", []) or []
        if str(contract).strip()
    }


def is_chat_tool_attempt(attempt: Any) -> bool:
    return str(getattr(attempt, "event_family", "")).strip() in _CHAT_TOOL_FAMILIES


def is_harness_attempt(attempt: Any) -> bool:
    if "automation_trace" in attempt_contracts(attempt):
        return True
    return any(
        str(getattr(attempt, attr_name, "")).strip().startswith("harness:")
        for attr_name in ("executor_action", "backfill_executor_action")
    )


def attempt_has_runtime_evidence(attempt: Any) -> bool:
    status = str(getattr(attempt, "status", "")).strip()
    attempted_passes = [
        str(pass_id).strip()
        for pass_id in getattr(attempt, "attempted_passes", []) or []
        if str(pass_id).strip()
    ]
    # ``activation_seen`` and ``target_log_seen`` are intermediate observation
    # states emitted by ``reconcile_event_attempts`` when the target extension
    # activated but full verification did not close. Both are strictly
    # stronger than ``attempted_only`` so they count as runtime evidence.
    return bool(
        attempted_passes
        or status
        in {
            "attempted_only",
            "activation_seen",
            "target_log_seen",
            "verified",
            "failed",
        }
    )


def attempt_related_scenarios(attempt: Any) -> list[str]:
    names: list[str] = []
    for raw_name in getattr(attempt, "legacy_scenarios", []) or []:
        name = str(raw_name).strip()
        if name and name not in names:
            names.append(name)
    for attr_name in ("executor_action", "backfill_executor_action"):
        action = str(getattr(attempt, attr_name, "")).strip()
        if not action.startswith("scenario:"):
            continue
        scenario_name = action.split(":", maxsplit=1)[1].strip()
        if scenario_name and scenario_name not in names:
            names.append(scenario_name)
    return names


def covered_scenarios_from_attempts(report: Any) -> list[str]:
    covered: list[str] = []
    for attempt in getattr(report, "event_attempts", []) or []:
        if not attempt_has_runtime_evidence(attempt):
            continue
        for scenario_name in attempt_related_scenarios(attempt):
            if scenario_name and scenario_name not in covered:
                covered.append(scenario_name)
    return covered


def official_unresolved_chat_tool_attempts(report: Any) -> list[Any]:
    return [
        attempt
        for attempt in getattr(report, "event_attempts", [])
        if getattr(attempt, "track", "") == "official"
        and is_chat_tool_attempt(attempt)
        and getattr(attempt, "status", "") != "verified"
        and (
            getattr(attempt, "status", "") in {"failed", "blocked"}
            or not is_harness_attempt(attempt)
        )
    ]
