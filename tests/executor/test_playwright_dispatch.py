"""Direct unit coverage for the W12-4 ``entrypoint/dispatch.py`` module.

The orchestrator-level coverage in ``test_playwright_entrypoint.py`` runs
every dispatch path end-to-end through a fake-``deps`` SimpleNamespace.
This file complements that with focused unit tests for the helpers whose
contract is most easily reasoned about in isolation:

- ``PageRef`` mutation semantics (page rebind across module boundary)
- ``summarize_skipped_scenarios_if_needed`` 3-condition gate
- ``apply_extra_triggers_if_needed`` early-return paths
- ``finalize_monitor_report`` no-op when ``mon`` is None
- ``make_page_callbacks`` callback wiring (mon=None silent, mon=mon
  records both detected/dismissed)

These pin the helper-level contract so a future change can be unit-tested
without spinning up the full ``main()`` harness.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from executor.flows.playwright.entrypoint import dispatch as dispatch_mod
from executor.flows.playwright.entrypoint.dispatch import (
    PageRef,
    apply_extra_triggers_if_needed,
    finalize_monitor_report,
    make_page_callbacks,
    summarize_skipped_scenarios_if_needed,
)


class _StubReport:
    def __init__(self) -> None:
        self.trigger_plan_applied = False
        self.requested_scenarios: list[str] = []
        self.extra_trigger_failures: list[str] = []
        self.scenarios_run: list[str] = []
        self.print_summary_calls = 0
        self.saved_paths: list[str] = []

    def print_summary(self) -> None:
        self.print_summary_calls += 1

    def save(self, path: str) -> None:
        self.saved_paths.append(path)


class _StubMonitor:
    def __init__(self) -> None:
        self.report = _StubReport()
        self.page: Any = None
        self.recorded_events: list[tuple[str, str, str | None]] = []
        self.applied_plans: list[tuple[list[str] | None, str | None]] = []
        self.execution_results: list[Any] = []
        self.failed_scenarios: list[Any] = []
        self.runner_status: int | None = None
        self.stop_calls = 0

    def record_automation_event(
        self, kind: str, message: str, *, status: str | None = None, **_kw
    ) -> None:
        self.recorded_events.append((kind, message, status))

    def mark_trigger_plan_applied(
        self, *, scenarios: list[str] | None = None, trigger_path: str | None = None
    ) -> None:
        self.applied_plans.append((scenarios, trigger_path))
        self.report.trigger_plan_applied = True

    def record_execution_result(self, result) -> None:
        self.execution_results.append(result)

    def record_failed_scenarios(self, items) -> None:
        self.failed_scenarios.append(list(items))

    def stop(self) -> _StubReport:
        self.stop_calls += 1
        return self.report

    def set_runner_status(self, code: int) -> None:
        self.runner_status = code


# ---------------------------------------------------------------------------
# PageRef
# ---------------------------------------------------------------------------


def test_page_ref_holds_initial_value() -> None:
    page = object()
    ref = PageRef(page)
    assert ref.value is page


def test_page_ref_mutates_value_in_place() -> None:
    initial = object()
    replacement = object()
    ref = PageRef(initial)

    def _swap() -> None:
        ref.value = replacement

    _swap()
    assert ref.value is replacement


def test_page_ref_only_exposes_value_attribute() -> None:
    """``__slots__`` keeps the wrapper minimal — pin to forbid drift."""
    ref = PageRef(object())
    with pytest.raises(AttributeError):
        ref.extra_attr = "no"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# summarize_skipped_scenarios_if_needed
# ---------------------------------------------------------------------------


def _make_result(*, skipped: list, executed: list) -> SimpleNamespace:
    return SimpleNamespace(skipped_scenarios=skipped, executed_scenarios=executed)


@pytest.mark.parametrize("mode", ["layered_passes", "skip_automation", "demo", ""])
def test_summarize_returns_zero_for_non_selected_modes(mode: str) -> None:
    result = _make_result(
        skipped=[SimpleNamespace(name="x", reason_code="r")], executed=[]
    )
    assert summarize_skipped_scenarios_if_needed(mode, result) == 0


def test_summarize_returns_zero_when_no_skipped() -> None:
    result = _make_result(skipped=[], executed=[])
    assert summarize_skipped_scenarios_if_needed("selected_scenarios", result) == 0


def test_summarize_returns_zero_when_executed_is_truthy() -> None:
    """Some scenarios ran, so partial-skip is just info not a failure."""
    result = _make_result(
        skipped=[SimpleNamespace(name="b", reason_code="r")],
        executed=["a"],
    )
    assert summarize_skipped_scenarios_if_needed("selected_scenarios", result) == 0


def test_summarize_returns_one_when_all_skipped_in_selected_mode(capsys) -> None:
    result = _make_result(
        skipped=[
            SimpleNamespace(name="alpha", reason_code="missing_target"),
            SimpleNamespace(name="beta", reason_code="dependency_failed"),
        ],
        executed=[],
    )
    assert summarize_skipped_scenarios_if_needed("selected_scenarios", result) == 1
    out = capsys.readouterr().out
    assert "alpha: missing_target" in out
    assert "beta: dependency_failed" in out


def test_summarize_returns_one_when_all_skipped_in_single_mode() -> None:
    result = _make_result(
        skipped=[SimpleNamespace(name="solo", reason_code="reason")],
        executed=[],
    )
    assert summarize_skipped_scenarios_if_needed("single_scenario", result) == 1


# ---------------------------------------------------------------------------
# apply_extra_triggers_if_needed
# ---------------------------------------------------------------------------


def test_apply_extra_triggers_returns_zero_without_payload() -> None:
    page_ref = PageRef(object())
    args = SimpleNamespace(triggers=None)
    result = SimpleNamespace(extra_trigger_failures=[], requested_scenarios=[])
    deps = SimpleNamespace()
    rc = apply_extra_triggers_if_needed(
        page_ref,
        args,
        mon=None,
        trigger_payload=None,
        execution_result=result,
        deps=deps,
    )
    assert rc == 0
    assert result.extra_trigger_failures == []


def test_apply_extra_triggers_returns_zero_when_payload_has_stimulus_passes() -> None:
    """Layered-pass payloads run via ``run_stimulus_plan``, not extra triggers."""
    page_ref = PageRef(object())
    args = SimpleNamespace(triggers="/results/triggers.json")
    payload = SimpleNamespace(stimulus_passes=["pass1"], selected_scenarios=["s"])
    result = SimpleNamespace(extra_trigger_failures=[], requested_scenarios=[])
    deps = SimpleNamespace()
    rc = apply_extra_triggers_if_needed(
        page_ref,
        args,
        mon=None,
        trigger_payload=payload,
        execution_result=result,
        deps=deps,
    )
    assert rc == 0
    assert result.extra_trigger_failures == []


def test_layered_dispatch_marks_plan_before_stimulus_execution() -> None:
    """A partial report remains truthful when stimulus execution is interrupted."""
    mon = _StubMonitor()
    payload = SimpleNamespace(
        event_attempts=["attempt"],
        stimulus_passes=["pass"],
    )

    def interrupted_plan(*_args, **_kwargs):
        assert mon.report.trigger_plan_applied is True
        raise RuntimeError("interrupted after a finalized pass")

    deps = SimpleNamespace(
        stimulus=SimpleNamespace(
            AutomationExecutionResult=lambda **kwargs: SimpleNamespace(**kwargs),
            run_stimulus_plan=interrupted_plan,
        )
    )

    with pytest.raises(RuntimeError, match="interrupted after a finalized pass"):
        dispatch_mod.dispatch_execution(
            PageRef(object()),
            object(),
            SimpleNamespace(demo=False, triggers="/results/triggers.json"),
            mon,
            payload,
            ["coding_session"],
            "layered_passes",
            deps=deps,
        )

    assert mon.applied_plans == [(["coding_session"], "/results/triggers.json")]
    assert any(event[0] == "trigger_plan_applied" for event in mon.recorded_events)


def test_apply_extra_triggers_records_plan_and_runs_when_no_stimulus_passes(
    monkeypatch,
) -> None:
    page_ref = PageRef(object())
    args = SimpleNamespace(triggers="/results/t.json")
    payload = SimpleNamespace(stimulus_passes=[], selected_scenarios=["seed"])
    result = SimpleNamespace(extra_trigger_failures=[], requested_scenarios=["seed"])
    mon = _StubMonitor()
    deps = SimpleNamespace()

    captured: dict = {}

    def fake_run_extra_triggers_for_deps(
        page,
        payload_arg,
        *,
        deps,
        automation_event_recorder=None,
        verification_monitor=None,
    ):
        captured["page"] = page
        captured["payload"] = payload_arg
        captured["recorder_set"] = automation_event_recorder is not None
        captured["monitor_set"] = verification_monitor is mon
        return []  # no failures

    monkeypatch.setattr(
        dispatch_mod,
        "_run_extra_triggers_for_deps",
        fake_run_extra_triggers_for_deps,
    )

    rc = apply_extra_triggers_if_needed(
        page_ref,
        args,
        mon=mon,
        trigger_payload=payload,
        execution_result=result,
        deps=deps,
    )

    assert rc == 0
    assert captured["page"] is page_ref.value
    assert captured["payload"] is payload
    assert captured["recorder_set"] is True
    assert captured["monitor_set"] is True
    assert mon.applied_plans == [(["seed"], "/results/t.json")]
    assert mon.report.trigger_plan_applied is True
    assert any(ev[0] == "trigger_plan_applied" for ev in mon.recorded_events)


def test_apply_extra_triggers_returns_one_on_failures(monkeypatch) -> None:
    page_ref = PageRef(object())
    args = SimpleNamespace(triggers=None)
    payload = SimpleNamespace(stimulus_passes=[], selected_scenarios=["seed"])
    result = SimpleNamespace(extra_trigger_failures=[], requested_scenarios=["seed"])
    deps = SimpleNamespace()

    monkeypatch.setattr(
        dispatch_mod,
        "_run_extra_triggers_for_deps",
        lambda *a, **kw: ["uri:bad", "task:fail"],
    )

    rc = apply_extra_triggers_if_needed(
        page_ref,
        args,
        mon=None,
        trigger_payload=payload,
        execution_result=result,
        deps=deps,
    )
    assert rc == 1
    assert result.extra_trigger_failures == ["uri:bad", "task:fail"]


def test_apply_extra_triggers_does_not_remark_already_applied_plan(
    monkeypatch,
) -> None:
    """Pin: if ``mon.report.trigger_plan_applied`` is already True (the
    layered_passes / selected_scenarios / single_scenario branches mark
    it), the extra-triggers fallback must not re-mark the plan."""
    page_ref = PageRef(object())
    args = SimpleNamespace(triggers="/r/t.json")
    payload = SimpleNamespace(stimulus_passes=[], selected_scenarios=["s"])
    result = SimpleNamespace(extra_trigger_failures=[], requested_scenarios=["s"])
    mon = _StubMonitor()
    mon.report.trigger_plan_applied = True

    monkeypatch.setattr(
        dispatch_mod,
        "_run_extra_triggers_for_deps",
        lambda *a, **kw: [],
    )

    apply_extra_triggers_if_needed(
        page_ref,
        args,
        mon=mon,
        trigger_payload=payload,
        execution_result=result,
        deps=SimpleNamespace(),
    )

    assert mon.applied_plans == []  # not re-marked


# ---------------------------------------------------------------------------
# finalize_monitor_report
# ---------------------------------------------------------------------------


def test_finalize_is_noop_when_mon_is_none() -> None:
    """No-op + no exceptions when monitor wasn't started."""
    args = SimpleNamespace(report_path="/results/x.json")
    finalize_monitor_report(
        mon=None,
        execution_result=SimpleNamespace(),
        exit_code=0,
        args=args,
    )


