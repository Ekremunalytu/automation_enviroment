"""Direct unit tests for ``MonitorRuntime`` (W11-1).

These tests pin the runtime state machine extracted from
``ExtensionMonitor`` in W11-1. They import at the real module path
(``executor.flows.playwright.monitor_runtime_state``) rather than
through the ``monitor`` facade so that the W12 directory reshuffle
cannot silently regress this surface.

Cross-module callbacks (persist, record_automation_event,
finalize_scenarios, append_activation_log_entries, refresh_derived_state)
are stubbed with simple recorders so each test asserts that the runtime
calls the right collaborator at the right point in the lifecycle.
"""

from __future__ import annotations

from typing import Any

from executor.flows.playwright import monitor
from executor.flows.playwright.monitor_runtime_state import MonitorRuntime
from executor.flows.playwright.monitor_types import ActivationReport


class _DummyPage:
    pass


class _RecordingHooks:
    """Bundle of collaborator callbacks with call recorders."""

    def __init__(self) -> None:
        self.persist_calls: list[bool] = []
        self.automation_events: list[tuple[str, str, dict[str, Any]]] = []
        self.finalize_calls: int = 0
        self.append_calls: int = 0
        self.refresh_calls: int = 0
        # W11-3: list of strategy-id lists shipped via the runtime callback.
        self.discovery_strategy_calls: list[list[str]] = []
        # W11-4: counts ``emit_intermediate_state_events`` invocations
        # routed through the runtime → facade-shim → accountant chain.
        self.emit_intermediate_calls: int = 0
        # W11-4: snapshot of runtime callback ordering — appended once
        # per stop() for ``refresh`` and ``emit`` so tests can pin the
        # post-refresh emission ordering invariant.
        self.callback_order: list[str] = []

    def persist(self, force: bool) -> None:
        self.persist_calls.append(force)

    def record_automation_event(
        self,
        kind: str,
        message: str,
        status: str = "",
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        self.automation_events.append(
            (
                kind,
                message,
                {
                    "status": status,
                    "scenario_name": scenario_name,
                    "activation_event": activation_event,
                },
            )
        )

    def finalize_scenarios(self) -> None:
        self.finalize_calls += 1

    def append_activation_log_entries(self) -> None:
        self.append_calls += 1

    def refresh_derived_state(self) -> None:
        self.refresh_calls += 1
        self.callback_order.append("refresh")

    def set_discovery_strategies(self, strategies: list[str]) -> None:
        self.discovery_strategy_calls.append(list(strategies))

    def emit_intermediate_state_events(self) -> None:
        self.emit_intermediate_calls += 1
        self.callback_order.append("emit")


class _FakeNetworkCapture:
    def __init__(
        self,
        monitoring_start: float,
        on_event: Any = None,
        events: list[Any] | None = None,
        *,
        capture_error: str = "",
        start_error: str = "",
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events = list(events or [])
        self.capture_error = capture_error
        self.start_error = start_error
        self.start_called: bool = False
        self.stop_called: bool = False

    def start(self) -> None:
        self.start_called = True
        if self.on_event is not None:
            for event in self.events:
                self.on_event(event)

    def stop(self) -> list[Any]:
        self.stop_called = True
        return list(self.events)


class _FakeFileCapture:
    def __init__(
        self,
        monitoring_start: float,
        on_event: Any = None,
        events: list[Any] | None = None,
        *,
        start_error: str = "",
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events = list(events or [])
        self.start_error = start_error
        self.stop_called: bool = False

    def start(self) -> None:
        if self.on_event is not None:
            for event in self.events:
                self.on_event(event)

    def stop(self) -> list[Any]:
        self.stop_called = True
        return list(self.events)


class _FakeExtensionHostCapture:
    def __init__(
        self,
        monitoring_start: float,
        on_event: Any = None,
        on_process_event: Any = None,
        *,
        start_error: str = "",
        attach_attempts: int = 1,
        pid: int | None = 4242,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.on_process_event = on_process_event
        self.start_error = start_error
        self.attach_attempts = attach_attempts
        self.pid = pid
        self.diagnostics = diagnostics or {"status": "planned"}
        self.start_called: bool = False
        self.stop_called: bool = False

    def start(self) -> None:
        self.start_called = True

    def stop(self) -> list[Any]:
        self.stop_called = True
        return []


def _build_runtime(
    *,
    page: Any = None,
    target_extension_id: str = "publisher.tool",
) -> tuple[MonitorRuntime, ActivationReport, _RecordingHooks]:
    report = ActivationReport(target_extension_id=target_extension_id)
    hooks = _RecordingHooks()
    runtime = MonitorRuntime(
        page=page or _DummyPage(),
        report=report,
        persist=hooks.persist,
        record_automation_event=hooks.record_automation_event,
        finalize_scenarios=hooks.finalize_scenarios,
        append_activation_log_entries=hooks.append_activation_log_entries,
        refresh_derived_state=hooks.refresh_derived_state,
        set_discovery_strategies=hooks.set_discovery_strategies,
        emit_intermediate_state_events=hooks.emit_intermediate_state_events,
    )
    return runtime, report, hooks


def _patch_facade(monkeypatch, **overrides: Any) -> None:
    """Install lightweight fakes on the ``monitor`` facade module.

    ``MonitorRuntime`` resolves dependencies through
    ``resolve_monitor_api()``. Each test patches only what it needs;
    sane defaults are filled in for the rest so ``start()`` and
    ``stop()`` do not crash on a missing attribute.
    """

    defaults: dict[str, Any] = {
        "_snapshot_log_offsets": lambda: {},
        "parse_all_exthost_logs": lambda start_offsets=None: [],
        "find_exthost_logs": lambda: [],
        "get_running_extensions": lambda page: [],
        "read_extension_host_output": lambda page=None: "",
        "parse_activations_from_output": lambda output, monitoring_start=0.0: [],
        "NetworkCapture": lambda monitoring_start, on_event=None: _FakeNetworkCapture(
            monitoring_start, on_event, []
        ),
        "FileSystemCapture": lambda monitoring_start, on_event=None: _FakeFileCapture(
            monitoring_start, on_event, []
        ),
        "ExtensionHostFileCapture": (
            lambda monitoring_start, on_event=None, on_process_event=None: (
                _FakeExtensionHostCapture(monitoring_start, on_event, on_process_event)
            )
        ),
    }
    defaults.update(overrides)
    for name, value in defaults.items():
        monkeypatch.setattr(monitor, name, value)


def test_init_state_defaults() -> None:
    runtime, report, hooks = _build_runtime()

    assert runtime.started is False
    assert runtime.log_offsets == {}
    assert isinstance(runtime.page, _DummyPage)
    assert runtime._network_capture is None
    assert runtime._file_capture is None
    assert runtime._extension_file_capture is None
    assert hooks.persist_calls == []
    assert report.network_events == []
    assert report.file_events == []


def test_page_setter_updates_runtime_page() -> None:
    """W11-5: ``MonitorRuntime.page`` setter lets the facade rewire the
    page reference after a reload (``entrypoint_runner`` calls
    ``mon.page = reloaded_page`` post-reload)."""

    runtime, _report, _hooks = _build_runtime()
    new_page = _DummyPage()

    runtime.page = new_page

    assert runtime.page is new_page
    assert runtime._page is new_page


def test_start_snapshots_log_offsets_and_attaches_captures(monkeypatch) -> None:
    expected_offsets = {"exthost-1.log": 17, "exthost-2.log": 99}
    _patch_facade(
        monkeypatch,
        _snapshot_log_offsets=lambda: expected_offsets,
    )

    runtime, report, hooks = _build_runtime()
    runtime.start()

    assert runtime.started is True
    assert runtime.log_offsets == expected_offsets
    assert report.log_offsets_snapshot == expected_offsets
    assert report.monitoring_start > 0.0
    assert runtime._network_capture is not None
    assert runtime._file_capture is not None
    assert hooks.persist_calls == [True]


def test_start_records_network_capture_failure(monkeypatch) -> None:
    _patch_facade(
        monkeypatch,
        NetworkCapture=lambda monitoring_start, on_event=None: _FakeNetworkCapture(
            monitoring_start,
            on_event,
            [],
            capture_error="tshark unavailable on host",
        ),
    )

    runtime, report, hooks = _build_runtime()
    runtime.start()

    assert report.network_capture_error == "tshark unavailable on host"
    assert any(
        kind == "network_capture" and meta["status"] == "failed"
        for kind, _msg, meta in hooks.automation_events
    )


def test_attach_runtime_tracers_records_completion(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def make_capture(monitoring_start, on_event=None, on_process_event=None):
        capture = _FakeExtensionHostCapture(
            monitoring_start,
            on_event,
            on_process_event,
            attach_attempts=2,
            pid=1717,
            diagnostics={"status": "attached", "selected_pid": 1717, "attempts": 2},
        )
        captured["capture"] = capture
        return capture

    _patch_facade(monkeypatch, ExtensionHostFileCapture=make_capture)

    runtime, report, hooks = _build_runtime()
    runtime.attach_runtime_tracers()

    assert captured["capture"].start_called is True
    assert report.file_capture_diagnostics["selected_pid"] == 1717
    assert any(
        kind == "runtime_tracer_attach" and meta["status"] == "completed"
        for kind, _msg, meta in hooks.automation_events
    )


def test_attach_runtime_tracers_records_failure_without_crashing(monkeypatch) -> None:
    def failing_capture(monitoring_start, on_event=None, on_process_event=None):
        return _FakeExtensionHostCapture(
            monitoring_start,
            on_event,
            on_process_event,
            start_error="Extension Host PID not found; file attribution unavailable.",
            attach_attempts=4,
            pid=None,
            diagnostics={
                "attempts": 4,
                "selected_pid": None,
                "status": "failed",
            },
        )

    _patch_facade(monkeypatch, ExtensionHostFileCapture=failing_capture)

    runtime, report, hooks = _build_runtime()
    runtime.attach_runtime_tracers()

    assert report.file_capture_error
    assert report.file_capture_diagnostics["attempts"] == 4
    assert any(
        kind == "runtime_tracer_attach" and meta["status"] == "failed"
        for kind, _msg, meta in hooks.automation_events
    )


def test_attach_runtime_tracers_is_idempotent(monkeypatch) -> None:
    call_count = {"value": 0}

    def make_capture(monitoring_start, on_event=None, on_process_event=None):
        call_count["value"] += 1
        return _FakeExtensionHostCapture(monitoring_start, on_event, on_process_event)

    _patch_facade(monkeypatch, ExtensionHostFileCapture=make_capture)

    runtime, _report, _hooks = _build_runtime()
    runtime.attach_runtime_tracers()
    runtime.attach_runtime_tracers()
    runtime.attach_runtime_tracers()

    assert call_count["value"] == 1


def test_stop_runs_strategies_and_invokes_collaborator_callbacks(
    monkeypatch, tmp_path
) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text("placeholder")
    activation = monitor.ActivationEntry(
        extension_id="publisher.tool",
        activation_event="onCommand:publisher.tool.run",
        timestamp="2026-01-01 10:00:00.500",
        source="log",
    )
    _patch_facade(
        monkeypatch,
        parse_all_exthost_logs=lambda start_offsets=None: [activation],
        find_exthost_logs=lambda: [log_file],
        read_extension_host_output=lambda page=None: "extension host output",
    )

    runtime, report, hooks = _build_runtime()
    runtime.start()
    returned = runtime.stop()

    assert returned is report
    assert report.activated and report.activated[0].extension_id == "publisher.tool"
    assert report.log_file_path == str(log_file)
    assert report.extension_host_output == "extension host output"
    assert report.monitoring_end >= report.monitoring_start
    assert hooks.finalize_calls == 1
    assert hooks.append_calls == 1
    assert hooks.refresh_calls == 1
    # start() persists once with force=True; stop() persists multiple times
    # (post-finalize, after each strategy, and at the end after refresh).
    assert hooks.persist_calls.count(True) >= 4
    # W11-3: strategy 1 (parse_all_exthost_logs) returned a non-empty
    # list and strategy 3's parse_activations_from_output returned [],
    # so only "exthost_log_parse" lands. Pin one shipped emission.
    assert hooks.discovery_strategy_calls == [["exthost_log_parse"]]


def test_stop_without_start_falls_back_safely(monkeypatch) -> None:
    _patch_facade(monkeypatch)

    runtime, report, hooks = _build_runtime()
    returned = runtime.stop()

    assert returned is report
    assert report.monitoring_start > 0.0
    assert report.monitoring_end >= report.monitoring_start
    assert hooks.finalize_calls == 1
    assert hooks.refresh_calls == 1


def test_context_manager_invokes_start_and_stop(monkeypatch) -> None:
    _patch_facade(monkeypatch)

    runtime, _report, hooks = _build_runtime()
    with runtime as ctx:
        assert ctx is runtime
        assert runtime.started is True

    assert hooks.finalize_calls == 1
    assert hooks.refresh_calls == 1


def test_handle_network_event_appends_and_persists() -> None:
    runtime, report, hooks = _build_runtime()
    event = monitor.NetworkEvent(
        timestamp="2026-01-01T10:00:00.000",
        rel_time_s=0.1,
        protocol="tls",
        event_type="tls_client_hello",
        source_ip="10.0.0.2",
        destination_ip="140.82.112.3",
        destination_port=443,
        host="github.com",
        summary="Client Hello",
    )

    runtime._handle_network_event(event)

    assert report.network_events == [event]
    assert hooks.persist_calls == [False]


def test_handle_process_event_appends_and_persists(tmp_path) -> None:
    runtime, report, hooks = _build_runtime()
    event = monitor.ProcessEvent(
        timestamp="2026-01-01T10:00:00.000",
        rel_time_s=0.1,
        pid=1234,
        ppid=1,
        operation="execve",
        command="/bin/sh",
        arguments_preview="-c echo hi",
        cwd=str(tmp_path),
    )

    runtime._handle_process_event(event)

    assert report.process_events == [event]
    assert hooks.persist_calls == [False]


def test_handle_file_event_appends_and_persists(tmp_path) -> None:
    runtime, report, hooks = _build_runtime()
    event = monitor.FileEvent(
        timestamp="2026-01-01T10:00:00.000",
        rel_time_s=0.1,
        path=str(tmp_path / "sample.txt"),
        operation="open",
        observer="strace",
        source="extension",
    )

    runtime._handle_file_event(event)

    assert report.file_events == [event]
    assert hooks.persist_calls == [False]


def test_capture_runtime_snapshot_returns_expected_shape(monkeypatch) -> None:
    _patch_facade(
        monkeypatch,
        parse_all_exthost_logs=lambda start_offsets=None: [
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand",
                timestamp="2026-01-01 10:00:00.500",
                source="log",
            ),
            monitor.ActivationEntry(
                extension_id="other.ext",
                activation_event="onStartupFinished",
                timestamp="2026-01-01 10:00:00.600",
                source="log",
            ),
        ],
        get_running_extensions=lambda page: [
            monitor.RunningExtension(
                extension_id="publisher.tool",
                activation_time_ms=12,
            )
        ],
    )

    runtime, _report, _hooks = _build_runtime()
    snapshot = runtime.capture_runtime_snapshot()

    assert set(snapshot.keys()) == {
        "target_activations",
        "target_running",
        "target_file_events",
        "target_network_events",
        "ui_blockers",
    }
    assert snapshot["target_activations"] == 1
    assert snapshot["target_running"] is True
    assert snapshot["target_file_events"] == 0
    assert snapshot["target_network_events"] == 0


# ---------------------------------------------------------------------------
# W11-3 — discovery-strategy callback emission
# ---------------------------------------------------------------------------


def test_stop_emits_all_three_strategies_when_all_succeed(
    monkeypatch, tmp_path
) -> None:
    """Strategy 1 finds an exthost-log activation, Strategy 2 returns a
    non-empty Running Extensions list, Strategy 3 merges in a brand-new
    activation entry. All three identifiers must reach the assembler."""

    log_file = tmp_path / "exthost.log"
    log_file.write_text("placeholder")

    strategy_one_entry = monitor.ActivationEntry(
        extension_id="publisher.tool",
        activation_event="onCommand:publisher.tool.run",
        timestamp="2026-01-01 10:00:00.500",
        source="log",
    )
    strategy_three_entry = monitor.ActivationEntry(
        extension_id="publisher.tool",
        activation_event="onView:publisher.view",
        timestamp="2026-01-01 10:00:01.000",
        source="output",
    )

    _patch_facade(
        monkeypatch,
        parse_all_exthost_logs=lambda start_offsets=None: [strategy_one_entry],
        find_exthost_logs=lambda: [log_file],
        get_running_extensions=lambda page: [
            monitor.RunningExtension(
                extension_id="publisher.tool", activation_time_ms=12
            )
        ],
        read_extension_host_output=lambda page=None: "extension host output",
        parse_activations_from_output=lambda output, monitoring_start=0.0: [
            strategy_three_entry,
        ],
    )

    runtime, _report, hooks = _build_runtime()
    runtime.start()
    runtime.stop()

    assert hooks.discovery_strategy_calls == [
        [
            "exthost_log_parse",
            "running_extensions_ui",
            "exthost_output_parse",
        ]
    ]


def test_stop_emits_empty_list_when_all_strategies_yield_no_entries(
    monkeypatch,
) -> None:
    """All three strategies execute without exception but return empty
    results; the callback still fires (so the assembler clears any
    stale value), with an empty list."""

    _patch_facade(monkeypatch)  # all defaults return empty results.

    runtime, _report, hooks = _build_runtime()
    runtime.start()
    runtime.stop()

    assert hooks.discovery_strategy_calls == [[]]


def test_stop_omits_strategy_three_when_output_parse_yields_no_new_entries(
    monkeypatch, tmp_path
) -> None:
    """If the exthost-output parse returns the same set already produced
    by Strategy 1 (i.e. no new entries after dedup-merge),
    ``exthost_output_parse`` must NOT be reported. Pins the producer's
    "yielded at least one *new* entry" semantics for Strategy 3."""

    log_file = tmp_path / "exthost.log"
    log_file.write_text("placeholder")
    activation = monitor.ActivationEntry(
        extension_id="publisher.tool",
        activation_event="onCommand:publisher.tool.run",
        timestamp="2026-01-01 10:00:00.500",
        source="log",
    )

    _patch_facade(
        monkeypatch,
        parse_all_exthost_logs=lambda start_offsets=None: [activation],
        find_exthost_logs=lambda: [log_file],
        # parse_activations_from_output returns the same activation; the
        # merge dedupes, so post_count == pre_count and Strategy 3 is
        # not credited.
        parse_activations_from_output=lambda output, monitoring_start=0.0: [activation],
        read_extension_host_output=lambda page=None: "extension host output",
    )

    runtime, _report, hooks = _build_runtime()
    runtime.start()
    runtime.stop()

    assert hooks.discovery_strategy_calls == [["exthost_log_parse"]]


def test_log_offsets_property_reflects_runtime_state(monkeypatch) -> None:
    """W11-1 transitional pin: facade reads ``_log_offsets`` via runtime."""

    expected = {"exthost.log": 1024}
    _patch_facade(monkeypatch, _snapshot_log_offsets=lambda: expected)

    runtime, _report, _hooks = _build_runtime()
    assert runtime.log_offsets == {}
    runtime.start()
    assert runtime.log_offsets == expected


# ---------------------------------------------------------------------------
# W11-4 — intermediate-state emission callback ordering
# ---------------------------------------------------------------------------


def test_stop_invokes_emit_intermediate_state_events_callback(monkeypatch) -> None:
    """W11-4: ``emit_intermediate_state_events`` fires exactly once per stop()."""

    _patch_facade(monkeypatch)

    runtime, _report, hooks = _build_runtime()
    runtime.start()
    runtime.stop()

    assert hooks.emit_intermediate_calls == 1


def test_stop_emits_intermediate_state_events_after_refresh(monkeypatch) -> None:
    """W11-4: ``emit_intermediate_state_events`` must run *after*
    ``refresh_derived_state`` so the emitted events reflect the
    post-reconcile ``verification_status`` literals
    (``activation_seen`` / ``target_log_seen``). Pinning the order at
    the runtime layer keeps this guarantee independent of the facade
    shim shape that W11-5 will collapse.
    """

    _patch_facade(monkeypatch)

    runtime, _report, hooks = _build_runtime()
    runtime.start()
    runtime.stop()

    # Filter to the two callbacks we care about; positional order matters.
    refresh_emit_order = [
        step for step in hooks.callback_order if step in {"refresh", "emit"}
    ]
    assert refresh_emit_order == ["refresh", "emit"]


def test_stop_without_start_still_emits_intermediate_state_events(monkeypatch) -> None:
    """W11-4: defensive ``stop()`` (without ``start()``) still drives the
    emission callback so partial test scaffolds do not silently drop the
    intermediate-state vocabulary."""

    _patch_facade(monkeypatch)

    runtime, _report, hooks = _build_runtime()
    runtime.stop()

    assert hooks.emit_intermediate_calls == 1
    assert hooks.refresh_calls == 1
