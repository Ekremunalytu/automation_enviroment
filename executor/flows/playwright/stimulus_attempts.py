"""Attempt execution helpers for layered stimulus plans."""

from __future__ import annotations

from typing import Any

import automation
import commands
import debug
import editor
import terminal
from stimulus_materializers import resolve_command_text, write_harness_context
from wait_helpers import (
    require_wait,
    wait_for_command_effect,
    wait_for_editor_ready,
    wait_for_trigger_effect,
    wait_for_ui_settle,
)

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def execute_attempt(
    page: Page,
    payload: Any,
    attempt: dict[str, Any],
    *,
    action: str,
    trigger_method: str,
    result: Any,
    monitor: Any | None,
) -> None:
    recorder = getattr(monitor, "record_automation_event", None)
    event_recorder = recorder if callable(recorder) else None
    if action.startswith("scenario:"):
        run_layered_scenario(
            page,
            action.split(":", maxsplit=1)[1],
            attempt=attempt,
            result=result,
            monitor=monitor,
        )
        return
    if action == "command:auto":
        command_text = resolve_command_text(payload, attempt)
        if command_text:
            commands.run_command(page, command_text)
            require_wait(
                wait_for_command_effect(
                    page,
                    event_recorder=event_recorder,
                    activation_event=str(attempt.get("activation_event", "")),
                )
            )
        else:
            run_layered_scenario(
                page,
                "coding_session",
                attempt=attempt,
                result=result,
                monitor=monitor,
            )
        return
    if action.startswith("command:"):
        commands.run_command(page, action.split(":", maxsplit=1)[1])
        require_wait(
            wait_for_command_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        return
    if action == "extra:task_trigger":
        commands.run_command(page, "Tasks: Run Task")
        require_wait(
            wait_for_trigger_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        page.keyboard.press("Escape")
        require_wait(
            wait_for_ui_settle(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        return
    if action == "extra:debug_lifecycle":
        run_debug_event_attempt(
            page,
            event_recorder=event_recorder,
            activation_event=str(attempt.get("activation_event", "")),
        )
        return
    if action == "extra:walkthrough":
        commands.run_command(page, "Welcome: Open Walkthrough")
        require_wait(
            wait_for_trigger_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        page.keyboard.press("Escape")
        require_wait(
            wait_for_ui_settle(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        return
    if action == "extra:uri_trigger":
        uri = str(getattr(payload, "uri_trigger", "")).strip()
        if not uri:
            raise ValueError("URI trigger requested without a target URI")
        terminal.new_terminal(page)
        require_wait(
            wait_for_ui_settle(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        terminal.type_in_terminal(page, f"xdg-open '{uri}'")
        require_wait(
            wait_for_trigger_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        return
    if action == "extra:custom_editor":
        for filename in getattr(payload, "extra_custom_editor_files", []) or []:
            editor.open_file_by_name(page, str(filename))
            require_wait(
                wait_for_trigger_effect(
                    page,
                    event_recorder=event_recorder,
                    activation_event=str(attempt.get("activation_event", "")),
                )
            )
            editor.close_active_editor(page)
            require_wait(
                wait_for_ui_settle(
                    page,
                    event_recorder=event_recorder,
                    activation_event=str(attempt.get("activation_event", "")),
                )
            )
        return
    if action.startswith("fixture:"):
        require_wait(
            wait_for_trigger_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        return
    if action.startswith("harness:"):
        write_harness_context(payload, attempt, trigger_method=trigger_method)
        commands.run_command(page, "ExTrace Harness: Run Current Stimulus")
        require_wait(
            wait_for_trigger_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        return
    raise ValueError(f"Unsupported stimulus action: {action}")


def run_layered_scenario(
    page: Page,
    scenario_name: str,
    *,
    attempt: dict[str, Any],
    result: Any,
    monitor: Any | None,
) -> None:
    language_id = (
        resolve_language_id(attempt) if scenario_name == "coding_session" else ""
    )
    emits_through_automation = not (scenario_name == "coding_session" and language_id)
    should_report_directly = monitor is not None and (
        not emits_through_automation
        or getattr(automation, "_SCENARIO_EVENT_REPORTER", None) is None
    )

    if should_report_directly and monitor is not None:
        monitor.record_scenario_event(
            "start", scenario_name, "", scenario_metadata_for_reporting(scenario_name)
        )
    result.executed_scenarios.append(scenario_name)
    try:
        if scenario_name == "coding_session" and language_id:
            automation.scenario_coding_session(page, language=language_id)
        else:
            automation.run_scenario(page, scenario_name)
    except (PlaywrightError, RuntimeError, ValueError) as exc:
        _append_unique(result.failed_scenarios, scenario_name)
        if should_report_directly and monitor is not None:
            monitor.record_scenario_event(
                "end",
                scenario_name,
                "failed",
                scenario_metadata_for_reporting(scenario_name, error=str(exc)),
            )
        raise
    if should_report_directly and monitor is not None:
        monitor.record_scenario_event(
            "end",
            scenario_name,
            "completed",
            scenario_metadata_for_reporting(scenario_name),
        )


def scenario_metadata_for_reporting(
    scenario_name: str,
    *,
    error: str = "",
) -> dict[str, Any]:
    metadata = next(
        (
            dict(item)
            for item in automation.get_scenario_registry()
            if str(item.get("name", "")).strip() == scenario_name
        ),
        {"name": scenario_name},
    )
    if error:
        metadata["error"] = error
    return metadata


def dedupe_execution_key(pass_id: str, attempt: dict[str, Any], action: str) -> str:
    if action == "extra:debug_lifecycle":
        return f"{pass_id}:{action}"
    if not action.startswith("scenario:"):
        return ""
    scenario_name = action.split(":", maxsplit=1)[1]
    if scenario_name == "coding_session":
        language_id = resolve_language_id(attempt) or "default"
        return f"{pass_id}:{action}:{language_id}"
    return f"{pass_id}:{action}"


def deduped_result_details(pass_id: str, action: str, prior_execution: Any) -> str:
    prefix = (
        f"Reused prior {action} result from the {pass_id} pass instead of "
        "re-running the same stimulus."
    )
    return (
        f"{prefix} Original result: {prior_execution.result_details}"
        if prior_execution.result_details
        else prefix
    )


def run_debug_event_attempt(
    page: Page,
    *,
    event_recorder=None,
    activation_event: str = "",
) -> None:
    """Drive a minimal debug lifecycle without command-palette breakpoint setup."""
    editor.open_file_by_name(page, "src/app.py")
    require_wait(
        wait_for_editor_ready(
            page,
            event_recorder=event_recorder,
            activation_event=activation_event,
        )
    )
    page.keyboard.press("Control+Home")
    require_wait(
        wait_for_ui_settle(
            page,
            event_recorder=event_recorder,
            activation_event=activation_event,
        )
    )
    page.keyboard.press("Escape")
    debug.start_debug(page)
    require_wait(
        wait_for_trigger_effect(
            page,
            event_recorder=event_recorder,
            activation_event=activation_event,
        )
    )
    editor._dismiss_notification(page)
    debug.stop_debug(page)
    require_wait(
        wait_for_ui_settle(
            page,
            event_recorder=event_recorder,
            activation_event=activation_event,
        )
    )
    editor._dismiss_notification(page)
    page.keyboard.press("Escape")


def failure_reason_code_for_exception(exc: BaseException) -> str:
    return str(getattr(exc, "reason_code", "")).strip() or "stimulus_execution_failed"


def action_for_pass(pass_id: str, attempt: dict[str, Any]) -> str:
    if (
        pass_id == str(attempt.get("backfill_pass_name", ""))
        and str(attempt.get("backfill_executor_action", "")).strip()
    ):
        return str(attempt.get("backfill_executor_action", ""))
    return str(attempt.get("executor_action", ""))


def method_for_pass(pass_id: str, attempt: dict[str, Any]) -> str:
    if (
        pass_id == str(attempt.get("backfill_pass_name", ""))
        and str(attempt.get("fallback_trigger_method", "")).strip()
    ):
        return str(attempt.get("fallback_trigger_method", ""))
    return str(attempt.get("trigger_method", ""))


def resolve_language_id(attempt: dict[str, Any]) -> str:
    if str(attempt.get("event_family", "")).strip() != "onLanguage":
        return ""
    event_value = str(attempt.get("event_value", "")).strip()
    if event_value:
        return event_value
    activation_event = str(attempt.get("activation_event", "")).strip()
    return (
        activation_event.split(":", maxsplit=1)[1].strip()
        if ":" in activation_event
        else ""
    )
