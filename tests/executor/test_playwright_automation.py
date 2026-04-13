from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import automation  # noqa: E402


class DummyPage:
    def wait_for_timeout(self, timeout_ms: int) -> None:
        _ = timeout_ms


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

    failed = automation.run_all_scenarios(DummyPage(), shuffle=False)

    assert failed == ["scenario_fail"]
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

    failed = automation.run_all_scenarios(DummyPage(), shuffle=False)

    assert failed == []
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
