from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

from playwright.sync_api import Error as PlaywrightError  # noqa: E402

import automation  # noqa: E402
import vscode  # noqa: E402


class _DummyContext:
    def is_closed(self) -> bool:
        return False


class DummyPage:
    def __init__(self) -> None:
        self.context = _DummyContext()

    def wait_for_timeout(self, timeout_ms: int) -> None:
        _ = timeout_ms

    def is_closed(self) -> bool:
        return False

    def wait_for_function(self, expression: str, *, timeout: int = 0) -> None:
        _ = expression, timeout


def test_run_all_scenarios_returns_failed_names(monkeypatch) -> None:
    calls: list[str] = []

    def scenario_ok(page) -> None:
        _ = page
        calls.append("ok")

    def scenario_fail(page) -> None:
        _ = page
        raise RuntimeError("expected failure")

    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="scenario_ok",
                handler=scenario_ok,
                intent="ok",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            ),
            automation.ScenarioSpec(
                name="scenario_fail",
                handler=scenario_fail,
                intent="fail",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            ),
        ],
    )
    monkeypatch.setattr(
        automation,
        "_recover_ui_state",
        lambda page: calls.append("recover"),
    )
    monkeypatch.setattr(
        automation,
        "_cleanup_between_scenarios",
        lambda page: calls.append("cleanup"),
    )

    result = automation.run_all_scenarios(DummyPage(), shuffle=False)

    assert result.requested_scenarios == ["scenario_ok", "scenario_fail"]
    assert result.executed_scenarios == ["scenario_ok", "scenario_fail"]
    assert result.failed_scenarios == ["scenario_fail"]
    assert calls.count("cleanup") == 2
    assert "recover" in calls


def test_run_all_scenarios_without_failures_does_not_recover(monkeypatch) -> None:
    calls: list[str] = []

    def scenario_one(page) -> None:
        _ = page
        calls.append("one")

    def scenario_two(page) -> None:
        _ = page
        calls.append("two")

    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="scenario_one",
                handler=scenario_one,
                intent="one",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            ),
            automation.ScenarioSpec(
                name="scenario_two",
                handler=scenario_two,
                intent="two",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            ),
        ],
    )
    monkeypatch.setattr(
        automation,
        "_recover_ui_state",
        lambda page: calls.append("recover"),
    )
    monkeypatch.setattr(
        automation,
        "_cleanup_between_scenarios",
        lambda page: calls.append("cleanup"),
    )

    result = automation.run_all_scenarios(DummyPage(), shuffle=False)

    assert result.failed_scenarios == []
    assert result.executed_scenarios == ["scenario_one", "scenario_two"]
    assert "recover" not in calls
    assert calls.count("cleanup") == 2


def test_run_scenario_executes_named_scenario(monkeypatch) -> None:
    seen_pages: list[DummyPage] = []

    def named(page) -> None:
        seen_pages.append(page)

    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="named",
                handler=named,
                intent="named",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            )
        ],
    )
    page = DummyPage()

    automation.run_scenario(page, "named")

    assert seen_pages == [page]


def test_run_scenario_raises_for_unknown_name(monkeypatch) -> None:
    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="known",
                handler=lambda page: None,
                intent="known",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            )
        ],
    )

    with pytest.raises(ValueError, match="Unknown scenario"):
        automation.run_scenario(DummyPage(), "unknown")


def test_list_scenarios_returns_scenario_names(monkeypatch) -> None:
    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="first",
                handler=lambda page: None,
                intent="first",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            ),
            automation.ScenarioSpec(
                name="second",
                handler=lambda page: None,
                intent="second",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            ),
        ],
    )

    assert automation.list_scenarios() == ["first", "second"]


def test_run_scenario_reports_lifecycle_events(monkeypatch) -> None:
    events: list[tuple[str, str, str, dict[str, object] | None]] = []

    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="named",
                handler=lambda page: None,
                intent="exercise named scenario",
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            )
        ],
    )
    automation.set_scenario_event_reporter(
        lambda action, name, status, metadata: events.append(
            (action, name, status, metadata)
        )
    )

    try:
        automation.run_scenario(DummyPage(), "named")
    finally:
        automation.set_scenario_event_reporter(None)

    assert events[0][:3] == ("start", "named", "")
    assert events[0][3] is not None
    assert events[0][3]["intent"] == "exercise named scenario"
    assert events[1][:3] == ("end", "named", "completed")


