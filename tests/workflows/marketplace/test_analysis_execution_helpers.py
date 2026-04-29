"""Unit tests for workflows.marketplace.analysis_execution helpers."""

from __future__ import annotations

import contextlib
import threading
from typing import Any
from unittest.mock import MagicMock

import pytest

from executor.control import ExecutorControl, ExecutorError
from workflows.marketplace import trigger_service
from workflows.marketplace.analysis_errors import AnalysisCancelledError
from workflows.marketplace.analysis_execution import (
    StepReporter,
    _run_monitoring_heartbeat,
    install_failure_message,
    monitoring_failure_message,
    run_monitoring,
)
from appcore.contracts.schemas import AnalyzeRequest


def test_install_failure_message_without_output_returns_base_only() -> None:
    exc = ExecutorError("Command failed (rc=1): code --install-extension")
    message = install_failure_message(exc)
    assert message == "Extension installation failed inside the sandbox."


def test_install_failure_message_appends_stderr_tail() -> None:
    exc = ExecutorError(
        "Command failed (rc=1): code --install-extension",
        returncode=1,
        output="Error: singleton lock held by another process",
    )
    message = install_failure_message(exc)
    assert "Extension installation failed" in message
    assert "singleton lock held" in message


def test_install_failure_message_truncates_long_output_to_500_chars() -> None:
    big = "x" * 800 + "TAIL_MARKER"
    exc = ExecutorError("rc=1", returncode=1, output=big)
    message = install_failure_message(exc)
    assert "TAIL_MARKER" in message
    # First 300+ Xs from the head should NOT be in the tail slice.
    assert "x" * 600 not in message


def test_monitoring_failure_message_falls_back_when_detail_missing() -> None:
    exc = ExecutorError("")
    message = monitoring_failure_message(exc)
    assert message == (
        "Sandbox automation failed before the report could be finalized."
    )


def test_monitoring_failure_message_includes_detail_when_present() -> None:
    exc = ExecutorError("Command failed (rc=2): python3 entrypoint.py --monitor")
    message = monitoring_failure_message(exc)
    assert message.startswith(
        "Sandbox automation failed before the report could be finalized: "
    )
    assert "entrypoint.py" in message


def test_run_monitoring_heartbeat_emits_progress_from_report_payload() -> None:
    emitted: list[dict[str, Any]] = []

    def progress_callback(step, status, message, error_code, progress):
        emitted.append(
            {
                "step": step,
                "status": status,
                "message": message,
                "error_code": error_code,
                "progress": progress,
            }
        )

    payload = {
        "scenario_traces": [
            {"status": "completed"},
            {"status": "failed"},
            {"status": "running"},
        ]
    }

    def load_payload(_path: str) -> dict[str, Any]:
        return payload

    stop_event = threading.Event()

    def schedule_stop():
        # Allow exactly one tick to fire, then stop the heartbeat.
        stop_event.set()

    timer = threading.Timer(0.06, schedule_stop)
    timer.start()
    try:
        _run_monitoring_heartbeat(
            stop_event,
            StepReporter(progress_callback),
            report_path="report.json",
            total_initial=4,
            load_report_payload=load_payload,
            interval_s=0.05,
        )
    finally:
        timer.cancel()

    assert emitted, "heartbeat should have emitted at least one progress event"
    last = emitted[-1]
    assert last["step"] == "run_monitoring"
    assert last["status"] == "running"
    assert last["progress"] == {"completed": 2, "total": 4}
    assert "2/4" in last["message"]


def test_run_monitoring_heartbeat_tolerates_missing_payload() -> None:
    emitted: list[dict[str, Any]] = []

    def progress_callback(step, status, message, error_code, progress):
        emitted.append({"progress": progress, "message": message})

    def load_payload(_path: str) -> None:
        return None

    stop_event = threading.Event()
    timer = threading.Timer(0.06, stop_event.set)
    timer.start()
    try:
        _run_monitoring_heartbeat(
            stop_event,
            StepReporter(progress_callback),
            report_path="report.json",
            total_initial=0,
            load_report_payload=load_payload,
            interval_s=0.05,
        )
    finally:
        timer.cancel()

    assert emitted
    # With total=0 and missing payload we fall back to the legacy "still running" message.
    assert emitted[-1]["progress"] is None
    assert "still running" in emitted[-1]["message"].lower()


