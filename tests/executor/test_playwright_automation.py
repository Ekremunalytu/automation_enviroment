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
        [("scenario_ok", scenario_ok), ("scenario_fail", scenario_fail)],
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
        [("scenario_one", scenario_one), ("scenario_two", scenario_two)],
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

    monkeypatch.setattr(automation, "_ALL_SCENARIOS", [("named", named)])
    page = DummyPage()

    automation.run_scenario(page, "named")

    assert seen_pages == [page]


def test_run_scenario_raises_for_unknown_name(monkeypatch) -> None:
    monkeypatch.setattr(automation, "_ALL_SCENARIOS", [("known", lambda page: None)])

    with pytest.raises(ValueError, match="Unknown scenario"):
        automation.run_scenario(DummyPage(), "unknown")


def test_list_scenarios_returns_scenario_names(monkeypatch) -> None:
    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [("first", lambda page: None), ("second", lambda page: None)],
    )

    assert automation.list_scenarios() == ["first", "second"]


def test_run_scenario_reports_lifecycle_events(monkeypatch) -> None:
    events: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        automation,
        "_ALL_SCENARIOS",
        [("named", lambda page: None)],
    )
    automation.set_scenario_event_reporter(
        lambda action, name, status: events.append((action, name, status))
    )

    try:
        automation.run_scenario(DummyPage(), "named")
    finally:
        automation.set_scenario_event_reporter(None)

    assert events == [
        ("start", "named", ""),
        ("end", "named", "completed"),
    ]
