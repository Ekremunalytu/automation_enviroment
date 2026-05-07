"""Composition pins for ``ExtensionMonitor`` (W11-5 collapsed shape).

W11-5 collapsed the transitional ``ExtensionMonitor`` facade into a
thin composition over three collaborators (``MonitorRuntime``,
``ReportAssembler``, ``ScenarioAccountant``). The pre-W11-5 version of
this file pinned bound-method-identity invariants between the facade
and the runtime — every runtime callback was a facade ``_*`` shim. The
W11-5 collapse deletes those shims; runtime callbacks now bind
directly to collaborator methods. These tests pin the new shape:

* the three collaborators are composed at construction and share the
  same ``ActivationReport`` instance;
* runtime callbacks point straight at collaborator methods (no shim
  layer in between);
* the keyword arguments ``runtime`` / ``assembler`` / ``accountant``
  let tests inject pre-built fakes;
* public-API method calls (``start``, ``stop``,
  ``attach_runtime_tracers``, ``capture_runtime_snapshot``,
  ``set_runner_status``, ``record_event_attempt_*``,
  ``record_failed_scenarios``, ``record_scenario_event``,
  ``record_stimulus_pass_event``, ``record_prerequisite_result``,
  ``mark_trigger_plan_*``) forward to the right collaborator;
* ``page`` is a property whose setter writes through to the runtime;
* ``apply_trigger_payload`` / ``set_trigger_execution_mode`` /
  ``record_automation_event`` / ``verify_target_reaction`` exercise
  the facade-owned bodies (or thin forwards) end-to-end.

A final sanity test asserts that an unpatched ``ExtensionMonitor``
holds three real collaborator instances — guarding against a future
constructor regression that silently elides one of them.
"""

from __future__ import annotations

from typing import Any, ClassVar

from executor.flows.playwright.monitor.lifecycle import ExtensionMonitor
from executor.flows.playwright.monitor.report_assembler import ReportAssembler
from executor.flows.playwright.monitor.runtime_state import MonitorRuntime
from executor.flows.playwright.monitor.scenario_accountant import ScenarioAccountant
from executor.flows.playwright.monitor.types import ActivationReport


class _DummyPage:
    pass


class _RecordingRuntime:
    """Captures every runtime call so composition wiring can be asserted."""

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
        set_discovery_strategies: Any,
        emit_intermediate_state_events: Any,
    ) -> None:
        self._page = page
        self.report = report
        self.persist = persist
        self.record_automation_event = record_automation_event
        self.finalize_scenarios = finalize_scenarios
        self.append_activation_log_entries = append_activation_log_entries
        self.refresh_derived_state = refresh_derived_state
        self.set_discovery_strategies = set_discovery_strategies
        self.emit_intermediate_state_events = emit_intermediate_state_events
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.log_offsets: dict[str, int] = {}
        self.snapshot_return: dict[str, int | bool] = {
            "target_activations": 7,
            "target_running": True,
            "target_file_events": 1,
            "target_network_events": 2,
            "ui_blockers": 0,
        }

    @property
    def page(self) -> Any:
        return self._page

    @page.setter
    def page(self, value: Any) -> None:
        self._page = value

    def start(self) -> None:
        self.calls.append(("start", ()))

    def stop(self) -> ActivationReport:
        self.calls.append(("stop", ()))
        return self.report

    def attach_runtime_tracers(self) -> None:
        self.calls.append(("attach_runtime_tracers", ()))

    def capture_runtime_snapshot(self) -> dict[str, int | bool]:
        self.calls.append(("capture_runtime_snapshot", ()))
        return self.snapshot_return


class _RecordingAssembler:
    def __init__(self, *, report: ActivationReport) -> None:
        self.report = report
        self.persist_calls: list[bool] = []
        self.refresh_calls: int = 0
        self.discovery_strategies_calls: list[list[str]] = []
        self.runner_status_calls: list[int] = []

    def persist(self, force: bool) -> None:
        self.persist_calls.append(force)

    def refresh_derived_state(self) -> None:
        self.refresh_calls += 1

    def set_discovery_strategies(self, strategies: Any) -> None:
        self.discovery_strategies_calls.append(list(strategies))

    def set_runner_status(self, exit_code: int) -> None:
        self.runner_status_calls.append(exit_code)