def test_run_monitoring_heartbeat_invokes_on_cancel_and_breaks() -> None:
    cancel_calls = {"count": 0}

    def cancel_check() -> bool:
        return True

    def on_cancel() -> None:
        cancel_calls["count"] += 1

    stop_event = threading.Event()
    started_at = threading.Event()
    started_at.set()

    _run_monitoring_heartbeat(
        stop_event,
        StepReporter(lambda *_a, **_k: None),
        report_path="report.json",
        total_initial=0,
        load_report_payload=lambda _p: None,
        cancel_check=cancel_check,
        on_cancel=on_cancel,
        interval_s=0.01,
    )

    assert cancel_calls["count"] == 1


def test_run_monitoring_heartbeat_swallows_on_cancel_exceptions() -> None:
    """A faulty on_cancel handler must not abort the heartbeat — the run loop
    still has to break cleanly so the parent run_monitoring can finish."""
    on_cancel_calls = {"count": 0}

    def cancel_check() -> bool:
        return True

    def on_cancel() -> None:
        on_cancel_calls["count"] += 1
        raise RuntimeError("synthetic on_cancel failure")

    stop_event = threading.Event()
    _run_monitoring_heartbeat(
        stop_event,
        StepReporter(lambda *_a, **_k: None),
        report_path="report.json",
        total_initial=0,
        load_report_payload=lambda _p: None,
        cancel_check=cancel_check,
        on_cancel=on_cancel,
        interval_s=0.01,
    )

    assert on_cancel_calls["count"] == 1


def test_run_monitoring_heartbeat_emits_on_cancel_only_once() -> None:
    """If cancel_check stays True across ticks, on_cancel must fire exactly once."""
    on_cancel_calls = {"count": 0}

    def on_cancel() -> None:
        on_cancel_calls["count"] += 1

    stop_event = threading.Event()
    # The heartbeat breaks after the first cancel, so even a stable cancel_check
    # should only invoke on_cancel once. We verify the contract explicitly.
    _run_monitoring_heartbeat(
        stop_event,
        StepReporter(lambda *_a, **_k: None),
        report_path="report.json",
        total_initial=0,
        load_report_payload=lambda _p: None,
        cancel_check=lambda: True,
        on_cancel=on_cancel,
        interval_s=0.01,
    )

    assert on_cancel_calls["count"] == 1


def test_run_monitoring_heartbeat_per_tick_load_is_constant_under_5s_interval() -> None:
    """Heartbeat tick interval was tightened from 30 s → 5 s
    (`analysis_execution.py:82`) for cancel responsiveness; this raised the
    tick rate by 6x, which means the executor + DB layer must absorb 6x more
    polls per long run. Per-tick cost (one ``load_report_payload`` and one
    ``cancel_check`` call) must stay constant: a regression that adds extra
    IO inside the loop body would silently amplify production load.

    Closes [FOLLOWUP simulation-progress-cancel] heartbeat 30s→5s load
    verification gap (``POST_POC_BACKLOG.md`` item
    [FOLLOWUP simulation-progress-cancel] cancel-after-finish race test;
    landed 2026-04-27 on ``feat/w8-2-and-reviewer-feedback-gaps``)."""
    payload_reads: list[str] = []
    cancel_polls: list[int] = []

    def load_payload(path: str) -> dict[str, Any]:
        payload_reads.append(path)
        return {"scenario_traces": [{"status": "running"}]}

    def cancel_check() -> bool:
        cancel_polls.append(len(cancel_polls))
        return False

    target_ticks = 6  # 30 s / 5 s = 6x tick amplification
    stop_event = threading.Event()

    def schedule_stop() -> None:
        # Allow exactly target_ticks tick intervals, then halt the loop.
        # interval_s=0.01 ⇒ stop after ≥6 ticks fire.
        stop_event.wait(0.01 * target_ticks + 0.005)
        stop_event.set()

    stopper = threading.Thread(target=schedule_stop, daemon=True)
    stopper.start()
    try:
        _run_monitoring_heartbeat(
            stop_event,
            StepReporter(lambda *_a, **_k: None),
            report_path="report.json",
            total_initial=4,
            load_report_payload=load_payload,
            cancel_check=cancel_check,
            interval_s=0.01,
        )
    finally:
        stopper.join(timeout=1.0)

    payload_count = len(payload_reads)
    cancel_count = len(cancel_polls)

    # Per-tick contract: each tick fires exactly one payload read and one
    # cancel poll. Allow a small jitter window (±2 ticks) to absorb timing
    # noise on busy CI runners while still catching a regression that
    # doubles the per-tick IO cost.
    assert payload_count == cancel_count, (
        f"per-tick load drifted: {payload_count} payload reads vs "
        f"{cancel_count} cancel polls (must be 1:1)"
    )
    assert target_ticks - 2 <= cancel_count <= target_ticks + 2, (
        f"unexpected tick count {cancel_count}; expected ~{target_ticks} "
        "(jitter ±2). A regression that adds an extra IO inside the loop "
        "body would surface here as 2x growth."
    )
    assert all(
        p == "report.json" for p in payload_reads
    ), "payload reader must always receive the canonical report path"


