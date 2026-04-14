from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import entrypoint  # noqa: E402
import triggers as trigger_loader  # noqa: E402


def test_resolve_execution_plan_prefers_layered_trigger_passes() -> None:
    payload = trigger_loader.TriggerPayload(
        selected_scenarios=["rename_symbol"],
        stimulus_passes=[{"pass_id": "workspace_bootstrap", "status": "planned"}],
    )

    plan, scenarios = entrypoint._resolve_execution_plan(
        None,
        payload,
    )

    assert plan == "layered_passes"
    assert scenarios == ["rename_symbol"]


def test_resolve_execution_plan_uses_selected_scenarios_for_explicit_scenario() -> None:
    payload = trigger_loader.TriggerPayload(selected_scenarios=["rename_symbol"])

    plan, scenarios = entrypoint._resolve_execution_plan(
        "coding_session",
        payload,
    )

    assert plan == "selected_scenarios"
    assert scenarios == ["coding_session"]


def test_resolve_execution_plan_uses_single_scenario_fallback() -> None:
    plan, scenarios = entrypoint._resolve_execution_plan(
        "coding_session",
        None,
    )

    assert plan == "single_scenario"
    assert scenarios == ["coding_session"]


def test_resolve_execution_plan_runs_all_without_payload_or_fallback() -> None:
    plan, scenarios = entrypoint._resolve_execution_plan(
        None,
        None,
    )

    assert plan == "all_scenarios"
    assert scenarios == []
