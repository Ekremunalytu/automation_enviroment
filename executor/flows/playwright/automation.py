"""User behavior simulation scenarios for extension security testing."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import commands
import editor
import keyboard
import settings  # noqa: F401
import sidebar  # noqa: F401
import terminal  # noqa: F401
from scenarios.common import log as _log
from scenarios.editing import (  # noqa: F401
    scenario_coding_session,
    scenario_notebook_session,
    scenario_refactor_workflow,
)
from scenarios.registry import (
    ScenarioSpec,
    build_default_scenarios,
    scenario_metadata,
)
from scenarios.runtime import (  # noqa: F401
    scenario_authentication_probe,
    scenario_debug_session,
    scenario_git_workflow,
    scenario_terminal_usage,
    scenario_webview_probe,
)
from scenarios.workbench import (  # noqa: F401
    scenario_diagnostics_check,
    scenario_extension_browsing,
    scenario_project_exploration,
    scenario_search_workflow,
    scenario_settings_modification,
)

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

ScenarioEventReporter = Callable[[str, str, str, dict[str, Any] | None], None]

_SCENARIO_EVENT_REPORTER: ScenarioEventReporter | None = None
_ALL_SCENARIOS: list[ScenarioSpec] = build_default_scenarios()


def run_all_scenarios(page: Page, shuffle: bool = False) -> list[str]:
    """Run all user behavior simulation scenarios sequentially."""
    scenarios = list(_ALL_SCENARIOS)
    failed_scenarios: list[str] = []
    if shuffle:
        random.shuffle(scenarios)

    for scenario in scenarios:
        _emit_scenario_event(
            "start", scenario.name, metadata=_scenario_metadata(scenario)
        )
        try:
            scenario.handler(page)
            _log(f"DONE: {scenario.name}")
            _emit_scenario_event(
                "end",
                scenario.name,
                "completed",
                metadata=_scenario_metadata(scenario),
            )
        except (PlaywrightError, RuntimeError, ValueError) as exc:
            _log(f"FAIL: {scenario.name} -> {exc}")
            failed_scenarios.append(scenario.name)
            _emit_scenario_event(
                "end",
                scenario.name,
                "failed",
                metadata=_scenario_metadata(scenario, error=str(exc)),
            )
            _recover_ui_state(page)
        _cleanup_between_scenarios(page)
        page.wait_for_timeout(1000)

    return failed_scenarios


def run_scenario(page: Page, name: str) -> None:
    """Run a single scenario by name."""
    scenario = _scenario_map().get(name)
    if scenario is None:
        raise ValueError(
            f"Unknown scenario: {name!r}. Available: {list(_scenario_map())}"
        )
    _emit_scenario_event("start", name, metadata=_scenario_metadata(scenario))
    try:
        scenario.handler(page)
    except (PlaywrightError, RuntimeError, ValueError) as exc:
        _emit_scenario_event(
            "end",
            name,
            "failed",
            metadata=_scenario_metadata(scenario, error=str(exc)),
        )
        raise
    _emit_scenario_event(
        "end",
        name,
        "completed",
        metadata=_scenario_metadata(scenario),
    )


def run_selected_scenarios(
    page: Page,
    names: list[str],
    shuffle: bool = False,
) -> list[str]:
    """Run a subset of scenarios by name."""
    selected = [scenario for name in names if (scenario := _scenario_map().get(name))]
    if shuffle:
        random.shuffle(selected)

    failed: list[str] = []
    for scenario in selected:
        _emit_scenario_event(
            "start", scenario.name, metadata=_scenario_metadata(scenario)
        )
        try:
            scenario.handler(page)
            _log(f"DONE: {scenario.name}")
            _emit_scenario_event(
                "end",
                scenario.name,
                "completed",
                metadata=_scenario_metadata(scenario),
            )
        except (PlaywrightError, RuntimeError, ValueError) as exc:
            _log(f"FAIL: {scenario.name} -> {exc}")
            failed.append(scenario.name)
            _emit_scenario_event(
                "end",
                scenario.name,
                "failed",
                metadata=_scenario_metadata(scenario, error=str(exc)),
            )
            _recover_ui_state(page)
        _cleanup_between_scenarios(page)
        page.wait_for_timeout(1000)
    return failed


def list_scenarios() -> list[str]:
    """Return available scenario names."""
    return [scenario.name for scenario in _ALL_SCENARIOS]


def get_scenario_registry() -> list[dict[str, Any]]:
    """Return scenario metadata without handlers for reporting/auditing."""
    return [_scenario_metadata(scenario) for scenario in _ALL_SCENARIOS]


def set_scenario_event_reporter(reporter: ScenarioEventReporter | None) -> None:
    """Register an optional callback for scenario lifecycle events."""
    global _SCENARIO_EVENT_REPORTER
    _SCENARIO_EVENT_REPORTER = reporter


def _recover_ui_state(page: Page) -> None:
    """Dismiss stuck dialogs and return VS Code to a usable state."""
    try:
        for _ in range(3):
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)
        editor._dismiss_notification(page)
        page.keyboard.press(keyboard.FOCUS_EDITOR)
        page.wait_for_timeout(300)
    except PlaywrightError as exc:
        _log(f"UI recovery failed: {exc}")


def _cleanup_between_scenarios(page: Page) -> None:
    """Release UI/editor state between scenarios to reduce memory pressure."""
    try:
        page.keyboard.press("Control+KeyK")
        page.wait_for_timeout(100)
        page.keyboard.press("Control+KeyW")
        page.wait_for_timeout(500)
        _kill_all_terminals(page)
        page.keyboard.press(keyboard.TOGGLE_PANEL)
        page.wait_for_timeout(200)
        editor._dismiss_notification(page)
        page.keyboard.press("Escape")
        page.keyboard.press(keyboard.FOCUS_EDITOR)
        page.wait_for_timeout(200)
    except PlaywrightError as exc:
        _log(f"Inter-scenario cleanup failed: {exc}")


def _kill_all_terminals(page: Page) -> None:
    """Kill all terminal instances via Command Palette."""
    try:
        commands.run_command(page, "Terminal: Kill All Terminals")
        page.wait_for_timeout(500)
    except PlaywrightError:
        pass


def _emit_scenario_event(
    action: str,
    name: str,
    status: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    if _SCENARIO_EVENT_REPORTER is None:
        return
    _SCENARIO_EVENT_REPORTER(action, name, status, metadata)


def _scenario_map() -> dict[str, ScenarioSpec]:
    return {scenario.name: scenario for scenario in _ALL_SCENARIOS}


def _scenario_metadata(
    scenario: ScenarioSpec,
    *,
    error: str = "",
) -> dict[str, Any]:
    return scenario_metadata(scenario, error=error)