# --- run_monitoring (cancel-flow integration) ---------------------------------

_ANALYZE_KWARGS = {"publisher": "ms-python", "name": "python", "version": "2025.0.0"}


def _trigger_plan(scenarios: list[str]) -> trigger_service.TriggerPlan:
    return trigger_service.TriggerPlan(
        trigger_container_path="/results/triggers.json",
        selected_scenarios=scenarios,
        skip_automation=False,
        reason_code="generated_trigger_plan",
        message="ready",
    )


def _executor_control(
    *,
    run_automation: object = "automation completed",
    reset_sandbox: object = "reset ok",
) -> MagicMock:
    control = MagicMock(spec=ExecutorControl)
    control.run_automation.side_effect = (
        run_automation if isinstance(run_automation, Exception) else None
    )
    if not isinstance(run_automation, Exception):
        control.run_automation.return_value = str(run_automation)
    control.reset_sandbox.side_effect = (
        reset_sandbox if isinstance(reset_sandbox, Exception) else None
    )
    if not isinstance(reset_sandbox, Exception):
        control.reset_sandbox.return_value = str(reset_sandbox)
    return control


def _install_synchronous_heartbeat(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the heartbeat with a synchronous shim that fires on_cancel once.

    The real ``_run_monitoring_heartbeat`` polls every 5 s, which is too slow
    for unit tests. We swap in a deterministic version: it invokes the cancel
    callback on the first tick (so ``cancel_triggered`` flips inside
    ``run_monitoring`` before ``executor_control.run_automation`` is called)
    and exits immediately. This mirrors the production behavior — the heartbeat
    runs on a daemon thread, ``run_automation`` runs on the main thread — but
    eliminates wall-clock waits.
    """

    def fake_heartbeat(
        stop_event: threading.Event,
        _reporter: StepReporter,
        *,
        report_path: str,
        total_initial: int,
        load_report_payload: Any,
        cancel_check: Any = None,
        on_cancel: Any = None,
        interval_s: float = 0.0,
    ) -> None:
        _ = (report_path, total_initial, load_report_payload, interval_s)
        if cancel_check is not None and cancel_check() and on_cancel is not None:
            with contextlib.suppress(
                ExecutorError, RuntimeError, OSError, ValueError, AttributeError
            ):
                on_cancel()
        stop_event.wait(timeout=0.05)

    import workflows.marketplace.analysis_execution as analysis_execution

    monkeypatch.setattr(analysis_execution, "_run_monitoring_heartbeat", fake_heartbeat)


def test_run_monitoring_raises_cancelled_when_cancel_check_fires_during_automation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When cancel_check returns True during the heartbeat, run_monitoring must
    convert the resulting ExecutorError into AnalysisCancelledError so the
    background worker silently exits instead of marking the job 'failed'."""
    _install_synchronous_heartbeat(monkeypatch)
    request = AnalyzeRequest(**_ANALYZE_KWARGS)

    on_cancel_calls = {"count": 0}

    def on_cancel_signal() -> None:
        on_cancel_calls["count"] += 1

    executor_control = _executor_control()
    executor_control.run_automation.side_effect = ExecutorError(
        "automation interrupted by sandbox reset"
    )

    progress_events: list[tuple[str, str, str, str | None, dict[str, int] | None]] = []

    def callback(step, status, message, error_code, progress):
        progress_events.append((step, status, message, error_code, progress))

    with pytest.raises(AnalysisCancelledError):
        run_monitoring(
            request,
            "report.json",
            _trigger_plan(["coding_session"]),
            StepReporter(callback),
            executor_control,
            trigger_payload_exists=lambda _p: True,
            load_report_payload=lambda _p: None,
            validate_trigger_plan_report=lambda *_args, **_kw: None,
            build_report_messages=lambda *_args, **_kw: ("ok", "done"),
            cancel_check=lambda: True,
            on_cancel_signal=on_cancel_signal,
        )

    assert on_cancel_calls["count"] == 1
    executor_control.reset_sandbox.assert_called_with(reload_window=True)
    # The "running" → "failed" transition must NOT have been emitted; the cancel
    # path takes precedence over the failure-message branch.
    assert not any(status == "failed" for _, status, _, _, _ in progress_events)


def test_run_monitoring_raises_cancelled_when_cancel_observed_after_clean_finish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the executor returns successfully but the heartbeat already observed
    a cancel, run_monitoring still raises AnalysisCancelledError — we don't want
    a partial run to be reported as 'success' once the user has clicked Stop."""
    _install_synchronous_heartbeat(monkeypatch)
    request = AnalyzeRequest(**_ANALYZE_KWARGS)

    on_cancel_calls = {"count": 0}

    def on_cancel_signal() -> None:
        on_cancel_calls["count"] += 1

    executor_control = _executor_control()
    # Note: run_automation returns successfully — the cancel was set before
    # the call (by the synchronous heartbeat shim) so the post-call branch
    # ``if cancel_triggered.is_set(): raise AnalysisCancelledError`` should fire.

    with pytest.raises(AnalysisCancelledError):
        run_monitoring(
            request,
            "report.json",
            _trigger_plan(["coding_session"]),
            StepReporter(lambda *_a, **_k: None),
            executor_control,
            trigger_payload_exists=lambda _p: True,
            load_report_payload=lambda _p: None,
            validate_trigger_plan_report=lambda *_args, **_kw: None,
            build_report_messages=lambda *_args, **_kw: ("ok", "done"),
            cancel_check=lambda: True,
            on_cancel_signal=on_cancel_signal,
        )

    assert on_cancel_calls["count"] == 1


def test_run_monitoring_swallows_reset_sandbox_failure_during_cancel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the cancel-time reset itself raises, the heartbeat must log and move
    on rather than crashing the worker. AnalysisCancelledError must still be
    the surface error — not the ExecutorError from reset_sandbox."""
    _install_synchronous_heartbeat(monkeypatch)
    request = AnalyzeRequest(**_ANALYZE_KWARGS)

    executor_control = _executor_control()
    executor_control.reset_sandbox.side_effect = ExecutorError("reset boom")
    executor_control.run_automation.side_effect = ExecutorError("aborted")

    with pytest.raises(AnalysisCancelledError):
        run_monitoring(
            request,
            "report.json",
            _trigger_plan(["coding_session"]),
            StepReporter(lambda *_a, **_k: None),
            executor_control,
            trigger_payload_exists=lambda _p: True,
            load_report_payload=lambda _p: None,
            validate_trigger_plan_report=lambda *_args, **_kw: None,
            build_report_messages=lambda *_args, **_kw: ("ok", "done"),
            cancel_check=lambda: True,
        )

    # reset_sandbox(reload_window=True) was called from _heartbeat_on_cancel
    # and raised, but the surface error remained AnalysisCancelledError.
    executor_control.reset_sandbox.assert_called_with(reload_window=True)


def test_run_monitoring_emits_initial_progress_zero_of_total_when_scenarios_planned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The very first progress emit at the start of run_monitoring should carry
    a {completed: 0, total: N} payload so the UI can render an honest 0%
    instead of jumping from "queued" to mid-progress when monitoring begins."""
    _install_synchronous_heartbeat(monkeypatch)
    # The shim flips cancel; for this test we don't want cancellation, so use a
    # heartbeat shim that does nothing.

    def noop_heartbeat(stop_event: threading.Event, *_a: Any, **_kw: Any) -> None:
        stop_event.wait(timeout=0.01)

    import workflows.marketplace.analysis_execution as analysis_execution

    monkeypatch.setattr(analysis_execution, "_run_monitoring_heartbeat", noop_heartbeat)

    request = AnalyzeRequest(**_ANALYZE_KWARGS)
    executor_control = _executor_control()
    progress_events: list[tuple[str, str, str, str | None, dict[str, int] | None]] = []

    run_monitoring(
        request,
        "report.json",
        _trigger_plan(["coding_session", "search_workflow", "settings_modification"]),
        StepReporter(lambda *args: progress_events.append(args)),
        executor_control,
        trigger_payload_exists=lambda _p: True,
        load_report_payload=lambda _p: None,
        validate_trigger_plan_report=lambda *_args, **_kw: None,
        build_report_messages=lambda *_args, **_kw: ("ok", "done"),
    )

    initial = progress_events[0]
    assert initial[0] == "run_monitoring"
    assert initial[1] == "running"
    # progress is the 5th positional arg when called via the reporter callback.
    assert initial[4] == {"completed": 0, "total": 3}
