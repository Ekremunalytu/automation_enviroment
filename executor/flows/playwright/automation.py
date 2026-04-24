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
import vscode
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
from stimulus_types import AutomationExecutionResult, SkippedScenarioRecord

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

ScenarioEventReporter = Callable[[str, str, str, dict[str, Any] | None], None]

_SCENARIO_EVENT_REPORTER: ScenarioEventReporter | None = None
_ALL_SCENARIOS: list[ScenarioSpec] = build_default_scenarios()


def run_all_scenarios(
    page: Page,
    shuffle: bool = False,
    *,
    retry_on_crash: bool = False,
    browser: Any = None,
) -> AutomationExecutionResult:
    """Run all user behavior simulation scenarios sequentially."""
    scenarios = list(_ALL_SCENARIOS)
    if shuffle:
        random.shuffle(scenarios)
    result = AutomationExecutionResult(
        requested_scenarios=[scenario.name for scenario in scenarios]
    )
    _run_scenario_sequence(
        page,
        scenarios,
        result,
        retry_on_crash=retry_on_crash,
        browser=browser,
    )
    return result


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
    *,
    retry_on_crash: bool = False,
    browser: Any = None,
) -> AutomationExecutionResult:
    """Run a subset of scenarios by name."""
    result = AutomationExecutionResult(requested_scenarios=list(names))
    selected: list[ScenarioSpec] = []
    for name in names:
        scenario = _scenario_map().get(name)
        if scenario is None:
            result.skipped_scenarios.append(
                SkippedScenarioRecord(
                    name=name,
                    reason_code="unknown_scenario",
                    detail=f"Scenario {name!r} is not registered in the executor.",
                )
            )
            continue
        selected.append(scenario)
    if shuffle:
        random.shuffle(selected)
    _run_scenario_sequence(
        page,
        selected,
        result,
        retry_on_crash=retry_on_crash,
        browser=browser,
    )
    return result


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


_FATAL_UI_ERROR_MARKERS: tuple[str, ...] = (
    "Target crashed",
    "renderer process gone",
    "Target closed",
    "Target page, context or browser has been closed",
    "Connection closed",
    "page has been closed",
)

FATAL_UI_CRASH_REASON = "fatal_ui_crash"


def is_fatal_ui_error(exc: BaseException, page: Page | None) -> tuple[bool, str]:
    """Classify whether an exception means the VS Code renderer is dead.

    Returns ``(True, "fatal_ui_crash")`` on a positive assertion — explicit
    error-message markers, `page.is_closed()` / `page.context.is_closed()`
    true, or a short-timeout liveness probe that raises. Otherwise returns
    ``(False, "")`` so the caller can continue with normal recovery.
    """
    message = str(exc)
    for marker in _FATAL_UI_ERROR_MARKERS:
        if marker in message:
            return True, FATAL_UI_CRASH_REASON
    if page is None:
        return False, ""
    try:
        if page.is_closed():
            return True, FATAL_UI_CRASH_REASON
    except PlaywrightError:
        return True, FATAL_UI_CRASH_REASON
    ctx_is_closed = getattr(page.context, "is_closed", None)
    if callable(ctx_is_closed):
        try:
            if ctx_is_closed():
                return True, FATAL_UI_CRASH_REASON
        except PlaywrightError:
            return True, FATAL_UI_CRASH_REASON
    try:
        page.wait_for_function("1 === 1", timeout=1500)
    except PlaywrightError:
        return True, FATAL_UI_CRASH_REASON
    return False, ""


def _run_scenario_sequence(
    page: Page,
    scenarios: list[ScenarioSpec],
    result: AutomationExecutionResult,
    *,
    retry_on_crash: bool = False,
    browser: Any = None,
) -> None:
    for scenario in scenarios:
        _append_unique(result.executed_scenarios, scenario.name)
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
            fatal, reason_code = is_fatal_ui_error(exc, page)
            error_detail = str(exc)[:500]
            _append_unique(result.failed_scenarios, scenario.name)
            _emit_scenario_event(
                "end",
                scenario.name,
                "failed",
                metadata=_scenario_metadata(
                    scenario,
                    error=error_detail,
                    failure_reason_code=reason_code,
                ),
            )
            if fatal:
                _log(f"FATAL: {scenario.name} -> {exc}")
                if retry_on_crash and browser is not None:
                    try:
                        page = vscode.reload_workbench_window(browser, page)
                    except (vscode.ReloadWindowError, PlaywrightError) as reload_exc:
                        _log(f"Reload after crash failed: {reload_exc}")
                        break
                    continue
                break
            _log(f"FAIL: {scenario.name} -> {exc}")
            _recover_ui_state(page)
        _cleanup_between_scenarios(page)
        page.wait_for_timeout(1000)


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _scenario_metadata(
    scenario: ScenarioSpec,
    *,
    error: str = "",
    failure_reason_code: str = "",
) -> dict[str, Any]:
    return scenario_metadata(
        scenario,
        error=error,
        failure_reason_code=failure_reason_code,
    )
