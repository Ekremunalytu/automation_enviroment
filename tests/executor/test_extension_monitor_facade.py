"""Facade delegation pins for ``ExtensionMonitor`` (W11-1 transitional).

W11-1 splits the runtime state machine into ``MonitorRuntime`` and
keeps ``ExtensionMonitor`` as a transitional facade with delegation
stubs for ``start``/``stop``/``attach_runtime_tracers``/
``capture_runtime_snapshot`` plus ``_handle_*_event`` shims. These
tests pin the facade's wiring: that constructing the facade builds a
``MonitorRuntime`` with the right callbacks bound to the facade's
own methods, and that each public-surface call forwards to the
runtime collaborator.

Once W11-5 collapses the facade into a thin composition (≤200 LoC,
no delegation stubs), these tests become a regression net for the
new shape — the assertions on `_handle_*_event` and `_log_offsets`
should fail (signaling the cleanup landed) and need rewriting against
the new surface. Mark them with the W11-5 cross-ref.
"""

from __future__ import annotations

from typing import Any

from executor.flows.playwright import monitor
from executor.flows.playwright import monitor_lifecycle
from executor.flows.playwright.monitor_lifecycle import ExtensionMonitor
from executor.flows.playwright.monitor_report_assembler import ReportAssembler
from executor.flows.playwright.monitor_runtime_state import MonitorRuntime
from executor.flows.playwright.monitor_types import ActivationReport


class _DummyPage:
    pass


class _RecordingRuntime:
    """Minimal stand-in for ``MonitorRuntime`` that captures every call."""

    last_instance: _RecordingRuntime | None = None

    def __init__(
        self,
        *,
        page: Any,
        report: ActivationReport,
        persist: Any,
        record_automation_event: Any,
        finalize_scenarios: Any,
        append_activation_log_entries: Any,
        refresh_derived_state: Any,
    ) -> None:
        self.page = page
        self.report = report
        self.persist = persist
        self.record_automation_event = record_automation_event
        self.finalize_scenarios = finalize_scenarios
        self.append_activation_log_entries = append_activation_log_entries
        self.refresh_derived_state = refresh_derived_state
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self._log_offsets: dict[str, int] = {}
        self.start_return: Any = None
        self.attach_return: Any = None
        self.stop_return: ActivationReport = report
        self.snapshot_return: dict[str, int | bool] = {
            "target_activations": 7,
            "target_running": True,
            "target_file_events": 1,
            "target_network_events": 2,
            "ui_blockers": 0,
        }
        _RecordingRuntime.last_instance = self

    @property
    def log_offsets(self) -> dict[str, int]:
        return self._log_offsets

    def start(self) -> None:
        self.calls.append(("start", ()))
        return self.start_return

    def stop(self) -> ActivationReport:
        self.calls.append(("stop", ()))
        return self.stop_return

    def attach_runtime_tracers(self) -> None:
        self.calls.append(("attach_runtime_tracers", ()))
        return self.attach_return

    def capture_runtime_snapshot(self) -> dict[str, int | bool]:
        self.calls.append(("capture_runtime_snapshot", ()))
        return self.snapshot_return

    def _handle_network_event(self, event: Any) -> None:
        self.calls.append(("_handle_network_event", (event,)))

    def _handle_process_event(self, event: Any) -> None:
        self.calls.append(("_handle_process_event", (event,)))

    def _handle_file_event(self, event: Any) -> None:
        self.calls.append(("_handle_file_event", (event,)))


def _patch_runtime(monkeypatch) -> type[_RecordingRuntime]:
    monkeypatch.setattr(monitor_lifecycle, "MonitorRuntime", _RecordingRuntime)
    _RecordingRuntime.last_instance = None
    return _RecordingRuntime


