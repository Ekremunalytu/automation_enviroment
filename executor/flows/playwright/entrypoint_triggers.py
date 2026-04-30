"""Trigger-planning helpers for the Playwright executor entrypoint."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import Any

import uri_validation
from playwright.sync_api import Browser, Page
from playwright.sync_api import Error as PlaywrightError
from wait_helpers import (
    require_wait,
    wait_for_command_effect,
    wait_for_target_reaction,
    wait_for_trigger_effect,
    wait_for_ui_settle,
)


def resolve_execution_plan(
    skip_automation: bool,
    scenario: str | None,
    trigger_payload: Any | None,
) -> tuple[str, list[str]]:
    """Resolve executor mode for trigger payloads and explicit scenarios."""
    if skip_automation:
        return "skip_automation", []
    if trigger_payload and trigger_payload.stimulus_passes and not scenario:
        return "layered_passes", list(trigger_payload.selected_scenarios)
    if trigger_payload and trigger_payload.selected_scenarios:
        if scenario:
            return "selected_scenarios", [scenario]
        return "selected_scenarios", list(trigger_payload.selected_scenarios)
    if scenario:
        return "single_scenario", [scenario]
    return "all_scenarios", []


def run_extra_triggers(
    page: Page,
    payload: Any,
    *,
    deps: Any,
    automation_event_recorder: Callable[[str, str, str, str, str], None] | None = None,
    verification_monitor: Any | None = None,
) -> list[str]:
    """Run additional activation triggers beyond the standard scenarios."""
    failed_triggers: list[str] = []

    def emit(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        if automation_event_recorder is not None:
            automation_event_recorder(
                kind,
                message,
                status,
                scenario_name,
                activation_event,
            )

    def dismiss_ui_blocker(context: str, activation_event: str) -> bool:
        blocker_text = deps.editor._dismiss_notification(page)
        if not blocker_text:
            return False
        emit(
            "ui_blocker_detected",
            f"Detected UI blocker during {context}: {blocker_text}",
            "running",
            activation_event=activation_event,
        )
        emit(
            "ui_blocker_dismissed",
            f"Dismissed UI blocker during {context}: {blocker_text}",
            "completed",
            activation_event=activation_event,
        )
        return True

    for filename in payload.extra_custom_editor_files:
        emit(
            "extra_trigger",
            f"Opening custom editor bait file {filename}",
            "running",
            activation_event="onCustomEditor",
        )
        try:
            print(f"[*] Opening custom editor bait file: {filename}")
            deps.editor.open_file_by_name(page, filename)
            require_wait(
                wait_for_trigger_effect(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onCustomEditor",
                )
            )
            deps.editor.close_active_editor(page)
            require_wait(
                wait_for_ui_settle(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onCustomEditor",
                )
            )
            emit(
                "extra_trigger",
                f"Opened custom editor bait file {filename}",
                "completed",
                activation_event="onCustomEditor",
            )
        except (PlaywrightError, RuntimeError) as exc:
            print(f"[!] Custom editor trigger failed for {filename}: {exc}")
            emit(
                "extra_trigger",
                f"Custom editor trigger failed for {filename}: {exc}",
                "failed",
                activation_event="onCustomEditor",
            )
            failed_triggers.append(f"custom_editor:{filename}")

    if payload.uri_trigger:
        emit(
            "extra_trigger",
            f"Triggering URI {payload.uri_trigger}",
            "running",
            activation_event="onUri",
        )
        try:
            uri_validation.validate_uri_scheme(payload.uri_trigger)
            print(f"[*] Triggering URI: {payload.uri_trigger}")
            deps.terminal.new_terminal(page)
            require_wait(
                wait_for_ui_settle(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onUri",
                )
            )
            uri_validation.run_uri_trigger(payload.uri_trigger)
            require_wait(
                wait_for_trigger_effect(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onUri",
                )
            )
            emit(
                "extra_trigger",
                f"Triggered URI {payload.uri_trigger}",
                "completed",
                activation_event="onUri",
            )
        except (
            PlaywrightError,
            RuntimeError,
            uri_validation.UriValidationError,
            subprocess.SubprocessError,
            OSError,
        ) as exc:
            print(f"[!] URI trigger failed: {exc}")
            emit(
                "extra_trigger",
                f"URI trigger failed: {exc}",
                "failed",
                activation_event="onUri",
            )
            failed_triggers.append("uri_trigger")

    if payload.run_task_trigger:
        emit(
            "extra_trigger",
            "Triggering task runner",
            "running",
            activation_event="onTaskType",
        )
        try:
            print("[*] Triggering task runner...")
            deps.commands.run_command(page, "Tasks: Run Task")
            require_wait(
                wait_for_trigger_effect(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onTaskType",
                )
            )
            dismiss_ui_blocker("task trigger", "onTaskType")
            emit(
                "extra_trigger",
                "Triggered task runner",
                "completed",
                activation_event="onTaskType",
            )
        except (PlaywrightError, RuntimeError) as exc:
            print(f"[!] Task trigger failed: {exc}")
            emit(
                "extra_trigger",
                f"Task trigger failed: {exc}",
                "failed",
                activation_event="onTaskType",
            )
            failed_triggers.append("task_trigger")

    if payload.run_walkthrough_trigger:
        emit(
            "extra_trigger",
            "Triggering walkthrough",
            "running",
            activation_event="onWalkthrough",
        )
        try:
            print("[*] Triggering walkthrough...")
            deps.commands.run_command(page, "Welcome: Open Walkthrough")
            require_wait(
                wait_for_trigger_effect(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onWalkthrough",
                )
            )
            deps.editor.close_active_editor(page)
            require_wait(
                wait_for_ui_settle(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onWalkthrough",
                )
            )
            dismiss_ui_blocker("walkthrough trigger", "onWalkthrough")
            emit(
                "extra_trigger",
                "Triggered walkthrough",
                "completed",
                activation_event="onWalkthrough",
            )
        except (PlaywrightError, RuntimeError) as exc:
            print(f"[!] Walkthrough trigger failed: {exc}")
            emit(
                "extra_trigger",
                f"Walkthrough trigger failed: {exc}",
                "failed",
                activation_event="onWalkthrough",
            )
            failed_triggers.append("walkthrough_trigger")

    for command in getattr(payload, "extra_commands", []):
        emit(
            "command",
            f"Running command {command}",
            "running",
            activation_event="onCommand",
        )
        try:
            print(f"[*] Running command: {command}")
            baseline = (
                verification_monitor.capture_runtime_snapshot()
                if verification_monitor is not None
                else {}
            )
            deps.commands.run_command(page, command)
            require_wait(
                wait_for_command_effect(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onCommand",
                )
            )
            dismiss_ui_blocker(f"command {command}", "onCommand")
            success_signal = False
            if verification_monitor is not None:
                target_reaction = wait_for_target_reaction(
                    verification_monitor,
                    baseline,
                    capability="commands",
                    trigger_label=command,
                    activation_event="onCommand",
                    event_recorder=automation_event_recorder,
                )
                success_signal = target_reaction.status == "completed"
            emit(
                "command",
                f"Ran command {command}",
                "completed",
                activation_event="onCommand",
            )
            if verification_monitor is not None and not success_signal:
                failed_triggers.append(f"command:{command}")
        except (PlaywrightError, RuntimeError) as exc:
            print(f"[!] Command trigger failed for {command}: {exc}")
            page.keyboard.press("Escape")
            require_wait(
                wait_for_ui_settle(
                    page,
                    event_recorder=automation_event_recorder,
                    activation_event="onCommand",
                )
            )
            emit(
                "ui_blocker_unresolved",
                f"Command {command} left the UI in a blocked state: {exc}",
                "failed",
                activation_event="onCommand",
            )
            emit(
                "command",
                f"Command trigger failed for {command}: {exc}",
                "failed",
                activation_event="onCommand",
            )
            failed_triggers.append(f"command:{command}")

    return failed_triggers


def reload_window_under_monitoring(browser: Browser, page: Page, *, deps: Any) -> Page:
    """Reload the current VS Code window after monitoring has started."""
    try:
        return deps.vscode.reload_workbench_window(
            browser,
            page,
            reconnect_timeout_ms=deps.vscode.DEFAULT_RECONNECT_TIMEOUT_MS,
            log=print,
        )
    except deps.vscode.ReloadWindowError as reconnect_error:
        raise PlaywrightError(
            f"Unable to reconnect to VS Code window after reload: {reconnect_error}"
        ) from reconnect_error