def test_finalize_records_result_stops_and_saves() -> None:
    mon = _StubMonitor()
    args = SimpleNamespace(report_path="/results/run.json")
    result = SimpleNamespace(
        requested_scenarios=["a"],
        executed_scenarios=["a"],
        failed_scenarios=[],
        skipped_scenarios=[],
        extra_trigger_failures=[],
    )

    finalize_monitor_report(
        mon=mon,
        execution_result=result,
        exit_code=0,
        args=args,
    )

    assert mon.execution_results == [result]
    assert mon.runner_status == 0
    assert mon.stop_calls == 1
    assert mon.report.print_summary_calls == 1
    assert mon.report.saved_paths == ["/results/run.json"]


def test_finalize_passes_through_nonzero_exit_code() -> None:
    """``runner_exit_code`` (W11-3) must reach the report before save."""
    mon = _StubMonitor()
    args = SimpleNamespace(report_path="/results/fail.json")
    result = SimpleNamespace(
        requested_scenarios=[],
        executed_scenarios=[],
        failed_scenarios=["x"],
        skipped_scenarios=[],
        extra_trigger_failures=[],
    )

    finalize_monitor_report(
        mon=mon,
        execution_result=result,
        exit_code=1,
        args=args,
    )

    assert mon.runner_status == 1


