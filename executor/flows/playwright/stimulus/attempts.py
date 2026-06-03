"""Attempt execution helpers for layered stimulus plans."""

from __future__ import annotations

import contextlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from .. import automation, uri_validation
from ..vscode import commands, debug, editor, terminal
from ..wait_helpers import (
    require_wait,
    wait_for_command_effect,
    wait_for_editor_ready,
    wait_for_trigger_effect,
    wait_for_ui_settle,
)
from .materializers import resolve_command_text, write_harness_context
from .types import (
    _HARNESS_READY_PATH,
    HARNESS_ACTIVATION_TIMEOUT_REASON,
    HARNESS_READY_MARKER_INVALID_REASON,
    HARNESS_READY_MARKER_MISSING_REASON,
    HARNESS_READY_MARKER_STALE_REASON,
    HarnessUnavailableError,
)


@dataclass(frozen=True)
class HarnessReadyMarker:
    """Parsed harness ready-marker payload (W8-0).

    The harness writes this JSON at the end of ``activate()``; the Python
    side validates each field before accepting the marker as proof that
    the harness command is registered.
    """

    ready_at_unix: float
    command: str
    marker_version: int
    epoch_run_id: str
    pid: int


def parse_harness_ready_marker(path: Path) -> HarnessReadyMarker | None:
    """Read and parse a harness ready marker. Returns None on any defect.

    Bare ``except Exception`` is forbidden by repo policy. We only swallow
    the four exception classes that legitimately mean "marker not yet
    valid": file-system race, malformed JSON, missing field, type error.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return HarnessReadyMarker(
            ready_at_unix=float(payload["ready_at_unix"]),
            command=str(payload["command"]),
            marker_version=int(payload["marker_version"]),
            epoch_run_id=str(payload.get("epoch_run_id", "")),
            pid=int(payload["pid"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _ensure_harness_ready(
    timeout_s: float = 15.0,
    *,
    poll_interval_s: float = 0.25,
    ready_path: Path = _HARNESS_READY_PATH,
    expected_epoch_run_id: str = "",
) -> None:
    """Block until the harness extension writes a valid ready marker, or raise.

    W8-0 split the legacy "marker exists" gate into four actionable cases:

    * ``harness_ready_marker_missing`` — deadline passed, marker never appeared.
    * ``harness_ready_marker_invalid`` — marker exists but payload is unparseable
      or missing required fields.
    * ``harness_ready_marker_stale`` — marker payload's ``epoch_run_id`` does
      not match ``expected_epoch_run_id`` (only checked when both are non-empty).
    * ``harness_activation_timeout`` — marker eventually appeared but only after
      the deadline (race observed mid-poll).

    The marker is written at the end of ``activate()`` in
    ``executor/flows/harness_extension/extension.js``; its valid presence
    proves the command has been registered for this container life.
    """
    deadline = time.monotonic() + timeout_s
    saw_marker_after_deadline = False
    while True:
        if ready_path.exists():
            marker = parse_harness_ready_marker(ready_path)
            if marker is None:
                raise HarnessUnavailableError(
                    f"Harness ready marker {ready_path} is unreadable.",
                    reason_code=HARNESS_READY_MARKER_INVALID_REASON,
                )
            if (
                expected_epoch_run_id
                and marker.epoch_run_id
                and marker.epoch_run_id != expected_epoch_run_id
            ):
                raise HarnessUnavailableError(
                    "Harness ready marker belongs to a previous run "
                    f"(payload epoch={marker.epoch_run_id!r} expected="
                    f"{expected_epoch_run_id!r}).",
                    reason_code=HARNESS_READY_MARKER_STALE_REASON,
                )
            if saw_marker_after_deadline:
                raise HarnessUnavailableError(
                    f"Harness ready marker {ready_path} arrived after "
                    f"{timeout_s:.1f}s deadline.",
                    reason_code=HARNESS_ACTIVATION_TIMEOUT_REASON,
                )
            return
        if time.monotonic() >= deadline:
            if ready_path.exists():
                saw_marker_after_deadline = True
                continue
            raise HarnessUnavailableError(
                f"Harness ready marker {ready_path} did not appear within "
                f"{timeout_s:.1f}s.",
                reason_code=HARNESS_READY_MARKER_MISSING_REASON,
            )
        time.sleep(poll_interval_s)


def _expected_harness_epoch() -> str:
    """Read the container's harness epoch run-id from the environment.

    Container ``start.sh`` exports ``EXTRACE_EPOCH_RUN_ID`` once per
    boot; the harness extension picks it up via ``process.env`` and
    stamps each marker. Empty here means stale-checking is disabled
    for backwards compatibility (e.g. pytest invocations outside a
    container).
    """
    return os.environ.get("EXTRACE_EPOCH_RUN_ID", "")


# W8-0: reason codes that signal a recoverable race (the marker may
# still be on its way) rather than corruption (a marker that exists
# but disagrees with our expectations).
_HARNESS_RECOVERABLE_REASONS = frozenset(
    {
        HARNESS_READY_MARKER_MISSING_REASON,
        HARNESS_ACTIVATION_TIMEOUT_REASON,
    }
)


def _ensure_harness_ready_with_recovery(
    timeout_s: float = 15.0,
    *,
    poll_interval_s: float = 0.25,
    ready_path: Path = _HARNESS_READY_PATH,
    expected_epoch_run_id: str = "",
    retry_budget: int = 1,
    recovery_sleep_s: float = 0.25,
) -> None:
    """Run ``_ensure_harness_ready`` with one controlled-recovery retry.

    On a recoverable miss (marker never appeared, or arrived past the
    deadline) we delete the marker path defensively (so a stale file
    cannot mask the second poll) and re-issue the wait once. STALE and
    INVALID reason codes are *not* recoverable here — they signal that
    the marker exists but disagrees with the current run, and another
    poll would just observe the same defective payload.
    """
    attempts = max(1, retry_budget + 1)
    last_error: HarnessUnavailableError | None = None
    for attempt_index in range(attempts):
        try:
            _ensure_harness_ready(
                timeout_s,
                poll_interval_s=poll_interval_s,
                ready_path=ready_path,
                expected_epoch_run_id=expected_epoch_run_id,
            )
            return
        except HarnessUnavailableError as exc:
            last_error = exc
            if attempt_index >= attempts - 1:
                raise
            if exc.reason_code not in _HARNESS_RECOVERABLE_REASONS:
                raise
            with contextlib.suppress(OSError):
                ready_path.unlink(missing_ok=True)
            time.sleep(recovery_sleep_s)
    # Defensive: the loop always either returns or raises above.
    if last_error is not None:
        raise last_error


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
            commands.drain_followup_ui(page)
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
        commands.drain_followup_ui(page)
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
        uri_validation.validate_uri_scheme(uri)
        terminal.new_terminal(page)
        require_wait(
            wait_for_ui_settle(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        uri_validation.run_uri_trigger(uri)
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
        _ensure_harness_ready_with_recovery(
            expected_epoch_run_id=_expected_harness_epoch()
        )
        write_harness_context(payload, attempt, trigger_method=trigger_method)
        commands.run_command(page, "ExTrace Harness: Run Current Stimulus")
        require_wait(
            wait_for_trigger_effect(
                page,
                event_recorder=event_recorder,
                activation_event=str(attempt.get("activation_event", "")),
            )
        )
        commands.drain_followup_ui(page)
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
