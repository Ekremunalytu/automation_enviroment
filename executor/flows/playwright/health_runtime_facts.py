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


def official_unresolved_chat_tool_attempts(report: Any) -> list[Any]:
    return [
        attempt
        for attempt in getattr(report, "event_attempts", [])
        if getattr(attempt, "track", "") == "official"
        and is_chat_tool_attempt(attempt)
        and getattr(attempt, "status", "") != "verified"
    ]