def test_finalize_is_idempotent() -> None:
    """W22: callable from both the normal path and the ``finally`` net without
    finalizing twice — ``mon.stop()`` + ``save`` run exactly once."""
    mon = _StubMonitor()
    args = SimpleNamespace(report_path="/results/run.json")
    result = SimpleNamespace(
        requested_scenarios=[],
        executed_scenarios=[],
        failed_scenarios=[],
        skipped_scenarios=[],
        extra_trigger_failures=[],
    )

    finalize_monitor_report(mon=mon, execution_result=result, exit_code=0, args=args)
    finalize_monitor_report(mon=mon, execution_result=result, exit_code=0, args=args)

    assert mon.stop_calls == 1
    assert mon.report.saved_paths == ["/results/run.json"]


def test_finalize_tolerates_none_execution_result() -> None:
    """W22: when an interrupt/exception fires before the stimulus produced a
    result, ``execution_result`` is None — the result-recording step is
    skipped but ``stop()`` (activation parse) + ``save`` still run."""
    mon = _StubMonitor()
    args = SimpleNamespace(report_path="/results/interrupted.json")

    finalize_monitor_report(mon=mon, execution_result=None, exit_code=143, args=args)

    assert mon.execution_results == []  # record skipped (no result)
    assert mon.stop_calls == 1  # activation parse still happens
    assert mon.report.saved_paths == ["/results/interrupted.json"]
    assert mon.runner_status == 143