def _make_scenarios(
    monkeypatch,
    specs: list[tuple[str, object]],
) -> None:
    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name=name,
                handler=handler,
                intent=name,
                activation_events=("onCommand",),
                api_capabilities=("commands",),
                success_signals=("done",),
            )
            for name, handler in specs
        ],
    )


def test_fail_fast_on_fatal_crash_breaks_loop(monkeypatch) -> None:
    calls: list[str] = []

    def scenario_crash(page) -> None:
        _ = page
        calls.append("crash")
        raise PlaywrightError("Keyboard.press: Target crashed")

    def scenario_after(page) -> None:
        _ = page
        calls.append("after")

    _make_scenarios(
        monkeypatch,
        [("scenario_crash", scenario_crash), ("scenario_after", scenario_after)],
    )
    monkeypatch.setattr(
        automation, "_recover_ui_state", lambda page: calls.append("recover")
    )
    monkeypatch.setattr(
        automation, "_cleanup_between_scenarios", lambda page: calls.append("cleanup")
    )

    events: list[tuple[str, str, str, dict | None]] = []
    automation.set_scenario_event_reporter(
        lambda action, name, status, metadata: events.append(
            (action, name, status, metadata)
        )
    )
    try:
        result = automation.run_all_scenarios(DummyPage(), shuffle=False)
    finally:
        automation.set_scenario_event_reporter(None)

    assert calls == ["crash"]
    assert result.executed_scenarios == ["scenario_crash"]
    assert result.failed_scenarios == ["scenario_crash"]
    assert "recover" not in calls
    assert "cleanup" not in calls

    end_events = [ev for ev in events if ev[0] == "end"]
    assert len(end_events) == 1
    assert end_events[0][1] == "scenario_crash"
    assert end_events[0][2] == "failed"
    metadata = end_events[0][3] or {}
    assert metadata.get("failure_reason_code") == "fatal_ui_crash"
    assert "Target crashed" in str(metadata.get("error", ""))


def test_non_fatal_error_still_continues(monkeypatch) -> None:
    calls: list[str] = []

    def scenario_fail(page) -> None:
        _ = page
        raise RuntimeError("selector missing")

    def scenario_next(page) -> None:
        _ = page
        calls.append("next")

    _make_scenarios(
        monkeypatch,
        [("scenario_fail", scenario_fail), ("scenario_next", scenario_next)],
    )
    monkeypatch.setattr(
        automation, "_recover_ui_state", lambda page: calls.append("recover")
    )
    monkeypatch.setattr(
        automation, "_cleanup_between_scenarios", lambda page: calls.append("cleanup")
    )

    result = automation.run_all_scenarios(DummyPage(), shuffle=False)

    assert result.executed_scenarios == ["scenario_fail", "scenario_next"]
    assert result.failed_scenarios == ["scenario_fail"]
    assert "recover" in calls
    assert calls.count("cleanup") == 2
    assert "next" in calls


def test_retry_on_crash_reloads_and_continues(monkeypatch) -> None:
    calls: list[str] = []
    reloaded_pages: list[object] = []

    crash_page = DummyPage()
    reloaded_page = DummyPage()

    def scenario_crash(page) -> None:
        calls.append(f"crash:{id(page)}")
        if id(page) == id(crash_page):
            raise PlaywrightError("Target crashed")

    def scenario_after(page) -> None:
        calls.append(f"after:{id(page)}")

    _make_scenarios(
        monkeypatch,
        [("scenario_crash", scenario_crash), ("scenario_after", scenario_after)],
    )
    monkeypatch.setattr(
        automation, "_recover_ui_state", lambda page: calls.append("recover")
    )
    monkeypatch.setattr(
        automation, "_cleanup_between_scenarios", lambda page: calls.append("cleanup")
    )

    def fake_reload(browser, page, **kwargs):
        _ = browser, page, kwargs
        reloaded_pages.append(page)
        return reloaded_page

    monkeypatch.setattr(vscode, "reload_workbench_window", fake_reload)

    result = automation.run_all_scenarios(
        crash_page,
        shuffle=False,
        retry_on_crash=True,
        browser=object(),
    )

    assert result.failed_scenarios == ["scenario_crash"]
    assert f"after:{id(reloaded_page)}" in calls
    assert len(reloaded_pages) == 1
    assert reloaded_pages[0] is crash_page
    assert "recover" not in calls