class _RecordingAccountant:
    def __init__(self, *, report: ActivationReport) -> None:
        self.report = report
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.verify_return: bool = True

    def _track(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))

    def mark_trigger_plan_applied(self, **kwargs: Any) -> None:
        self._track("mark_trigger_plan_applied", **kwargs)

    def mark_trigger_plan_missing(self, trigger_path: str = "") -> None:
        self._track("mark_trigger_plan_missing", trigger_path)

    def record_failed_scenarios(self, failed_scenarios: list[str]) -> None:
        self._track("record_failed_scenarios", failed_scenarios)

    def record_execution_result(self, result: Any) -> None:
        self._track("record_execution_result", result)

    def record_stimulus_pass_event(self, *args: Any, **kwargs: Any) -> None:
        self._track("record_stimulus_pass_event", *args, **kwargs)

    def record_prerequisite_result(self, *args: Any, **kwargs: Any) -> None:
        self._track("record_prerequisite_result", *args, **kwargs)

    def record_event_attempt_start(self, *args: Any, **kwargs: Any) -> None:
        self._track("record_event_attempt_start", *args, **kwargs)

    def record_event_attempt_end(self, *args: Any, **kwargs: Any) -> None:
        self._track("record_event_attempt_end", *args, **kwargs)

    def record_scenario_event(self, *args: Any, **kwargs: Any) -> None:
        self._track("record_scenario_event", *args, **kwargs)

    def finalize_running_scenarios(self) -> None:
        self._track("finalize_running_scenarios")

    def append_activation_log_entries(self) -> None:
        self._track("append_activation_log_entries")

    def emit_intermediate_state_events(self) -> None:
        self._track("emit_intermediate_state_events")

    def verify_target_reaction(self, *args: Any, **kwargs: Any) -> bool:
        self._track("verify_target_reaction", *args, **kwargs)
        return self.verify_return


def _make_facade_with_fakes(
    *,
    page: Any | None = None,
    target_extension_id: str = "publisher.tool",
) -> tuple[
    ExtensionMonitor,
    _RecordingRuntime,
    _RecordingAssembler,
    _RecordingAccountant,
]:
    page = page or _DummyPage()
    report = ActivationReport(target_extension_id=target_extension_id)
    assembler = _RecordingAssembler(report=report)
    accountant = _RecordingAccountant(report=report)
    runtime_holder: dict[str, _RecordingRuntime] = {}

    def runtime_factory(**kwargs: Any) -> _RecordingRuntime:
        runtime_holder["instance"] = _RecordingRuntime(**kwargs)
        return runtime_holder["instance"]

    # We can't pre-build the runtime (it needs the accountant/assembler
    # callbacks) so we let the facade construct it via the kwarg path
    # below. Use the standard ctor with assembler/accountant injected
    # and let the facade build a real MonitorRuntime — but for shim-free
    # composition we want a recording runtime, so pass through.
    mon = ExtensionMonitor(
        page,
        target_extension_id=target_extension_id,
        report=report,
        assembler=assembler,  # type: ignore[arg-type]
        accountant=accountant,  # type: ignore[arg-type]
        runtime=None,
    )
    # Replace the auto-built MonitorRuntime with a recording one that
    # uses the *exact* callbacks the facade computed.
    real_runtime = mon._runtime
    rec_runtime = _RecordingRuntime(
        page=real_runtime._page,
        report=real_runtime._report,
        persist=real_runtime._persist,
        record_automation_event=real_runtime._record_automation,
        finalize_scenarios=real_runtime._finalize_scenarios,
        append_activation_log_entries=real_runtime._append_activation_log_entries,
        refresh_derived_state=real_runtime._refresh_derived_state,
        set_discovery_strategies=real_runtime._set_discovery_strategies,
        emit_intermediate_state_events=real_runtime._emit_intermediate_state_events,
    )
    mon._runtime = rec_runtime  # type: ignore[assignment]
    return mon, rec_runtime, assembler, accountant


# ---------------------------------------------------------------------------
# Composition contract
# ---------------------------------------------------------------------------


def test_facade_composes_three_collaborators_sharing_one_report() -> None:
    page = _DummyPage()
    mon = ExtensionMonitor(page=page, target_extension_id="publisher.tool")

    assert isinstance(mon._runtime, MonitorRuntime)
    assert isinstance(mon._assembler, ReportAssembler)
    assert isinstance(mon._scenario_accountant, ScenarioAccountant)
    # Same ActivationReport instance flows through all three.
    assert mon.report is mon._assembler._report
    assert mon.report is mon._scenario_accountant._report
    assert mon.report is mon._runtime._report