# ---------------------------------------------------------------------------
# make_page_callbacks
# ---------------------------------------------------------------------------


def test_on_page_reloaded_mutates_page_ref_and_monitor_page() -> None:
    page_ref = PageRef(object())
    mon = _StubMonitor()
    on_reload, _probe = make_page_callbacks(mon, page_ref, deps=SimpleNamespace())

    new_page = object()
    on_reload(new_page)

    assert page_ref.value is new_page
    assert mon.page is new_page


def test_on_page_reloaded_safe_when_mon_is_none() -> None:
    page_ref = PageRef(object())
    on_reload, _probe = make_page_callbacks(None, page_ref, deps=SimpleNamespace())

    new_page = object()
    on_reload(new_page)

    assert page_ref.value is new_page  # mon=None path stays silent + safe


def test_probe_ui_blocker_is_noop_when_mon_is_none() -> None:
    """``mon is None`` short-circuit must not even touch ``deps.editor``."""
    page_ref = PageRef(object())
    deps = SimpleNamespace()  # no .editor attribute on purpose
    _on_reload, probe = make_page_callbacks(None, page_ref, deps=deps)

    probe(object(), "scenario-x")  # would AttributeError without the guard


def test_probe_ui_blocker_records_detected_and_dismissed_when_text_present() -> None:
    page_ref = PageRef(object())
    mon = _StubMonitor()
    deps = SimpleNamespace(
        editor=SimpleNamespace(
            _dismiss_notification=lambda page: "Python extension installed"
        ),
    )
    _on_reload, probe = make_page_callbacks(mon, page_ref, deps=deps)

    probe(page_ref.value, "coding_session")

    kinds = [ev[0] for ev in mon.recorded_events]
    assert kinds == ["ui_blocker_detected", "ui_blocker_dismissed"]


def test_probe_ui_blocker_silent_when_dismiss_returns_empty() -> None:
    page_ref = PageRef(object())
    mon = _StubMonitor()
    deps = SimpleNamespace(
        editor=SimpleNamespace(_dismiss_notification=lambda page: ""),
    )
    _on_reload, probe = make_page_callbacks(mon, page_ref, deps=deps)

    probe(page_ref.value, "coding_session")
    assert mon.recorded_events == []


def test_probe_ui_blocker_swallows_known_exceptions() -> None:
    """Playwright/runtime/value errors during probe must not bubble up;
    a flaky probe should never crash the dispatch loop."""
    page_ref = PageRef(object())
    mon = _StubMonitor()

    def raise_runtime(page):
        raise RuntimeError("simulated dismiss failure")

    deps = SimpleNamespace(
        editor=SimpleNamespace(_dismiss_notification=raise_runtime),
    )
    _on_reload, probe = make_page_callbacks(mon, page_ref, deps=deps)

    probe(page_ref.value, "coding_session")  # must not raise
    assert mon.recorded_events == []