def test_retry_on_crash_without_browser_falls_back_to_fail_fast(monkeypatch) -> None:
    calls: list[str] = []

    def scenario_crash(page) -> None:
        _ = page
        calls.append("crash")
        raise PlaywrightError("Target crashed")

    def scenario_after(page) -> None:
        _ = page
        calls.append("after")

    _make_scenarios(
        monkeypatch,
        [("scenario_crash", scenario_crash), ("scenario_after", scenario_after)],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    def fake_reload(*args, **kwargs):
        _ = args, kwargs
        raise AssertionError("reload must not be called without browser")

    monkeypatch.setattr(vscode, "reload_workbench_window", fake_reload)

    result = automation.run_all_scenarios(
        DummyPage(),
        shuffle=False,
        retry_on_crash=True,
        browser=None,
    )

    assert calls == ["crash"]
    assert "after" not in calls
    assert result.failed_scenarios == ["scenario_crash"]


def test_retry_on_crash_reload_failure_breaks_loop(monkeypatch) -> None:
    calls: list[str] = []

    def scenario_crash(page) -> None:
        _ = page
        calls.append("crash")
        raise PlaywrightError("Target crashed")

    def scenario_after(page) -> None:
        _ = page
        calls.append("after")

    _make_scenarios(
        monkeypatch,
        [("scenario_crash", scenario_crash), ("scenario_after", scenario_after)],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    def fake_reload(browser, page, **kwargs):
        _ = browser, page, kwargs
        raise vscode.ReloadWindowError("dispatch", "reload failed in test")

    monkeypatch.setattr(vscode, "reload_workbench_window", fake_reload)

    result = automation.run_all_scenarios(
        DummyPage(),
        shuffle=False,
        retry_on_crash=True,
        browser=object(),
    )

    assert calls == ["crash"]
    assert "after" not in calls
    assert result.failed_scenarios == ["scenario_crash"]


def test_fail_fast_marks_remaining_scenarios_as_aborted(monkeypatch) -> None:
    def scenario_crash(page) -> None:
        _ = page
        raise PlaywrightError("Target crashed")

    def scenario_b(page) -> None:
        raise AssertionError("scenario_b must not run after fatal crash")

    def scenario_c(page) -> None:
        raise AssertionError("scenario_c must not run after fatal crash")

    _make_scenarios(
        monkeypatch,
        [
            ("scenario_crash", scenario_crash),
            ("scenario_b", scenario_b),
            ("scenario_c", scenario_c),
        ],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    result = automation.run_all_scenarios(DummyPage(), shuffle=False)

    assert result.failed_scenarios == ["scenario_crash"]
    skipped_names = [record.name for record in result.skipped_scenarios]
    assert skipped_names == ["scenario_b", "scenario_c"]
    for record in result.skipped_scenarios:
        assert record.reason_code == automation.ABORTED_AFTER_FATAL_UI_CRASH_REASON
        assert "renderer crashed" in record.detail


def test_fail_fast_aborts_on_reload_failure_when_retry_requested(monkeypatch) -> None:
    def scenario_crash(page) -> None:
        _ = page
        raise PlaywrightError("Target crashed")

    def scenario_b(page) -> None:
        raise AssertionError("scenario_b must not run after failed reload")

    _make_scenarios(
        monkeypatch,
        [("scenario_crash", scenario_crash), ("scenario_b", scenario_b)],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    def fake_reload(*args, **kwargs):
        _ = args, kwargs
        raise vscode.ReloadWindowError("dispatch", "reload failed in test")

    monkeypatch.setattr(vscode, "reload_workbench_window", fake_reload)

    result = automation.run_all_scenarios(
        DummyPage(),
        shuffle=False,
        retry_on_crash=True,
        browser=object(),
    )

    assert result.failed_scenarios == ["scenario_crash"]
    assert [r.name for r in result.skipped_scenarios] == ["scenario_b"]
    assert (
        result.skipped_scenarios[0].reason_code
        == automation.ABORTED_AFTER_FATAL_UI_CRASH_REASON
    )


def test_retry_on_crash_invokes_on_page_reloaded_callback(monkeypatch) -> None:
    crash_page = DummyPage()
    reloaded_page = DummyPage()
    callback_args: list[object] = []

    def scenario_crash(page) -> None:
        if id(page) == id(crash_page):
            raise PlaywrightError("Target crashed")

    def scenario_after(page) -> None:
        _ = page

    _make_scenarios(
        monkeypatch,
        [("scenario_crash", scenario_crash), ("scenario_after", scenario_after)],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)
    monkeypatch.setattr(
        vscode,
        "reload_workbench_window",
        lambda browser, page, **kwargs: reloaded_page,
    )

    automation.run_all_scenarios(
        crash_page,
        shuffle=False,
        retry_on_crash=True,
        browser=object(),
        on_page_reloaded=lambda page: callback_args.append(page),
    )

    assert callback_args == [reloaded_page]


def test_on_page_reloaded_not_called_on_reload_failure(monkeypatch) -> None:
    def scenario_crash(page) -> None:
        _ = page
        raise PlaywrightError("Target crashed")

    _make_scenarios(monkeypatch, [("scenario_crash", scenario_crash)])
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    def fake_reload(*args, **kwargs):
        _ = args, kwargs
        raise vscode.ReloadWindowError("dispatch", "reload failed in test")

    monkeypatch.setattr(vscode, "reload_workbench_window", fake_reload)

    callback_args: list[object] = []
    automation.run_all_scenarios(
        DummyPage(),
        shuffle=False,
        retry_on_crash=True,
        browser=object(),
        on_page_reloaded=lambda page: callback_args.append(page),
    )

    assert callback_args == []


def test_ui_blocker_probe_invoked_before_each_scenario(monkeypatch) -> None:
    probe_calls: list[str] = []

    _make_scenarios(
        monkeypatch,
        [
            ("scenario_one", lambda page: None),
            ("scenario_two", lambda page: None),
        ],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    automation.run_all_scenarios(
        DummyPage(),
        shuffle=False,
        ui_blocker_probe=lambda page, name: probe_calls.append(name),
    )

    assert probe_calls == ["scenario_one", "scenario_two"]


def test_ui_blocker_probe_failure_does_not_break_loop(monkeypatch) -> None:
    completed: list[str] = []

    def probe(page, name) -> None:
        raise PlaywrightError("probe boom")

    _make_scenarios(
        monkeypatch,
        [
            ("scenario_one", lambda page: completed.append("one")),
            ("scenario_two", lambda page: completed.append("two")),
        ],
    )
    monkeypatch.setattr(automation, "_recover_ui_state", lambda page: None)
    monkeypatch.setattr(automation, "_cleanup_between_scenarios", lambda page: None)

    result = automation.run_all_scenarios(
        DummyPage(),
        shuffle=False,
        ui_blocker_probe=probe,
    )

    assert completed == ["one", "two"]
    assert result.failed_scenarios == []


def test_get_scenario_registry_exposes_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [
            automation.ScenarioSpec(
                name="registry_case",
                handler=lambda page: None,
                intent="registry metadata",
                activation_events=("onView:search",),
                api_capabilities=("search_views",),
                success_signals=("search focus",),
                risk_of_noise="low",
            )
        ],
    )

    registry = automation.get_scenario_registry()

    assert registry == [
        {
            "name": "registry_case",
            "intent": "registry metadata",
            "activation_events": ["onView:search"],
            "api_capabilities": ["search_views"],
            "success_signals": ["search focus"],
            "risk_of_noise": "low",
        }
    ]