def test_facade_runtime_callbacks_bind_directly_to_collaborator_methods() -> None:
    """No shim layer between runtime and assembler/accountant — runtime
    callbacks are bound methods of the collaborators themselves."""

    mon = ExtensionMonitor(page=_DummyPage(), target_extension_id="t")

    assert mon._runtime._persist == mon._assembler.persist
    assert mon._runtime._refresh_derived_state == mon._assembler.refresh_derived_state
    assert (
        mon._runtime._set_discovery_strategies
        == mon._assembler.set_discovery_strategies
    )
    assert (
        mon._runtime._finalize_scenarios
        == mon._scenario_accountant.finalize_running_scenarios
    )
    assert (
        mon._runtime._append_activation_log_entries
        == mon._scenario_accountant.append_activation_log_entries
    )
    assert (
        mon._runtime._emit_intermediate_state_events
        == mon._scenario_accountant.emit_intermediate_state_events
    )
    # record_automation_event stays on the facade (orchestration ham);
    # both runtime and accountant get it as a callback.
    assert mon._runtime._record_automation == mon.record_automation_event
    assert (
        mon._scenario_accountant._record_automation_event == mon.record_automation_event
    )


def test_facade_accepts_pre_built_report_kwarg() -> None:
    """The ``report`` kwarg lets a caller pin the underlying
    ``ActivationReport`` instance instead of letting the facade build a
    fresh one from ``target_extension_id``."""

    custom = ActivationReport(target_extension_id="custom.target")
    custom.trigger_plan_path = "/seed.json"

    mon = ExtensionMonitor(page=_DummyPage(), report=custom)

    assert mon.report is custom
    assert mon.report.target_extension_id == "custom.target"
    assert mon.report.trigger_plan_path == "/seed.json"
    # Default-built collaborators must observe the injected report.
    assert mon._assembler._report is custom
    assert mon._scenario_accountant._report is custom
    assert mon._runtime._report is custom


def test_facade_accepts_pre_built_collaborator_injection() -> None:
    page = _DummyPage()
    report = ActivationReport(target_extension_id="t")
    assembler = ReportAssembler(report=report, report_path=None)
    accountant = ScenarioAccountant(
        report=report,
        record_automation_event=lambda *a, **kw: None,
        persist=assembler.persist,
    )

    mon = ExtensionMonitor(
        page=page,
        target_extension_id="t",
        report=report,
        assembler=assembler,
        accountant=accountant,
    )

    assert mon.report is report
    assert mon._assembler is assembler
    assert mon._scenario_accountant is accountant


# ---------------------------------------------------------------------------
# Page property
# ---------------------------------------------------------------------------


def test_facade_page_property_reads_runtime() -> None:
    page = _DummyPage()
    mon = ExtensionMonitor(page=page, target_extension_id="t")

    assert mon.page is page
    assert mon._runtime.page is page


def test_facade_page_setter_writes_through_to_runtime() -> None:
    mon = ExtensionMonitor(page=_DummyPage(), target_extension_id="t")
    new_page = _DummyPage()

    mon.page = new_page

    assert mon.page is new_page
    assert mon._runtime.page is new_page


# ---------------------------------------------------------------------------
# Public-API forwards
# ---------------------------------------------------------------------------


def test_facade_lifecycle_methods_forward_to_runtime() -> None:
    mon, runtime, _assembler, _accountant = _make_facade_with_fakes()

    mon.start()
    mon.attach_runtime_tracers()
    snapshot = mon.capture_runtime_snapshot()
    report = mon.stop()

    names = [name for name, _ in runtime.calls]
    assert names == [
        "start",
        "attach_runtime_tracers",
        "capture_runtime_snapshot",
        "stop",
    ]
    assert snapshot == runtime.snapshot_return
    assert report is mon.report


def test_facade_context_manager_runs_start_and_stop() -> None:
    mon, runtime, _assembler, _accountant = _make_facade_with_fakes()

    with mon:
        pass

    names = [name for name, _ in runtime.calls]
    assert names == ["start", "stop"]


def test_facade_set_runner_status_forwards_to_assembler() -> None:
    mon, _runtime, assembler, _accountant = _make_facade_with_fakes()

    mon.set_runner_status(0)
    mon.set_runner_status(2)

    assert assembler.runner_status_calls == [0, 2]


def test_facade_trigger_plan_methods_forward_to_accountant() -> None:
    mon, _runtime, _assembler, accountant = _make_facade_with_fakes()

    mon.mark_trigger_plan_applied(scenarios=["s1"], trigger_path="/t.json")
    mon.mark_trigger_plan_missing("/t.json")

    names = [call[0] for call in accountant.calls]
    assert names == ["mark_trigger_plan_applied", "mark_trigger_plan_missing"]


