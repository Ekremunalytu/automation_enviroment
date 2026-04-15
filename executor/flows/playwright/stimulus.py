"""Layered stimulus-plan execution helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import automation
import commands
import debug
import editor
import terminal
import workspace

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


@dataclass
class PrerequisiteMaterialization:
    status: str
    detail: str = ""
    reason_code: str = ""
    resolved_targets: dict[str, Any] = field(default_factory=dict)


@dataclass
class AttemptExecutionRecord:
    status: str
    result_details: str = ""
    failure_reason_code: str = ""


def run_stimulus_plan(
    page: Page,
    payload: Any,
    *,
    monitor: Any | None = None,
) -> StimulusExecutionResult:
    """Execute the compiled layered plan pass-by-pass."""

    result = StimulusExecutionResult()
    attempts_by_id = {
        attempt_id: attempt
        for raw_attempt in getattr(payload, "event_attempts", []) or []
        for attempt in [_trigger_item_as_dict(raw_attempt)]
        if attempt is not None
        for attempt_id in [str(attempt.get("attempt_id", "")).strip()]
        if attempt_id
    }

    for raw_pass_data in getattr(payload, "stimulus_passes", []) or []:
        pass_data = _trigger_item_as_dict(raw_pass_data)
        if pass_data is None:
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
        blocked_attempts: dict[str, tuple[str, str]] = {}
        execution_records: dict[str, AttemptExecutionRecord] = {}
        for prerequisite in _prerequisites_for_pass(pass_data, payload):
            result_data = _materialize_prerequisite(
                prerequisite,
                payload=payload,
                attempts_by_id=attempts_by_id,
                monitor=monitor,
            )
            if result_data.status != "completed":
                for attempt_id in prerequisite.get("attempt_ids", []) or []:
                    blocked_attempts[str(attempt_id)] = (
                        result_data.reason_code or "prerequisite_blocked",
                        result_data.detail,
                    )

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
            blocked_reason = blocked_attempts.get(str(attempt_id))
            if blocked_reason is not None:
                pass_failed = True
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="blocked",
                        blocked_reason_code=blocked_reason[0],
                        result_details=blocked_reason[1],
                    )
                continue
            action = _action_for_pass(stage_id, attempt)
            trigger_method = _method_for_pass(stage_id, attempt)
            if monitor is not None:
                monitor.record_event_attempt_start(
                    attempt["attempt_id"], pass_name=stage_id
                )
            execution_key = _dedupe_execution_key(stage_id, attempt, action)
            prior_execution = (
                execution_records.get(execution_key) if execution_key else None
            )
            if prior_execution is not None:
                if prior_execution.status == "failed":
                    pass_failed = True
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status=prior_execution.status,
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                        result_details=_deduped_result_details(
                            stage_id,
                            action,
                            prior_execution,
                        ),
                        failure_reason_code=prior_execution.failure_reason_code,
                    )
                continue
            try:
                _execute_attempt(
                    page,
                    payload,
                    attempt,
                    action=action,
                    trigger_method=trigger_method,
                    result=result,
                    monitor=monitor,
                )
                if execution_key:
                    execution_records[execution_key] = AttemptExecutionRecord(
                        status="attempted_only"
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
                failure_reason_code = _failure_reason_code_for_exception(exc)
                if execution_key:
                    execution_records[execution_key] = AttemptExecutionRecord(
                        status="failed",
                        result_details=str(exc),
                        failure_reason_code=failure_reason_code,
                    )
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="failed",
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                        result_details=str(exc),
                        failure_reason_code=failure_reason_code,
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
    monitor: Any | None,
) -> None:
    if action.startswith("scenario:"):
        scenario_name = action.split(":", maxsplit=1)[1]
        _run_layered_scenario(
            page,
            scenario_name,
            attempt=attempt,
            result=result,
            monitor=monitor,
        )
        return
    if action == "command:auto":
        command_text = _resolve_command_text(payload, attempt)
        if command_text:
            commands.run_command(page, command_text)
            page.wait_for_timeout(1200)
            return
        _run_layered_scenario(
            page,
            "coding_session",
            attempt=attempt,
            result=result,
            monitor=monitor,
        )
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
    if action == "extra:debug_lifecycle":
        _run_debug_event_attempt(page)
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


def _run_layered_scenario(
    page: Page,
    scenario_name: str,
    *,
    attempt: dict[str, Any],
    result: StimulusExecutionResult,
    monitor: Any | None,
) -> None:
    language_id = (
        _resolve_language_id(attempt) if scenario_name == "coding_session" else ""
    )
    emits_through_automation = not (scenario_name == "coding_session" and language_id)
    should_report_directly = monitor is not None and (
        not emits_through_automation
        or getattr(automation, "_SCENARIO_EVENT_REPORTER", None) is None
    )

    if should_report_directly and monitor is not None:
        monitor.record_scenario_event(
            "start",
            scenario_name,
            "",
            _scenario_metadata_for_reporting(scenario_name),
        )

    try:
        if scenario_name == "coding_session" and language_id:
            automation.scenario_coding_session(page, language=language_id)
        else:
            automation.run_scenario(page, scenario_name)
    except (PlaywrightError, RuntimeError, ValueError) as exc:
        if scenario_name not in result.failed_scenarios:
            result.failed_scenarios.append(scenario_name)
        if should_report_directly and monitor is not None:
            monitor.record_scenario_event(
                "end",
                scenario_name,
                "failed",
                _scenario_metadata_for_reporting(scenario_name, error=str(exc)),
            )
        raise

    result.executed_scenarios.append(scenario_name)
    if should_report_directly and monitor is not None:
        monitor.record_scenario_event(
            "end",
            scenario_name,
            "completed",
            _scenario_metadata_for_reporting(scenario_name),
        )


def _scenario_metadata_for_reporting(
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


def _dedupe_execution_key(
    pass_id: str,
    attempt: dict[str, Any],
    action: str,
) -> str:
    if action == "extra:debug_lifecycle":
        return f"{pass_id}:{action}"
    if not action.startswith("scenario:"):
        return ""

    scenario_name = action.split(":", maxsplit=1)[1]
    if scenario_name == "coding_session":
        language_id = _resolve_language_id(attempt) or "default"
        return f"{pass_id}:{action}:{language_id}"
    return f"{pass_id}:{action}"


def _deduped_result_details(
    pass_id: str,
    action: str,
    prior_execution: AttemptExecutionRecord,
) -> str:
    prefix = (
        f"Reused prior {action} result from the {pass_id} pass instead of "
        "re-running the same stimulus."
    )
    if prior_execution.result_details:
        return f"{prefix} Original result: {prior_execution.result_details}"
    return prefix


def _run_debug_event_attempt(page: Page) -> None:
    """Drive a minimal debug lifecycle without command-palette breakpoint setup."""
    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(800)
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(150)
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    debug.start_debug(page)
    page.wait_for_timeout(2000)
    editor._dismiss_notification(page)
    page.wait_for_timeout(250)
    debug.stop_debug(page)
    page.wait_for_timeout(300)
    editor._dismiss_notification(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)


def _failure_reason_code_for_exception(exc: BaseException) -> str:
    reason_code = str(getattr(exc, "reason_code", "")).strip()
    if reason_code:
        return reason_code
    return "stimulus_execution_failed"


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
        for item in [_trigger_item_as_dict(item)]
        if item is not None
    }
    by_key = {
        str(item.get("key", "")): item
        for item in getattr(payload, "prerequisite_results", []) or []
        for item in [_trigger_item_as_dict(item)]
        if item is not None
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
    payload: Any,
    attempts_by_id: dict[str, dict[str, Any]],
    monitor: Any | None,
) -> PrerequisiteMaterialization:
    prerequisite_id = str(
        prerequisite.get("prerequisite_id", "") or prerequisite.get("key", "")
    )
    key = str(prerequisite.get("key", ""))
    attempts = [
        attempt
        for attempt_id in prerequisite.get("attempt_ids", []) or []
        for attempt in [attempts_by_id.get(str(attempt_id))]
        if attempt is not None
    ]
    result = _resolve_prerequisite_materialization(
        key,
        payload=payload,
        attempts=attempts,
        detail=str(prerequisite.get("detail", "")),
    )
    if monitor is not None:
        monitor.record_prerequisite_result(
            prerequisite_id,
            status=result.status,
            detail=result.detail,
            reason_code=result.reason_code,
            resolved_targets=result.resolved_targets,
        )
    return result


def _trigger_item_as_dict(item: Any) -> dict[str, Any] | None:
    if isinstance(item, Mapping):
        return dict(item)

    model_dump = getattr(item, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, dict):
            return dumped

    dict_method = getattr(item, "dict", None)
    if callable(dict_method):
        dumped = dict_method()
        if isinstance(dumped, dict):
            return dumped

    return None


def _resolve_prerequisite_materialization(
    key: str,
    *,
    payload: Any,
    attempts: list[dict[str, Any]],
    detail: str,
) -> PrerequisiteMaterialization:
    if key == "task_definition_target":
        return _materialize_task_definition()
    if key == "debug_launch_config":
        return _materialize_debug_launch_config()
    if key == "workspace_contains_fixture":
        return _materialize_workspace_contains_fixture(attempts)
    if key == "language_fixture":
        return _materialize_language_fixture(attempts)
    if key == "command_target":
        return _materialize_command_target(payload, attempts)
    if key == "auth_request_target":
        providers = sorted(
            {
                str(provider_id).strip()
                for provider_id in getattr(payload, "auth_provider_ids", []) or []
                if str(provider_id).strip()
            }
        )
        if not providers:
            return _blocked(
                "missing_auth_request_target",
                "Authentication request target was not available in the trigger payload.",
            )
        return _completed(
            f"Resolved auth providers: {', '.join(providers)}",
            {"auth_provider_ids": providers},
        )
    if key == "language_model_tool_target":
        tool_id = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        if not tool_id:
            return _blocked(
                "missing_language_model_tool_target",
                "Language-model tool id was missing from the trigger payload.",
            )
        return _completed(
            f"Resolved language-model tool target {tool_id}.",
            {"language_model_tool_id": tool_id},
        )
    if key == "chat_participant_target":
        participant_id = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        if not participant_id:
            return _blocked(
                "missing_chat_participant_target",
                "Chat participant id was missing from the trigger payload.",
            )
        return _completed(
            f"Resolved chat participant {participant_id}.",
            {"chat_participant_id": participant_id},
        )
    if key == "terminal_shell_target":
        shell = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "bash",
        )
        return _completed(
            f"Using terminal shell target {shell}.",
            {"terminal_shell": shell},
        )
    if key == "terminal_profile_target":
        profile_id = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        if not profile_id:
            return _blocked(
                "missing_terminal_profile_target",
                "Terminal profile id was missing from the trigger payload.",
            )
        return _completed(
            f"Resolved terminal profile {profile_id}.",
            {"terminal_profile": profile_id},
        )
    if key == "view_target":
        view_id = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        view_targets = getattr(payload, "view_targets", {}) or {}
        if (
            not view_id
            or not isinstance(view_targets, dict)
            or view_id not in view_targets
        ):
            return _blocked(
                "missing_view_target",
                "Contributed view target metadata was unavailable for this attempt.",
                {"view_id": view_id},
            )
        return _completed(
            f"Resolved view target {view_id}.",
            {"view_id": view_id, "view_target": dict(view_targets.get(view_id, {}))},
        )
    if key == "webview_target":
        view_id = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        webview_ids = [
            str(item).strip()
            for item in getattr(payload, "webview_view_ids", []) or []
            if str(item).strip()
        ]
        resolved_id = view_id or (webview_ids[0] if webview_ids else "")
        if not resolved_id:
            return _blocked(
                "missing_webview_target",
                "Webview target metadata was unavailable for this attempt.",
            )
        return _completed(
            f"Resolved webview target {resolved_id}.",
            {"webview_view_id": resolved_id},
        )
    if key == "uri_target":
        uri = str(getattr(payload, "uri_trigger", "") or "").strip()
        if not uri:
            return _blocked(
                "missing_uri_target",
                "Target vscode URI was unavailable for this attempt.",
            )
        return _completed(f"Resolved URI target {uri}.", {"uri_trigger": uri})
    if key == "loopback_uri_target":
        uri = (
            str(getattr(payload, "uri_trigger", "") or "").strip()
            or "http://127.0.0.1/extrace"
        )
        return _completed(f"Resolved loopback URI target {uri}.", {"uri_trigger": uri})
    if key == "walkthrough_target":
        walkthrough_id = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        if not walkthrough_id and getattr(payload, "run_walkthrough_trigger", False):
            walkthrough_id = "walkthrough"
        if not walkthrough_id:
            return _blocked(
                "missing_walkthrough_target",
                "Walkthrough target metadata was unavailable for this attempt.",
            )
        return _completed(
            f"Resolved walkthrough target {walkthrough_id}.",
            {"walkthrough_id": walkthrough_id},
        )
    if key == "custom_editor_bait_files":
        filenames = [
            str(item).strip()
            for item in getattr(payload, "extra_custom_editor_files", []) or []
            if str(item).strip()
        ]
        if not filenames:
            return _blocked(
                "missing_custom_editor_bait_files",
                "Custom editor bait files were missing from the trigger payload.",
            )
        created = [str(path) for path in workspace.create_bait_files(filenames)]
        return _completed(
            f"Created custom editor bait files: {', '.join(created)}",
            {"bait_files": created},
        )
    if key == "notebook_fixture":
        notebook_files = [
            str(item).strip()
            for item in getattr(payload, "extra_notebook_files", []) or []
            if str(item).strip()
        ] or ["notebooks/analysis.ipynb"]
        created = [
            str(
                workspace.create_workspace_file(
                    notebook_file,
                    '{\n  "cells": [],\n  "metadata": {},\n  "nbformat": 4,\n  "nbformat_minor": 5\n}\n',
                )
            )
            for notebook_file in notebook_files
        ]
        return _completed(
            f"Prepared notebook fixture(s): {', '.join(created)}",
            {"notebook_files": created},
        )
    if key == "renderer_fixture":
        notebook_result = _resolve_prerequisite_materialization(
            "notebook_fixture",
            payload=payload,
            attempts=attempts,
            detail=detail,
        )
        if notebook_result.status != "completed":
            return notebook_result
        rendered = str(
            workspace.create_workspace_file(
                "notebooks/renderer-output.txt", "renderer output\n"
            )
        )
        return _completed(
            f"Prepared renderer fixture {rendered}.",
            {
                **notebook_result.resolved_targets,
                "renderer_output": rendered,
            },
        )
    if key == "searchable_workspace":
        created = [
            str(workspace.create_workspace_file("README.md", "# ExTrace\n")),
            str(workspace.create_workspace_file("src/app.py", "print('extrace')\n")),
        ]
        return _completed(
            f"Prepared searchable workspace fixture(s): {', '.join(created)}",
            {"paths": created},
        )
    if key == "filesystem_scheme_target":
        scheme = next(
            (
                value
                for value in (_resolve_event_value(attempt) for attempt in attempts)
                if value
            ),
            "",
        )
        if not scheme:
            return _blocked(
                "missing_filesystem_scheme_target",
                "Filesystem scheme target was unavailable for this attempt.",
            )
        return _completed(
            f"Resolved filesystem scheme {scheme}.", {"filesystem_scheme": scheme}
        )
    if key == "edit_session_fixture":
        return _blocked(
            "missing_edit_session_target",
            "Edit session stimulus requires harness metadata that was not provided.",
        )
    if key == "workspace_ready":
        return _completed(detail or "Workbench readiness prerequisite acknowledged.")
    return _completed(detail or f"Prerequisite {key} was acknowledged.")


def _materialize_task_definition() -> PrerequisiteMaterialization:
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
    return _completed(
        f"Ensured task definition at {_TASKS_PATH}.",
        {"task_definition": str(_TASKS_PATH)},
    )


def _materialize_debug_launch_config() -> PrerequisiteMaterialization:
    workspace.create_workspace_file("src/app.py", "print('debug fixture')\n")
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
    return _completed(
        f"Ensured debug launch config at {_LAUNCH_PATH}.",
        {"debug_launch_config": str(_LAUNCH_PATH)},
    )


def _materialize_workspace_contains_fixture(
    attempts: list[dict[str, Any]],
) -> PrerequisiteMaterialization:
    patterns = sorted(
        {
            _resolve_event_value(attempt)
            for attempt in attempts
            if _resolve_event_value(attempt)
        }
    )
    if not patterns:
        return _blocked(
            "missing_workspace_contains_pattern",
            "workspaceContains prerequisite did not include a filename pattern.",
        )
    created: list[str] = []
    for pattern in patterns:
        created.extend(_create_workspace_contains_fixture(pattern))
    return _completed(
        f"Prepared workspaceContains fixtures for {', '.join(patterns)}.",
        {"patterns": patterns, "paths": created},
    )


def _materialize_language_fixture(
    attempts: list[dict[str, Any]],
) -> PrerequisiteMaterialization:
    languages = sorted(
        {
            language_id
            for attempt in attempts
            for language_id in [_resolve_language_id(attempt)]
            if language_id
        }
    )
    if not languages:
        return _blocked(
            "missing_language_fixture_target",
            "Language fixture target was unavailable for this attempt.",
        )
    created: list[str] = []
    for language_id in languages:
        try:
            created.extend(_ensure_language_fixture(language_id))
        except KeyError:
            return _blocked(
                "unknown_language_fixture",
                f"Language fixture {language_id} is not supported by the workspace seed.",
                {"language_id": language_id},
            )
    return _completed(
        f"Prepared language fixtures for {', '.join(languages)}.",
        {"languages": languages, "paths": created},
    )


def _materialize_command_target(
    payload: Any,
    attempts: list[dict[str, Any]],
) -> PrerequisiteMaterialization:
    for attempt in attempts:
        command_text = _resolve_command_text(payload, attempt)
        if command_text:
            return _completed(
                f"Resolved command target {command_text}.",
                {"command_text": command_text},
            )
    return _blocked(
        "missing_command_target",
        "Command target metadata was unavailable for this attempt.",
    )


def _create_workspace_contains_fixture(pattern: str) -> list[str]:
    normalized = pattern.strip()
    if not normalized:
        return []
    created: list[str] = []

    def create_file(path: str, content: str = "") -> None:
        created.append(str(workspace.create_workspace_file(path, content)))

    def create_dir(path: str) -> None:
        created.append(str(workspace.create_workspace_dir(path)))

    if normalized in {"**/.venv", ".venv"}:
        create_dir(".venv")
        return created
    if normalized in {"**/.conda", ".conda"}:
        create_dir(".conda")
        return created
    fixtures = {
        "Pipfile": '[packages]\nflask = "*"\n',
        "requirements.txt": "flask==3.0.0\n",
        "setup.py": "from setuptools import setup\nsetup(name='extrace')\n",
        "pyproject.toml": '[project]\nname = "extrace"\n',
        "pylock.toml": "[tool.extrace]\nlock = true\n",
        "manage.py": "print('manage')\n",
        "app.py": "print('app fixture')\n",
        "mspythonconfig.json": '{\n  "python.defaultInterpreterPath": "/usr/bin/python3"\n}\n',
    }
    if normalized in fixtures:
        create_file(normalized, fixtures[normalized])
        return created
    if normalized == "**/pylock.*.toml":
        create_file("nested/pylock.dev.toml", '[tool.extrace]\nchannel = "dev"\n')
        return created

    fallback = normalized.replace("**/", "nested/")
    fallback = fallback.lstrip("/")
    fallback = fallback.replace("*", "sample").replace("?", "x")
    if fallback.endswith("/") or Path(fallback).suffix == "":
        create_dir(fallback.rstrip("/"))
    else:
        create_file(fallback, "")
    return created


def _ensure_language_fixture(language_id: str) -> list[str]:
    created: list[str] = []

    def create(path: str, content: str) -> None:
        created.append(str(workspace.create_workspace_file(path, content)))

    language_fixtures = {
        "python": ("src/app.py", "def main():\n    return 'extrace'\n"),
        "javascript": ("frontend/src/api.js", "export const api = () => 'ok';\n"),
        "typescript": (
            "frontend/src/index.ts",
            "export const version: string = '1.0.0';\n",
        ),
        "go": ("services/api/main.go", "package main\n\nfunc main() {}\n"),
        "rust": ("services/worker/src/main.rs", "fn main() {}\n"),
    }
    if language_id in language_fixtures:
        path, content = language_fixtures[language_id]
        create(path, content)
        return created
    created.append(str(workspace.create_language_file(language_id)))
    return created


def _resolve_event_value(attempt: dict[str, Any]) -> str:
    event_value = str(attempt.get("event_value", "")).strip()
    if event_value:
        return event_value
    activation_event = str(attempt.get("activation_event", "")).strip()
    if ":" in activation_event:
        return activation_event.split(":", maxsplit=1)[1].strip()
    return ""


def _resolve_language_id(attempt: dict[str, Any]) -> str:
    if str(attempt.get("event_family", "")).strip() != "onLanguage":
        return ""
    return _resolve_event_value(attempt)


def _completed(
    detail: str,
    resolved_targets: dict[str, Any] | None = None,
) -> PrerequisiteMaterialization:
    return PrerequisiteMaterialization(
        status="completed",
        detail=detail,
        resolved_targets=dict(resolved_targets or {}),
    )


def _blocked(
    reason_code: str,
    detail: str,
    resolved_targets: dict[str, Any] | None = None,
) -> PrerequisiteMaterialization:
    return PrerequisiteMaterialization(
        status="blocked",
        detail=detail,
        reason_code=reason_code,
        resolved_targets=dict(resolved_targets or {}),
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
        "attempt_id": str(attempt.get("attempt_id", "")),
        "attempt": attempt,
        "trigger_method": trigger_method,
        "resolved_targets": _resolve_attempt_targets(payload, attempt),
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


def _resolve_attempt_targets(payload: Any, attempt: dict[str, Any]) -> dict[str, Any]:
    event_value = _resolve_event_value(attempt)
    view_targets = getattr(payload, "view_targets", {}) or {}
    resolved: dict[str, Any] = {
        "event_value": event_value,
        "command_text": _resolve_command_text(payload, attempt),
        "view_target": dict(view_targets.get(event_value, {}))
        if isinstance(view_targets, dict) and event_value in view_targets
        else {},
        "uri_trigger": getattr(payload, "uri_trigger", None),
        "auth_provider_ids": list(getattr(payload, "auth_provider_ids", []) or []),
        "webview_view_ids": list(getattr(payload, "webview_view_ids", []) or []),
    }
    if str(attempt.get("event_family", "")).strip() == "onLanguageModelTool":
        resolved["language_model_tool_id"] = event_value
    if str(attempt.get("event_family", "")).strip() in {
        "onTerminal",
        "onTerminalShellIntegration",
    }:
        resolved["terminal_shell"] = event_value or "bash"
    if str(attempt.get("event_family", "")).strip() == "onTerminalProfile":
        resolved["terminal_profile"] = event_value
    return resolved
