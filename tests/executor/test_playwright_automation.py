from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = Path(__file__).resolve().parents[2] / "executor" / "playwright"
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
