"""Layered stimulus-plan execution helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import automation
import commands
import editor
import terminal

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

_HARNESS_CONTEXT_DIR = Path("/workspace/.extrace-harness")
_HARNESS_CONTEXT_PATH = _HARNESS_CONTEXT_DIR / "context.json"
_TASKS_PATH = Path("/workspace/.vscode/tasks.json")
_LAUNCH_PATH = Path("/workspace/.vscode/launch.json")


@dataclass
class StimulusExecutionResult:
    """Execution result for a layered stimulus plan."""

    executed_scenarios: list[str] = field(default_factory=list)
    failed_scenarios: list[str] = field(default_factory=list)
    extra_trigger_failures: list[str] = field(default_factory=list)


def run_stimulus_plan(
    page: Page,
    payload: Any,
    *,
    monitor: Any | None = None,
) -> StimulusExecutionResult:
    """Execute the compiled layered plan pass-by-pass."""

    result = StimulusExecutionResult()
    attempts_by_id = {
        str(attempt.get("attempt_id", "")): attempt
        for attempt in getattr(payload, "event_attempts", []) or []
        if isinstance(attempt, dict) and str(attempt.get("attempt_id", "")).strip()
    }

    for pass_data in getattr(payload, "stimulus_passes", []) or []:
        if not isinstance(pass_data, dict):
            continue
        stage_id = str(pass_data.get("pass_id", "")).strip()
        if not stage_id:
            continue
        label = str(pass_data.get("label", stage_id))
        order = int(pass_data.get("order", 0) or 0)
        if monitor is not None:
            monitor.record_stimulus_pass_event(
                "start",
                stage_id,
                label=label,
                order=order,
                trigger_method="layered_deep",
            )

        pass_failed = False
        for prerequisite in _prerequisites_for_pass(pass_data, payload):
            _materialize_prerequisite(prerequisite, monitor=monitor)

        if stage_id == "post_run_verification":
            if monitor is not None:
                monitor.record_stimulus_pass_event(
                    "end",
                    stage_id,
                    label=label,
                    order=order,
                    trigger_method="layered_deep",
                    status="completed",
                )
            continue

        for attempt_id in pass_data.get("attempt_ids", []):
            attempt = attempts_by_id.get(str(attempt_id))
            if attempt is None:
                continue
            action = _action_for_pass(stage_id, attempt)
            trigger_method = _method_for_pass(stage_id, attempt)
            if monitor is not None:
                monitor.record_event_attempt_start(
                    attempt["attempt_id"], pass_name=stage_id
                )
            try:
                _execute_attempt(
                    page,
                    payload,
                    attempt,
                    action=action,
                    trigger_method=trigger_method,
                    result=result,
                )
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="attempted_only",
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                    )
            except (OSError, PlaywrightError, RuntimeError, ValueError) as exc:
                pass_failed = True
                result.extra_trigger_failures.append(
                    f"{attempt['attempt_id']}:{action}"
                )
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="failed",
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                        result_details=str(exc),
                        failure_reason_code="stimulus_execution_failed",
                    )
        if monitor is not None:
            monitor.record_stimulus_pass_event(
                "end",
                stage_id,
                label=label,
                order=order,
                trigger_method="layered_deep",
                status="failed" if pass_failed else "completed",
            )

    return result


def _execute_attempt(
    page: Page,
    payload: Any,
    attempt: dict[str, Any],
    *,
    action: str,
    trigger_method: str,
    result: StimulusExecutionResult,
) -> None:
    if action.startswith("scenario:"):
        scenario_name = action.split(":", maxsplit=1)[1]
        automation.run_scenario(page, scenario_name)
        result.executed_scenarios.append(scenario_name)
        return
    if action == "command:auto":
        command_text = _resolve_command_text(payload, attempt)
        if command_text:
            commands.run_command(page, command_text)
            page.wait_for_timeout(1200)
            return
        automation.run_scenario(page, "coding_session")
        result.executed_scenarios.append("coding_session")
        return
    if action.startswith("command:"):
        commands.run_command(page, action.split(":", maxsplit=1)[1])
        page.wait_for_timeout(1200)
        return
    if action == "extra:task_trigger":
        commands.run_command(page, "Tasks: Run Task")
        page.wait_for_timeout(1500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        return
    if action == "extra:walkthrough":
        commands.run_command(page, "Welcome: Open Walkthrough")
        page.wait_for_timeout(2000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        return
    if action == "extra:uri_trigger":
        uri = str(getattr(payload, "uri_trigger", "")).strip()
        if not uri:
            raise ValueError("URI trigger requested without a target URI")
        terminal.new_terminal(page)
        page.wait_for_timeout(500)
        terminal.type_in_terminal(page, f"xdg-open '{uri}'")
        page.wait_for_timeout(1500)
        return
    if action == "extra:custom_editor":
        for filename in getattr(payload, "extra_custom_editor_files", []) or []:
            editor.open_file_by_name(page, str(filename))
            page.wait_for_timeout(1200)
            editor.close_active_editor(page)
            page.wait_for_timeout(300)
        return
    if action.startswith("fixture:"):
        page.wait_for_timeout(1000)
        return
    if action.startswith("harness:"):
        _write_harness_context(payload, attempt, trigger_method=trigger_method)
        commands.run_command(page, "ExTrace Harness: Run Current Stimulus")
        page.wait_for_timeout(1500)
        return
    raise ValueError(f"Unsupported stimulus action: {action}")


def _action_for_pass(pass_id: str, attempt: dict[str, Any]) -> str:
    if (
        pass_id == str(attempt.get("backfill_pass_name", ""))
        and str(attempt.get("backfill_executor_action", "")).strip()
    ):
        return str(attempt.get("backfill_executor_action", ""))
    return str(attempt.get("executor_action", ""))


def _method_for_pass(pass_id: str, attempt: dict[str, Any]) -> str:
    if (
        pass_id == str(attempt.get("backfill_pass_name", ""))
        and str(attempt.get("fallback_trigger_method", "")).strip()
    ):
        return str(attempt.get("fallback_trigger_method", ""))
    return str(attempt.get("trigger_method", ""))


def _prerequisites_for_pass(
    pass_data: dict[str, Any], payload: Any
) -> list[dict[str, Any]]:
    lookup = {
        str(item.get("prerequisite_id", "")): item
        for item in getattr(payload, "prerequisite_results", []) or []
        if isinstance(item, dict)
    }
    by_key = {
        str(item.get("key", "")): item
        for item in getattr(payload, "prerequisite_results", []) or []
        if isinstance(item, dict)
    }
    items: list[dict[str, Any]] = []
    for raw_key in pass_data.get("prerequisite_keys", []):
        key = str(raw_key).strip()
        if not key:
            continue
        if key in lookup:
            items.append(lookup[key])
            continue
        if key in by_key:
            items.append(by_key[key])
    return items


def _materialize_prerequisite(
    prerequisite: dict[str, Any],
    *,
    monitor: Any | None,
) -> None:
    prerequisite_id = str(
        prerequisite.get("prerequisite_id", "") or prerequisite.get("key", "")
    )
    key = str(prerequisite.get("key", ""))
    if key == "task_definition_target":
        _TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _TASKS_PATH.exists():
            _TASKS_PATH.write_text(
                json.dumps(
                    {
                        "version": "2.0.0",
                        "tasks": [
                            {
                                "label": "ExTrace Harness Task",
                                "type": "shell",
                                "command": "echo extrace",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
    elif key == "debug_launch_config":
        _LAUNCH_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _LAUNCH_PATH.exists():
            _LAUNCH_PATH.write_text(
                json.dumps(
                    {
                        "version": "0.2.0",
                        "configurations": [
                            {
                                "name": "ExTrace Python",
                                "type": "python",
                                "request": "launch",
                                "program": "${workspaceFolder}/src/app.py",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
    if monitor is not None:
        monitor.record_prerequisite_result(
            prerequisite_id,
            status="completed",
            detail=str(prerequisite.get("detail", "")),
        )


def _resolve_command_text(payload: Any, attempt: dict[str, Any]) -> str:
    command_id = str(attempt.get("event_value", "")).strip()
    activation_event = str(attempt.get("activation_event", "")).strip()
    if not command_id and activation_event.startswith("onCommand:"):
        command_id = activation_event.split(":", maxsplit=1)[1].strip()

    command_targets = getattr(payload, "command_targets", {}) or {}
    if isinstance(command_targets, dict) and command_id:
        command_text = str(command_targets.get(command_id, "")).strip()
        if command_text:
            return command_text

    if command_id:
        return command_id

    titles = list(getattr(payload, "extra_commands", []) or [])
    if titles:
        return str(titles[0])

    return ""


def _write_harness_context(
    payload: Any,
    attempt: dict[str, Any],
    *,
    trigger_method: str,
) -> None:
    _HARNESS_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "attempt": attempt,
        "trigger_method": trigger_method,
        "command_targets": dict(getattr(payload, "command_targets", {}) or {}),
        "view_targets": dict(getattr(payload, "view_targets", {}) or {}),
        "auth_provider_ids": list(getattr(payload, "auth_provider_ids", []) or []),
        "webview_view_ids": list(getattr(payload, "webview_view_ids", []) or []),
        "uri_trigger": getattr(payload, "uri_trigger", None),
        "run_task_trigger": bool(getattr(payload, "run_task_trigger", False)),
        "run_walkthrough_trigger": bool(
            getattr(payload, "run_walkthrough_trigger", False)
        ),
    }
    _HARNESS_CONTEXT_PATH.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