def test_facade_init_constructs_runtime_with_facade_callbacks(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    page = _DummyPage()
    mon = ExtensionMonitor(page=page, target_extension_id="publisher.tool")

    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    assert runtime.page is page
    assert runtime.report is mon.report
    # The five facade callbacks must be bound methods of this exact facade.
    assert runtime.persist == mon._persist_report
    assert runtime.record_automation_event == mon.record_automation_event
    assert runtime.finalize_scenarios == mon._finalize_running_scenarios
    assert runtime.append_activation_log_entries == mon._append_activation_log_entries
    assert runtime.refresh_derived_state == mon._refresh_derived_report_state


def test_facade_start_delegates_to_runtime(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    mon.start()

    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    assert ("start", ()) in runtime.calls


def test_facade_stop_returns_runtime_result(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    sentinel = ActivationReport(target_extension_id="other")
    runtime.stop_return = sentinel

    returned = mon.stop()

    assert returned is sentinel
    assert ("stop", ()) in runtime.calls


def test_facade_attach_runtime_tracers_delegates_to_runtime(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    mon.attach_runtime_tracers()

    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    assert ("attach_runtime_tracers", ()) in runtime.calls


def test_facade_capture_runtime_snapshot_returns_runtime_dict(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    snapshot = mon.capture_runtime_snapshot()

    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    assert ("capture_runtime_snapshot", ()) in runtime.calls
    assert snapshot == runtime.snapshot_return


def test_facade_log_offsets_property_reads_runtime(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    runtime._log_offsets = {"exthost.log": 4242}

    assert mon._log_offsets == {"exthost.log": 4242}


def test_facade_handle_event_shims_forward_to_runtime(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())

    network_event = monitor.NetworkEvent(
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
    process_event = monitor.ProcessEvent(
        timestamp="2026-01-01T10:00:00.500",
        rel_time_s=0.5,
        pid=4242,
        ppid=1,
        operation="execve",
    )
    file_event = monitor.FileEvent(
        timestamp="2026-01-01T10:00:00.700",
        rel_time_s=0.7,
        path="/sandbox/file",
        operation="open",
        observer="strace",
    )

    mon._handle_network_event(network_event)
    mon._handle_process_event(process_event)
    mon._handle_file_event(file_event)

    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    kinds = [name for name, _args in runtime.calls]
    assert kinds == [
        "_handle_network_event",
        "_handle_process_event",
        "_handle_file_event",
    ]
    # Forwarded payload identity preserved.
    assert runtime.calls[0][1] == (network_event,)
    assert runtime.calls[1][1] == (process_event,)
    assert runtime.calls[2][1] == (file_event,)


def test_facade_context_manager_round_trip(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    page = _DummyPage()
    with ExtensionMonitor(page=page) as mon:
        assert isinstance(mon, ExtensionMonitor)
        assert mon.page is page

    runtime = _RecordingRuntime.last_instance
    assert runtime is not None
    assert ("start", ()) in runtime.calls
    assert ("stop", ()) in runtime.calls


def test_facade_runtime_uses_real_class_when_unpatched() -> None:
    """Sanity guard: without the monkeypatch the facade composes the real class.

    Catches accidental import drift in W11-5 if the facade ever stops
    importing ``MonitorRuntime`` directly from
    ``monitor_runtime_state``.
    """

    mon = ExtensionMonitor(page=_DummyPage())
    assert isinstance(mon._runtime, MonitorRuntime)


# ---------------------------------------------------------------------------
# W11-2 — ReportAssembler delegation pins
#
# These cases pin that the facade composes a ``ReportAssembler``, that the
# transitional ``_refresh_derived_report_state`` / ``_persist_report``
# shims forward to it, and that runtime callbacks reach the assembler
# *through* those shims (so the W11-1 bound-method-identity assertions
# above keep their meaning until W11-5 collapses the facade).
# ---------------------------------------------------------------------------


class _RecordingAssembler:
    """Minimal stand-in for ``ReportAssembler`` that captures every call."""

    last_instance: _RecordingAssembler | None = None

    def __init__(self, *, report: ActivationReport, report_path: Any) -> None:
        self.report = report
        self.report_path = report_path
        self.refresh_calls: int = 0
        self.persist_calls: list[bool] = []
        _RecordingAssembler.last_instance = self

    def refresh_derived_state(self) -> None:
        self.refresh_calls += 1

    def persist(self, force: bool) -> None:
        self.persist_calls.append(force)


def _patch_assembler(monkeypatch) -> type[_RecordingAssembler]:
    monkeypatch.setattr(monitor_lifecycle, "ReportAssembler", _RecordingAssembler)
    _RecordingAssembler.last_instance = None
    return _RecordingAssembler


def test_facade_init_constructs_assembler_with_shared_report(monkeypatch) -> None:
    _patch_assembler(monkeypatch)
    _patch_runtime(monkeypatch)

    page = _DummyPage()
    mon = ExtensionMonitor(
        page=page,
        report_path="/tmp/r.json",  # noqa: S108 — never written, just shape pin
        target_extension_id="publisher.tool",
    )

    assembler = _RecordingAssembler.last_instance
    assert assembler is not None
    # Same ActivationReport instance reaches the assembler (the W11-1
    # facade and runtime invariant: all three share one report).
    assert assembler.report is mon.report
    # Path is the Path-coerced value the facade owns; the assembler
    # captures it once and never re-resolves.
    assert assembler.report_path == mon.report_path


def test_facade_persist_shim_delegates_to_assembler(monkeypatch) -> None:
    _patch_assembler(monkeypatch)
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    assembler = _RecordingAssembler.last_instance
    assert assembler is not None

    mon._persist_report(force=True)
    mon._persist_report(force=False)

    assert assembler.persist_calls == [True, False]


def test_facade_refresh_shim_delegates_to_assembler(monkeypatch) -> None:
    _patch_assembler(monkeypatch)
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    assembler = _RecordingAssembler.last_instance
    assert assembler is not None

    mon._refresh_derived_report_state()
    mon._refresh_derived_report_state()

    assert assembler.refresh_calls == 2


def test_facade_runtime_callback_reaches_assembler_through_shim(
    monkeypatch,
) -> None:
    """End-to-end pin: runtime.persist invocation lands on the assembler.

    The runtime holds ``mon._persist_report`` as the persist callback
    (W11-1 invariant). After W11-2 that bound method is a one-line shim
    that delegates to the assembler. Calling through the runtime
    callback must transitively reach ``assembler.persist``.
    """

    _patch_assembler(monkeypatch)
    _patch_runtime(monkeypatch)

    mon = ExtensionMonitor(page=_DummyPage())
    runtime = _RecordingRuntime.last_instance
    assembler = _RecordingAssembler.last_instance
    assert runtime is not None and assembler is not None
    # The runtime captured the facade's bound _persist_report — pin
    # the W11-1 identity invariant alongside the new chain.
    assert runtime.persist == mon._persist_report
    assert runtime.refresh_derived_state == mon._refresh_derived_report_state

    # Invoking through the runtime-held reference must hit the assembler.
    runtime.persist(True)
    runtime.refresh_derived_state()

    assert assembler.persist_calls == [True]
    assert assembler.refresh_calls == 1


def test_facade_uses_real_assembler_when_unpatched() -> None:
    """Sanity guard parallel to ``test_facade_runtime_uses_real_class…``.

    Catches accidental import drift if the facade ever stops importing
    ``ReportAssembler`` directly from ``monitor_report_assembler``.
    """

    mon = ExtensionMonitor(page=_DummyPage())
    assert isinstance(mon._assembler, ReportAssembler)
