"""Scenario registry and metadata for Playwright automation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page

from .editing import (
    scenario_coding_session,
    scenario_notebook_session,
    scenario_refactor_workflow,
)
from .runtime import (
    scenario_authentication_probe,
    scenario_debug_session,
    scenario_git_workflow,
    scenario_terminal_usage,
    scenario_webview_probe,
)
from .workbench import (
    scenario_diagnostics_check,
    scenario_extension_browsing,
    scenario_project_exploration,
    scenario_search_workflow,
    scenario_settings_modification,
)

ScenarioFn = Callable[[Page], None]


@dataclass(frozen=True)
class ScenarioSpec:
    """Execution handler plus metadata for a supported scenario."""

    name: str
    handler: ScenarioFn
    intent: str
    activation_events: tuple[str, ...]
    api_capabilities: tuple[str, ...]
    success_signals: tuple[str, ...]
    risk_of_noise: str = "medium"


def build_default_scenarios() -> list[ScenarioSpec]:
    return [
        ScenarioSpec(
            name="coding_session",
            handler=scenario_coding_session,
            intent="Exercise language tooling, commands, formatting, and save flows.",
            activation_events=("onLanguage", "onCommand"),
            api_capabilities=(
                "commands",
                "window_ui",
                "workspace_fs",
                "languages_editor",
            ),
            success_signals=(
                "file open",
                "suggest widget",
                "format action",
                "save action",
            ),
        ),
        ScenarioSpec(
            name="debug_session",
            handler=scenario_debug_session,
            intent="Drive debug views, breakpoints, and debug lifecycle transitions.",
            activation_events=(
                "onDebug",
                "onDebugResolve",
                "onDebugAdapterProtocolTracker",
            ),
            api_capabilities=("commands", "window_ui", "debug", "workspace_fs"),
            success_signals=("breakpoint toggle", "debug start", "debug console"),
            risk_of_noise="high",
        ),
        ScenarioSpec(
            name="terminal_usage",
            handler=scenario_terminal_usage,
            intent="Use integrated terminals and task-adjacent shell flows.",
            activation_events=("onTaskType", "onTerminalProfile"),
            api_capabilities=("commands", "terminal_tasks", "workspace_fs"),
            success_signals=("terminal open", "command execution"),
            risk_of_noise="high",
        ),
        ScenarioSpec(
            name="git_workflow",
            handler=scenario_git_workflow,
            intent="Exercise Source Control UI and git-oriented workspace changes.",
            activation_events=("onView:scm",),
            api_capabilities=("commands", "window_ui", "scm", "workspace_fs"),
            success_signals=("scm focus", "git diff", "git status"),
            risk_of_noise="high",
        ),
        ScenarioSpec(
            name="extension_browsing",
            handler=scenario_extension_browsing,
            intent="Drive Extensions view browsing and marketplace search.",
            activation_events=("onView:extensions",),
            api_capabilities=("window_ui",),
            success_signals=("extensions focus", "search query changes"),
            risk_of_noise="low",
        ),
        ScenarioSpec(
            name="settings_modification",
            handler=scenario_settings_modification,
            intent="Modify settings and browse configuration UI surfaces.",
            activation_events=("onConfiguration",),
            api_capabilities=("commands", "window_ui", "settings", "workspace_fs"),
            success_signals=("settings write", "theme change", "settings search"),
        ),
        ScenarioSpec(
            name="project_exploration",
            handler=scenario_project_exploration,
            intent="Open multiple file types to trigger broad workspace and language activation.",
            activation_events=("workspaceContains", "onView:explorer", "onLanguage"),
            api_capabilities=("window_ui", "workspace_fs", "languages_editor"),
            success_signals=("explorer focus", "multi-file open"),
        ),
        ScenarioSpec(
            name="search_workflow",
            handler=scenario_search_workflow,
            intent="Drive search sidebar queries across the workspace.",
            activation_events=("onView:search",),
            api_capabilities=("window_ui", "search_views"),
            success_signals=("search focus", "query updates"),
            risk_of_noise="low",
        ),
        ScenarioSpec(
            name="diagnostics_check",
            handler=scenario_diagnostics_check,
            intent="Inspect problems and output views where diagnostics surface.",
            activation_events=("onView:output",),
            api_capabilities=("window_ui", "workspace_fs"),
            success_signals=("problems focus", "output focus"),
        ),
        ScenarioSpec(
            name="refactor_workflow",
            handler=scenario_refactor_workflow,
            intent="Trigger rename and refactor actions in the editor.",
            activation_events=("onCommand", "onLanguage"),
            api_capabilities=("commands", "languages_editor", "workspace_fs"),
            success_signals=("find widget", "rename widget"),
        ),
        ScenarioSpec(
            name="notebook_session",
            handler=scenario_notebook_session,
            intent="Open notebook content and interact with notebook UI.",
            activation_events=("onNotebook",),
            api_capabilities=("window_ui", "notebooks", "workspace_fs"),
            success_signals=("notebook open", "cell focus"),
        ),
        ScenarioSpec(
            name="authentication_probe",
            handler=scenario_authentication_probe,
            intent="Exercise account and sign-in surfaces that trigger authentication flows.",
            activation_events=("onAuthenticationRequest",),
            api_capabilities=("commands", "window_ui", "authentication"),
            success_signals=("accounts menu", "sign in prompt"),
        ),
        ScenarioSpec(
            name="webview_probe",
            handler=scenario_webview_probe,
            intent="Open preview surfaces backed by a VS Code webview panel.",
            activation_events=("onWebviewPanel",),
            api_capabilities=("commands", "window_ui", "webview"),
            success_signals=("preview open", "webview surface"),
        ),
    ]


def scenario_metadata(
    scenario: ScenarioSpec,
    *,
    error: str = "",
    failure_reason_code: str = "",
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "name": scenario.name,
        "intent": scenario.intent,
        "activation_events": list(scenario.activation_events),
        "api_capabilities": list(scenario.api_capabilities),
        "success_signals": list(scenario.success_signals),
        "risk_of_noise": scenario.risk_of_noise,
    }
    if error:
        metadata["error"] = error
    if failure_reason_code:
        metadata["failure_reason_code"] = failure_reason_code
    return metadata
