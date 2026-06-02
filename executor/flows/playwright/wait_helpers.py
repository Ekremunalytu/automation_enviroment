"""Bounded readiness and verification helpers for Playwright executor flows."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Error as PlaywrightError

AutomationEventRecorder = Callable[[str, str, str, str, str], None]


@dataclass(frozen=True)
class WaitResult:
    status: str
    reason_code: str = ""
    detail: str = ""
    observed: bool = False


class WaitTimeoutError(RuntimeError):
    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code


def wait_for_ui_settle(
    page: Any,
    *,
    event_recorder: AutomationEventRecorder | None = None,
    activation_event: str = "",
) -> WaitResult:
    return _wait_for_duration(
        page,
        event_name="wait_for_ui_settle",
        timeout_ms=2000,
        poll_ms=100,
        detail="Waiting for the VS Code UI to settle.",
        event_recorder=event_recorder,
        activation_event=activation_event,
    )


def wait_for_editor_ready(
    page: Any,
    *,
    event_recorder: AutomationEventRecorder | None = None,
    activation_event: str = "",
) -> WaitResult:
    return _wait_for_selector(
        page,
        event_name="wait_for_editor_ready",
        selector=".monaco-editor",
        timeout_ms=2000,
        poll_ms=100,
        reason_code="editor_ready_timeout",
        detail="Timed out waiting for the editor surface to become ready.",
        event_recorder=event_recorder,
        activation_event=activation_event,
    )


def wait_for_command_effect(
    page: Any,
    *,
    event_recorder: AutomationEventRecorder | None = None,
    activation_event: str = "",
) -> WaitResult:
    return _wait_for_duration(
        page,
        event_name="wait_for_command_effect",
        timeout_ms=1500,
        poll_ms=100,
        detail="Waiting for a command-side UI effect to surface.",
        event_recorder=event_recorder,
        activation_event=activation_event,
    )


def wait_for_trigger_effect(
    page: Any,
    *,
    event_recorder: AutomationEventRecorder | None = None,
    activation_event: str = "",
) -> WaitResult:
    return _wait_for_duration(
        page,
        event_name="wait_for_trigger_effect",
        timeout_ms=1500,
        poll_ms=100,
        detail="Waiting for a trigger-side effect to surface.",
        event_recorder=event_recorder,
        activation_event=activation_event,
    )


def wait_for_target_reaction(
    monitor: Any | None,
    baseline: dict[str, int | bool],
    *,
    capability: str,
    trigger_label: str,
    activation_event: str = "",
    event_recorder: AutomationEventRecorder | None = None,
) -> WaitResult:
    _emit(
        event_recorder,
        "wait_for_target_reaction",
        (f"Waiting for target-owned telemetry after {trigger_label} ({capability})."),
        "running",
        activation_event=activation_event,
    )
    if monitor is None:
        result = WaitResult(
            status="failed",
            reason_code="target_reaction_unavailable",
            detail="Target reaction verification requires a live monitor instance.",
        )
        _emit_result(
            event_recorder,
            "wait_for_target_reaction",
            result,
            activation_event=activation_event,
        )
        return result

    polls = int(8000 / 500)
    for _ in range(polls):
        snapshot = monitor.capture_runtime_snapshot()
        if _snapshot_changed(snapshot, baseline):
            monitor.verify_target_reaction(
                baseline,
                capability=capability,
                trigger_label=trigger_label,
                activation_event=activation_event,
                success_signal=True,
            )
            result = WaitResult(
                status="completed",
                detail=(
                    f"Observed target-owned telemetry growth after {trigger_label}."
                ),
                observed=True,
            )
            _emit_result(
                event_recorder,
                "wait_for_target_reaction",
                result,
                activation_event=activation_event,
            )
            return result
        _wait(page=None, timeout_ms=500)

    monitor.verify_target_reaction(
        baseline,
        capability=capability,
        trigger_label=trigger_label,
        activation_event=activation_event,
        success_signal=False,
    )
    result = WaitResult(
        status="failed",
        reason_code="target_reaction_timeout",
        detail=(
            "Timed out waiting for target-owned activation, file, or network "
            f"telemetry after {trigger_label}."
        ),
    )
    _emit_result(
        event_recorder,
        "wait_for_target_reaction",
        result,
        activation_event=activation_event,
    )
    return result


def wait_for_idle_observation(
    page: Any | None = None,
    *,
    monitor: Any | None = None,
    event_recorder: AutomationEventRecorder | None = None,
    activation_event: str = "",
) -> WaitResult:
    _emit(
        event_recorder,
        "wait_for_idle_observation",
        "Opening a bounded idle observation window for deferred activations.",
        "running",
        activation_event=activation_event,
    )
    baseline = monitor.capture_runtime_snapshot() if monitor is not None else {}
    polls = int(8000 / 500)
    for _ in range(polls):
        _wait(page=page, timeout_ms=500)
        if monitor is None:
            continue
        snapshot = monitor.capture_runtime_snapshot()
        if _snapshot_changed(snapshot, baseline):
            result = WaitResult(
                status="completed",
                detail="Observed deferred telemetry during the idle observation window.",
                observed=True,
            )
            _emit_result(
                event_recorder,
                "wait_for_idle_observation",
                result,
                activation_event=activation_event,
            )
            return result
    result = WaitResult(
        status="failed",
        reason_code="idle_observation_timeout",
        detail="Idle observation window ended without new target telemetry.",
    )
    _emit_result(
        event_recorder,
        "wait_for_idle_observation",
        result,
        activation_event=activation_event,
    )
    return result


def require_wait(result: WaitResult) -> None:
    if result.status != "completed":
        raise WaitTimeoutError(result.reason_code or "wait_timeout", result.detail)


def _wait_for_duration(
    page: Any,
    *,
    event_name: str,
    timeout_ms: int,
    poll_ms: int,
    detail: str,
    event_recorder: AutomationEventRecorder | None,
    activation_event: str,
) -> WaitResult:
    _emit(
        event_recorder, event_name, detail, "running", activation_event=activation_event
    )
    # Host-side sleep (page=None), NOT page.wait_for_timeout: an in-renderer
    # wait is measured in *renderer* time, so under cumulative load a nominal
    # 3s settle ballooned to ~8.5s of wall-clock. A flat host-side delay stays
    # at its nominal cost. (A monitor.capture_runtime_snapshot() early-exit was
    # tried and reverted — each snapshot does a renderer round-trip + full
    # exthost-log reparse, ~8s under load, which inflated every wait to ~50s.)
    for _ in range(int(timeout_ms / poll_ms)):
        _wait(page=None, timeout_ms=poll_ms)
    result = WaitResult(status="completed", detail=detail)
    _emit_result(event_recorder, event_name, result, activation_event=activation_event)
    return result


def _wait_for_selector(
    page: Any,
    *,
    event_name: str,
    selector: str,
    timeout_ms: int,
    poll_ms: int,
    reason_code: str,
    detail: str,
    event_recorder: AutomationEventRecorder | None,
    activation_event: str,
) -> WaitResult:
    _emit(
        event_recorder, event_name, detail, "running", activation_event=activation_event
    )
    wait_for_selector = getattr(page, "wait_for_selector", None)
    if not callable(wait_for_selector):
        return _wait_for_duration(
            page,
            event_name=event_name,
            timeout_ms=timeout_ms,
            poll_ms=poll_ms,
            detail=detail,
            event_recorder=event_recorder,
            activation_event=activation_event,
        )
    for _ in range(int(timeout_ms / poll_ms)):
        try:
            wait_for_selector(selector, state="visible", timeout=poll_ms)
            result = WaitResult(status="completed", detail=detail)
            _emit_result(
                event_recorder,
                event_name,
                result,
                activation_event=activation_event,
            )
            return result
        except (PlaywrightError, RuntimeError, ValueError):
            _wait(page=page, timeout_ms=poll_ms)
    result = WaitResult(status="failed", reason_code=reason_code, detail=detail)
    _emit_result(event_recorder, event_name, result, activation_event=activation_event)
    return result


def _emit(
    recorder: AutomationEventRecorder | None,
    event_name: str,
    message: str,
    status: str,
    *,
    activation_event: str = "",
) -> None:
    if recorder is None:
        return
    recorder(event_name, message, status, "", activation_event)


def _emit_result(
    recorder: AutomationEventRecorder | None,
    event_name: str,
    result: WaitResult,
    *,
    activation_event: str = "",
) -> None:
    _emit(
        recorder,
        event_name,
        result.detail or event_name,
        "completed" if result.status == "completed" else "failed",
        activation_event=activation_event,
    )


def _snapshot_changed(
    current: dict[str, int | bool],
    baseline: dict[str, int | bool],
) -> bool:
    return (
        int(current.get("target_activations", 0) or 0)
        > int(baseline.get("target_activations", 0) or 0)
        or int(current.get("target_file_events", 0) or 0)
        > int(baseline.get("target_file_events", 0) or 0)
        or int(current.get("target_network_events", 0) or 0)
        > int(baseline.get("target_network_events", 0) or 0)
        or bool(current.get("target_running", False))
        != bool(baseline.get("target_running", False))
    )


def _wait(page: Any | None, timeout_ms: int) -> None:
    if page is not None and hasattr(page, "wait_for_timeout"):
        page.wait_for_timeout(timeout_ms)
        return
    time.sleep(timeout_ms / 1000)