def test_facade_failed_scenarios_and_execution_result_forward_to_accountant() -> None:
    mon, _runtime, _assembler, accountant = _make_facade_with_fakes()

    mon.record_failed_scenarios(["a"])
    mon.record_execution_result(object())

    names = [call[0] for call in accountant.calls]
    assert names == ["record_failed_scenarios", "record_execution_result"]


def test_facade_event_attempt_methods_forward_to_accountant() -> None:
    mon, _runtime, _assembler, accountant = _make_facade_with_fakes()

    mon.record_event_attempt_start("att1", pass_name="pass1")  # noqa: S106
    mon.record_event_attempt_end(
        "att1",
        status="verified",
        pass_name="pass1",  # noqa: S106
        trigger_method_used="cmd",
        result_details="ok",
    )

    names = [call[0] for call in accountant.calls]
    assert names == ["record_event_attempt_start", "record_event_attempt_end"]
    end_kwargs = accountant.calls[1][2]
    assert end_kwargs["status"] == "verified"
    assert end_kwargs["trigger_method_used"] == "cmd"


def test_facade_scenario_stimulus_prerequisite_forwards_to_accountant() -> None:
    mon, _runtime, _assembler, accountant = _make_facade_with_fakes()

    mon.record_scenario_event("start", "s1")
    mon.record_stimulus_pass_event("start", "p1", label="Pass")
    mon.record_prerequisite_result("ext", status="completed")

    names = [call[0] for call in accountant.calls]
    assert names == [
        "record_scenario_event",
        "record_stimulus_pass_event",
        "record_prerequisite_result",
    ]


def test_facade_verify_target_reaction_forwards_with_runtime_log_offsets() -> None:
    mon, runtime, _assembler, accountant = _make_facade_with_fakes()
    runtime.log_offsets = {"exthost-1.log": 42}
    accountant.verify_return = True

    result = mon.verify_target_reaction(
        {"target_activations": 0},
        capability="cap",
        trigger_label="trig",
    )

    assert result is True
    assert accountant.calls[-1][0] == "verify_target_reaction"
    args = accountant.calls[-1][1]
    assert args[1] == {"exthost-1.log": 42}


# ---------------------------------------------------------------------------
# Facade-owned bodies
# ---------------------------------------------------------------------------


def test_facade_apply_trigger_payload_persists_force_true() -> None:
    mon, _runtime, assembler, _accountant = _make_facade_with_fakes()

    class _Payload:
        scenario_filter: ClassVar[list[str]] = []
        execution_mode: str = ""
        trigger_path: str = ""
        triggers: ClassVar[dict[str, Any]] = {}

    mon.apply_trigger_payload(_Payload())

    assert assembler.persist_calls and assembler.persist_calls[-1] is True


def test_facade_set_trigger_execution_mode_persists_force_false() -> None:
    mon, _runtime, assembler, _accountant = _make_facade_with_fakes()

    mon.set_trigger_execution_mode("  parallel  ")

    assert mon.report.trigger_execution_mode == "parallel"
    assert assembler.persist_calls and assembler.persist_calls[-1] is False


def test_facade_record_automation_event_appends_log_entry_and_persists() -> None:
    mon, _runtime, assembler, _accountant = _make_facade_with_fakes()
    initial = len(mon.report.log_entries)

    mon.record_automation_event("scenario", "started", status="running")

    assert len(mon.report.log_entries) == initial + 1
    last = mon.report.log_entries[-1]
    assert last.kind == "scenario"
    assert last.message == "started"
    assert last.stream == "automation"
    assert assembler.persist_calls and assembler.persist_calls[-1] is False


def test_facade_record_automation_event_routes_ui_blockers_to_ui_stream() -> None:
    mon, _runtime, _assembler, _accountant = _make_facade_with_fakes()

    mon.record_automation_event("ui_blocker", "blocked")

    assert mon.report.log_entries[-1].stream == "ui_blockers"


# ---------------------------------------------------------------------------
# Sanity guard: unpatched facade really holds three real collaborators
# ---------------------------------------------------------------------------


def test_facade_unpatched_holds_three_real_collaborator_instances() -> None:
    mon = ExtensionMonitor(page=_DummyPage(), target_extension_id="t")

    assert isinstance(mon._runtime, MonitorRuntime)
    assert isinstance(mon._assembler, ReportAssembler)
    assert isinstance(mon._scenario_accountant, ScenarioAccountant)
