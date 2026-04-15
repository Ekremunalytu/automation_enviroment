"""Trigger selection helpers for the marketplace analysis workflow."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CAPABILITY_TAXONOMY: list[str] = [
    "commands",
    "window_ui",
    "workspace_fs",
    "languages_editor",
    "debug",
    "terminal_tasks",
    "scm",
    "search_views",
    "settings",
    "notebooks",
    "custom_editors",
    "uri_walkthrough",
    "authentication",
    "chat",
    "comments",
    "testing",
    "webview",
    "workspace_trust",
]

_GLOBAL_CAPABILITY_SUPPORT: dict[str, str] = {
    "commands": "covered",
    "window_ui": "covered",
    "workspace_fs": "covered",
    "languages_editor": "covered",
    "debug": "covered",
    "terminal_tasks": "covered",
    "scm": "covered",
    "search_views": "covered",
    "settings": "covered",
    "notebooks": "covered",
    "custom_editors": "covered",
    "uri_walkthrough": "covered",
    "authentication": "covered",
    "chat": "missing",
    "comments": "missing",
    "testing": "missing",
    "webview": "covered",
    "workspace_trust": "missing",
}

_GLOBAL_CAPABILITY_NOTES: dict[str, str] = {
    "custom_editors": (
        "Custom editor coverage uses bait files plus a post-open ledger so each "
        "attempt is visible even when the target editor fails to restore."
    ),
    "uri_walkthrough": (
        "URI, walkthrough, and open-external flows are kept explicit in the "
        "ledger so UI-first vs harness-assisted attempts stay distinguishable."
    ),
    "authentication": (
        "Authentication coverage stays local-only and uses stub providers or "
        "target provider requests inside the sandbox."
    ),
    "chat": (
        "Chat participant and language-model tool coverage remain local-only and "
        "must not call external services."
    ),
    "comments": (
        "Comment thread coverage is provided through local harness surfaces so "
        "discussion flows stay inside the sandbox."
    ),
    "testing": (
        "Testing coverage uses local controllers and run/debug flows without "
        "calling external test services."
    ),
    "workspace_trust": (
        "Workspace trust transitions are explicitly labeled when they require "
        "harness assistance instead of visible UI-only stimulation."
    ),
}

_OFFICIAL_CAPABILITY_SUPPORT: dict[str, str] = {
    "commands": "covered",
    "window_ui": "covered",
    "workspace_fs": "covered",
    "languages_editor": "covered",
    "debug": "covered",
    "terminal_tasks": "covered",
    "scm": "missing",
    "search_views": "covered",
    "settings": "missing",
    "notebooks": "covered",
    "custom_editors": "covered",
    "uri_walkthrough": "covered",
    "authentication": "covered",
    "chat": "missing",
    "comments": "missing",
    "testing": "missing",
    "webview": "covered",
    "workspace_trust": "missing",
}

_HEURISTIC_CAPABILITY_SUPPORT: dict[str, str] = {
    capability: _GLOBAL_CAPABILITY_SUPPORT[capability]
    for capability in CAPABILITY_TAXONOMY
}

_OFFICIAL_TRACK = "official"
_HEURISTIC_TRACK = "heuristic"
_TRACK_SOURCE = {
    _OFFICIAL_TRACK: "official_activation_track",
    _HEURISTIC_TRACK: "heuristic_workflow_track",
}
_BUILTIN_VIEW_IDS = frozenset({"explorer", "extensions", "output", "scm", "search"})
_PASS_ORDER = [
    "workspace_bootstrap",
    "ui_first_user_session",
    "target_specific_activation",
    "unresolved_event_backfill",
    "post_run_verification",
]
_PASS_LABELS = {
    "workspace_bootstrap": "workspace/bootstrap pass",
    "ui_first_user_session": "UI-first user session pass",
    "target_specific_activation": "target-specific activation pass",
    "unresolved_event_backfill": "unresolved-event backfill pass",
    "post_run_verification": "post-run verification pass",
}
_PASS_DESCRIPTIONS = {
    "workspace_bootstrap": (
        "Materialize workspace fixtures, launch prerequisites, and startup-aligned "
        "stimuli before visible interaction begins."
    ),
    "ui_first_user_session": (
        "Drive visible VS Code workflows first so user-led evidence stays primary."
    ),
    "target_specific_activation": (
        "Run event-family-specific flows for the target extension's declared "
        "activation surface."
    ),
    "unresolved_event_backfill": (
        "Retry events through deterministic harness paths when the visible UI "
        "cannot reach them reliably."
    ),
    "post_run_verification": (
        "Reconcile activation evidence, target ownership, and per-event outcome "
        "status after execution finishes."
    ),
}
_MAX_SCENARIOS_PER_RUN = 5
_MAX_EXTRA_COMMANDS = 6


@dataclass(frozen=True)
class ScenarioDefinition:
    """Metadata for a supported automation scenario."""

    name: str
    intent: str
    activation_events: tuple[str, ...]
    contributes_signals: tuple[str, ...]
    api_capabilities: tuple[str, ...]
    prerequisites: tuple[str, ...] = ()
    success_signals: tuple[str, ...] = ()
    risk_of_noise: str = "medium"


SCENARIO_REGISTRY: tuple[ScenarioDefinition, ...] = (
    ScenarioDefinition(
        name="coding_session",
        intent=(
            "Exercise editor commands, language tooling, formatting, and command "
            "handlers."
        ),
        activation_events=("onLanguage", "onCommand"),
        contributes_signals=("commands", "languages", "keybindings", "menus"),
        api_capabilities=("commands", "window_ui", "workspace_fs", "languages_editor"),
        prerequisites=("workspace files available",),
        success_signals=("file open", "suggest widget", "format action", "save action"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="project_exploration",
        intent=(
            "Open multiple workspace files and explorer surfaces to trigger broad "
            "language activation."
        ),
        activation_events=("workspaceContains", "onView:explorer", "onLanguage"),
        contributes_signals=("languages", "views"),
        api_capabilities=("window_ui", "workspace_fs", "languages_editor"),
        prerequisites=("workspace fixture tree available",),
        success_signals=("explorer focus", "multi-file open"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="diagnostics_check",
        intent=(
            "Inspect problems and output surfaces where diagnostic extensions "
            "usually surface activity."
        ),
        activation_events=("onView:output",),
        contributes_signals=("problemMatchers", "views", "viewsWelcome"),
        api_capabilities=("window_ui", "workspace_fs"),
        prerequisites=("workspace file with analyzable content",),
        success_signals=("problems focus", "output focus"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="search_workflow",
        intent=(
            "Drive the search sidebar and text search UI for search-related "
            "activations."
        ),
        activation_events=("onView:search", "onSearch"),
        contributes_signals=("views",),
        api_capabilities=("window_ui", "search_views"),
        prerequisites=("workspace indexed by VS Code",),
        success_signals=("search focus", "query updates"),
        risk_of_noise="low",
    ),
    ScenarioDefinition(
        name="settings_modification",
        intent=(
            "Modify settings.json and browse Settings UI to trigger "
            "configuration listeners."
        ),
        activation_events=("onConfiguration",),
        contributes_signals=("configuration", "configurationDefaults"),
        api_capabilities=("commands", "window_ui", "settings", "workspace_fs"),
        prerequisites=("user settings writable",),
        success_signals=("settings.json write", "theme change", "settings search"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="debug_session",
        intent="Open debug tooling, set breakpoints, and start/stop debug flows.",
        activation_events=(
            "onDebug",
            "onDebugResolve",
            "onDebugAdapterProtocolTracker",
            "onDebugDynamicConfigurations",
            "onDebugInitialConfigurations",
        ),
        contributes_signals=("debuggers", "breakpoints"),
        api_capabilities=("commands", "window_ui", "debug", "workspace_fs"),
        prerequisites=("debuggable workspace file",),
        success_signals=("breakpoint toggle", "debug start", "debug console"),
        risk_of_noise="high",
    ),
    ScenarioDefinition(
        name="terminal_usage",
        intent="Open integrated terminals and run task-like commands.",
        activation_events=(
            "onTaskType",
            "onTerminal",
            "onTerminalProfile",
            "onTerminalShellIntegration",
        ),
        contributes_signals=("terminal", "taskDefinitions"),
        api_capabilities=("commands", "terminal_tasks", "workspace_fs"),
        prerequisites=("integrated terminal available",),
        success_signals=("terminal open", "command execution"),
        risk_of_noise="high",
    ),
    ScenarioDefinition(
        name="git_workflow",
        intent="Drive source control view and git-oriented workspace actions.",
        activation_events=("onView:scm",),
        contributes_signals=("menus", "views"),
        api_capabilities=("commands", "window_ui", "scm", "workspace_fs"),
        prerequisites=("workspace under git",),
        success_signals=("scm focus", "git diff", "git status"),
        risk_of_noise="high",
    ),
    ScenarioDefinition(
        name="extension_browsing",
        intent="Open Extensions view and browse marketplace search results.",
        activation_events=("onView:extensions",),
        contributes_signals=("views",),
        api_capabilities=("window_ui",),
        prerequisites=("extensions view available",),
        success_signals=("extensions focus", "search query changes"),
        risk_of_noise="low",
    ),
    ScenarioDefinition(
        name="refactor_workflow",
        intent="Trigger rename and refactor-related editor operations.",
        activation_events=("onCommand", "onLanguage"),
        contributes_signals=("commands", "menus"),
        api_capabilities=("commands", "languages_editor", "workspace_fs"),
        prerequisites=("workspace symbol available",),
        success_signals=("find widget", "rename widget"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="notebook_session",
        intent="Open notebook content and interact with notebook cells.",
        activation_events=("onNotebook", "onRenderer"),
        contributes_signals=("customEditors",),
        api_capabilities=("window_ui", "notebooks", "workspace_fs"),
        prerequisites=("notebook bait file available",),
        success_signals=("notebook open", "cell focus"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="authentication_probe",
        intent="Open account and sign-in surfaces to trigger authentication flows.",
        activation_events=("onAuthenticationRequest",),
        contributes_signals=("authentication", "commands", "menus"),
        api_capabilities=("commands", "window_ui", "authentication"),
        prerequisites=("accounts integration available",),
        success_signals=("accounts menu", "sign in prompt"),
        risk_of_noise="medium",
    ),
    ScenarioDefinition(
        name="webview_probe",
        intent="Open preview and panel flows that rely on VS Code webview surfaces.",
        activation_events=("onWebviewPanel", "onView"),
        contributes_signals=("commands", "views", "viewsWelcome"),
        api_capabilities=("commands", "window_ui", "webview"),
        prerequisites=("previewable workspace file available",),
        success_signals=("preview open", "webview surface"),
        risk_of_noise="medium",
    ),
)


@dataclass(frozen=True)
class EventStrategy:
    """Targeted strategy for an activation-event family."""

    family: str
    capability_tags: tuple[str, ...]
    executor_group: str
    prerequisites: tuple[str, ...]
    verification_contract: tuple[str, ...]
    legacy_scenarios: tuple[str, ...] = ()
    ui_path: str = ""
    harness_fallback: str | None = None
    official: bool = True
    heuristic: bool = False


OFFICIAL_EVENT_REGISTRY: dict[str, EventStrategy] = {
    "onAuthenticationRequest": EventStrategy(
        family="onAuthenticationRequest",
        capability_tags=("authentication", "window_ui"),
        executor_group="authentication_request",
        prerequisites=("auth_request_target",),
        verification_contract=("activation_log_exact", "target_runtime_delta"),
        legacy_scenarios=("authentication_probe",),
        ui_path="Accounts: Sign In or target auth consumer flow",
        harness_fallback="run_current_stimulus",
    ),
    "onChatParticipant": EventStrategy(
        family="onChatParticipant",
        capability_tags=("chat", "window_ui"),
        executor_group="chat_participant",
        prerequisites=("chat_participant_target",),
        verification_contract=("activation_log_exact", "automation_trace"),
        ui_path="Open chat and invoke participant by id",
        harness_fallback="run_current_stimulus",
    ),
    "onCommand": EventStrategy(
        family="onCommand",
        capability_tags=("commands", "window_ui"),
        executor_group="command",
        prerequisites=("command_target",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("coding_session", "refactor_workflow"),
        ui_path="Command Palette invocation",
        harness_fallback="run_current_stimulus",
    ),
    "onCustomEditor": EventStrategy(
        family="onCustomEditor",
        capability_tags=("custom_editors", "workspace_fs", "window_ui"),
        executor_group="custom_editor",
        prerequisites=("custom_editor_bait_files",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        ui_path="Open a bait file matched by contributes.customEditors",
        harness_fallback="run_current_stimulus",
    ),
    "onDebug": EventStrategy(
        family="onDebug",
        capability_tags=("debug", "window_ui"),
        executor_group="debug",
        prerequisites=("debug_launch_config",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("debug_session",),
        ui_path="Run and Debug sidebar workflow",
        harness_fallback="run_current_stimulus",
    ),
    "onDebugAdapterProtocolTracker": EventStrategy(
        family="onDebugAdapterProtocolTracker",
        capability_tags=("debug",),
        executor_group="debug",
        prerequisites=("debug_launch_config",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("debug_session",),
        ui_path="Start a debug session that needs protocol tracking",
        harness_fallback="run_current_stimulus",
    ),
    "onDebugDynamicConfigurations": EventStrategy(
        family="onDebugDynamicConfigurations",
        capability_tags=("debug",),
        executor_group="debug_dynamic",
        prerequisites=("debug_launch_config",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        legacy_scenarios=("debug_session",),
        ui_path="Select and Start Debugging flow",
        harness_fallback="run_current_stimulus",
    ),
    "onDebugInitialConfigurations": EventStrategy(
        family="onDebugInitialConfigurations",
        capability_tags=("debug",),
        executor_group="debug_initial",
        prerequisites=("debug_launch_config",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        legacy_scenarios=("debug_session",),
        ui_path="Create launch.json through Run and Debug",
        harness_fallback="run_current_stimulus",
    ),
    "onDebugResolve": EventStrategy(
        family="onDebugResolve",
        capability_tags=("debug",),
        executor_group="debug",
        prerequisites=("debug_launch_config",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("debug_session",),
        ui_path="Start a debug session with a matching debug type",
        harness_fallback="run_current_stimulus",
    ),
    "onEditSession": EventStrategy(
        family="onEditSession",
        capability_tags=("workspace_fs",),
        executor_group="edit_session",
        prerequisites=("edit_session_fixture",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        ui_path="Visible edit-session commands when available",
        harness_fallback="run_current_stimulus",
    ),
    "onFileSystem": EventStrategy(
        family="onFileSystem",
        capability_tags=("workspace_fs",),
        executor_group="filesystem",
        prerequisites=("filesystem_scheme_target",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        ui_path="Read a document for the requested scheme",
        harness_fallback="run_current_stimulus",
    ),
    "onIssueReporterOpened": EventStrategy(
        family="onIssueReporterOpened",
        capability_tags=("window_ui",),
        executor_group="issue_reporter",
        prerequisites=(),
        verification_contract=("activation_log_exact", "automation_trace"),
        ui_path="Help: Report Issue",
        harness_fallback="run_current_stimulus",
    ),
    "onLanguage": EventStrategy(
        family="onLanguage",
        capability_tags=("languages_editor", "workspace_fs"),
        executor_group="language",
        prerequisites=("language_fixture",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("coding_session", "project_exploration"),
        ui_path="Open a file that resolves to the requested language",
    ),
    "onLanguageModelTool": EventStrategy(
        family="onLanguageModelTool",
        capability_tags=("chat",),
        executor_group="language_model_tool",
        prerequisites=("language_model_tool_target",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        ui_path="Invoke the tool from the chat/tooling surface",
        harness_fallback="run_current_stimulus",
    ),
    "onNotebook": EventStrategy(
        family="onNotebook",
        capability_tags=("notebooks", "workspace_fs"),
        executor_group="notebook",
        prerequisites=("notebook_fixture",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("notebook_session",),
        ui_path="Open a notebook document with the requested type",
        harness_fallback="run_current_stimulus",
    ),
    "onOpenExternalUri": EventStrategy(
        family="onOpenExternalUri",
        capability_tags=("uri_walkthrough", "window_ui"),
        executor_group="open_external_uri",
        prerequisites=("loopback_uri_target",),
        verification_contract=("activation_log_exact", "automation_trace"),
        ui_path="Open a loopback http/https URI",
        harness_fallback="run_current_stimulus",
    ),
    "onRenderer": EventStrategy(
        family="onRenderer",
        capability_tags=("notebooks", "webview"),
        executor_group="renderer",
        prerequisites=("renderer_fixture", "notebook_fixture"),
        verification_contract=("activation_log_prefix", "automation_trace"),
        legacy_scenarios=("notebook_session",),
        ui_path="Render notebook output that matches the renderer id",
        harness_fallback="run_current_stimulus",
    ),
    "onSearch": EventStrategy(
        family="onSearch",
        capability_tags=("search_views", "window_ui"),
        executor_group="search",
        prerequisites=("searchable_workspace",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("search_workflow",),
        ui_path="Find in Files over the requested scheme",
    ),
    "onStartupFinished": EventStrategy(
        family="onStartupFinished",
        capability_tags=("window_ui",),
        executor_group="startup_finished",
        prerequisites=("workspace_ready",),
        verification_contract=("activation_log_exact",),
        legacy_scenarios=("project_exploration",),
        ui_path="Observe startup completion after workbench warmup",
    ),
    "onTaskType": EventStrategy(
        family="onTaskType",
        capability_tags=("terminal_tasks",),
        executor_group="task_type",
        prerequisites=("task_definition_target",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("terminal_usage",),
        ui_path="Tasks: Run Task",
        harness_fallback="run_current_stimulus",
    ),
    "onTerminal": EventStrategy(
        family="onTerminal",
        capability_tags=("terminal_tasks",),
        executor_group="terminal",
        prerequisites=("terminal_shell_target",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("terminal_usage",),
        ui_path="Launch an integrated terminal for the requested shell type",
        harness_fallback="run_current_stimulus",
    ),
    "onTerminalProfile": EventStrategy(
        family="onTerminalProfile",
        capability_tags=("terminal_tasks",),
        executor_group="terminal_profile",
        prerequisites=("terminal_profile_target",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("terminal_usage",),
        ui_path="Launch the requested terminal profile",
        harness_fallback="run_current_stimulus",
    ),
    "onTerminalShellIntegration": EventStrategy(
        family="onTerminalShellIntegration",
        capability_tags=("terminal_tasks",),
        executor_group="terminal_shell_integration",
        prerequisites=("terminal_shell_target",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        legacy_scenarios=("terminal_usage",),
        ui_path="Open a terminal and wait for shell integration",
        harness_fallback="run_current_stimulus",
    ),
    "onUri": EventStrategy(
        family="onUri",
        capability_tags=("uri_walkthrough", "window_ui"),
        executor_group="uri",
        prerequisites=("uri_target",),
        verification_contract=("activation_log_exact", "target_runtime_delta"),
        ui_path="Open vscode://<publisher.name>/...",
        harness_fallback="run_current_stimulus",
    ),
    "onView": EventStrategy(
        family="onView",
        capability_tags=("window_ui",),
        executor_group="view",
        prerequisites=("view_target",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        legacy_scenarios=("project_exploration",),
        ui_path="Expand the contributed view in the sidebar",
        harness_fallback="run_current_stimulus",
    ),
    "onWalkthrough": EventStrategy(
        family="onWalkthrough",
        capability_tags=("uri_walkthrough", "window_ui"),
        executor_group="walkthrough",
        prerequisites=("walkthrough_target",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        ui_path="Getting Started walkthrough open flow",
        harness_fallback="run_current_stimulus",
    ),
    "onWebviewPanel": EventStrategy(
        family="onWebviewPanel",
        capability_tags=("webview", "window_ui"),
        executor_group="webview_panel",
        prerequisites=("webview_target",),
        verification_contract=("activation_log_prefix", "automation_trace"),
        legacy_scenarios=("webview_probe",),
        ui_path="Restore a webview panel with the matching viewType",
        harness_fallback="run_current_stimulus",
    ),
    "workspaceContains": EventStrategy(
        family="workspaceContains",
        capability_tags=("workspace_fs", "languages_editor"),
        executor_group="workspace_contains",
        prerequisites=("workspace_contains_fixture",),
        verification_contract=("activation_log_prefix", "target_runtime_delta"),
        legacy_scenarios=("project_exploration",),
        ui_path="Open a workspace that contains the requested glob",
    ),
    "*": EventStrategy(
        family="*",
        capability_tags=("window_ui",),
        executor_group="startup",
        prerequisites=("workspace_ready",),
        verification_contract=("activation_log_exact",),
        legacy_scenarios=(
            "coding_session",
            "project_exploration",
            "diagnostics_check",
            "search_workflow",
            "debug_session",
        ),
        ui_path="Observe startup activation once the window is ready",
    ),
}

_SCENARIO_BY_NAME = {scenario.name: scenario for scenario in SCENARIO_REGISTRY}
_SCENARIO_PRIORITY = [scenario.name for scenario in SCENARIO_REGISTRY]


@dataclass
class TriggerPayload:
    """Data passed from host to container to guide layered stimulation."""

    analysis_profile: str = "layered_deep"
    selected_scenarios: list[str] = field(default_factory=list)
    official_selected_scenarios: list[str] = field(default_factory=list)
    heuristic_selected_scenarios: list[str] = field(default_factory=list)
    selected_scenario_details: list[dict[str, Any]] = field(default_factory=list)
    selection_reasons: dict[str, list[str]] = field(default_factory=dict)
    coverage_tracks: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage_summary: dict[str, Any] = field(default_factory=dict)
    coverage_matrix: list[dict[str, Any]] = field(default_factory=list)
    official_attempted_capabilities: list[str] = field(default_factory=list)
    heuristic_attempted_capabilities: list[str] = field(default_factory=list)
    target_extension_id: str | None = None
    command_targets: dict[str, str] = field(default_factory=dict)
    view_targets: dict[str, dict[str, str]] = field(default_factory=dict)
    extra_notebook_files: list[str] = field(default_factory=list)
    extra_custom_editor_files: list[str] = field(default_factory=list)
    extra_commands: list[str] = field(default_factory=list)
    auth_provider_ids: list[str] = field(default_factory=list)
    webview_view_ids: list[str] = field(default_factory=list)
    uri_trigger: str | None = None
    run_task_trigger: bool = False
    run_walkthrough_trigger: bool = False
    stimulus_passes: list[dict[str, Any]] = field(default_factory=list)
    event_attempts: list[dict[str, Any]] = field(default_factory=list)
    prerequisite_results: list[dict[str, Any]] = field(default_factory=list)
    official_event_coverage: dict[str, Any] = field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, Any] = field(default_factory=dict)


EVENT_TYPE_TO_SCENARIOS: dict[str, list[str]] = {
    "onLanguage": ["coding_session", "project_exploration"],
    "onCommand": ["coding_session", "refactor_workflow"],
    "onDebug": ["debug_session"],
    "onDebugResolve": ["debug_session"],
    "onDebugAdapterProtocolTracker": ["debug_session"],
    "onDebugDynamicConfigurations": ["debug_session"],
    "onDebugInitialConfigurations": ["debug_session"],
    "workspaceContains": ["project_exploration"],
    "onNotebook": ["notebook_session"],
    "onRenderer": ["notebook_session"],
    "onTaskType": ["terminal_usage"],
    "onTerminal": ["terminal_usage"],
    "onTerminalProfile": ["terminal_usage"],
    "onTerminalShellIntegration": ["terminal_usage"],
    "onAuthenticationRequest": ["authentication_probe"],
    "onWebviewPanel": ["webview_probe"],
    "onSearch": ["search_workflow"],
    "onWalkthrough": [],
    "onUri": [],
    "onOpenExternalUri": [],
    "onCustomEditor": [],
    "onFileSystem": [],
    "onEditSession": [],
    "onIssueReporterOpened": [],
    "onChatParticipant": [],
    "onLanguageModelTool": [],
    "onView": [],
    "onStartupFinished": [],
    "*": [],
}

HEURISTIC_EVENT_TYPE_TO_SCENARIOS: dict[str, list[str]] = {
    "onView:scm": ["git_workflow"],
    "onView:extensions": ["extension_browsing"],
    "onView:explorer": ["project_exploration"],
    "onView:search": ["search_workflow"],
    "onView:output": ["diagnostics_check"],
    "onConfiguration": ["settings_modification"],
}


def _apply_activation_event(
    event: dict[str, str | None],
    *,
    payload: TriggerPayload,
    publisher_name: str | None,
    contributed_view_ids: set[str],
    official_extra_capabilities: set[str],
    mark_scenario: Callable[..., None],
    register_attempt: Callable[..., None],
) -> None:
    event_type = event.get("event_type", "") or ""
    event_value = event.get("event_value")
    event_label = _activation_label(event_type, event_value)

    if event_type in {"*", "onStartupFinished"}:
        register_attempt(
            event_type=event_type,
            event_value=event_value,
            track=_OFFICIAL_TRACK,
            reason=f"activation {event_type} requests startup coverage",
        )
        for index, scenario_name in enumerate(_SCENARIO_PRIORITY):
            mark_scenario(
                scenario_name,
                reason=f"activation {event_type} requests broad workspace coverage",
                score=10_000 - index,
                track=_HEURISTIC_TRACK,
            )
        return

    if event_type == "onView" and event_value:
        _apply_view_trigger(
            event_value=str(event_value),
            contributed_view_ids=contributed_view_ids,
            payload=payload,
            mark_scenario=mark_scenario,
            register_attempt=register_attempt,
            official_extra_capabilities=official_extra_capabilities,
        )
        return

    if event_type in OFFICIAL_EVENT_REGISTRY:
        register_attempt(
            event_type=event_type,
            event_value=event_value,
            track=_OFFICIAL_TRACK,
            reason=f"activation {event_label}",
        )
        scenario_names = EVENT_TYPE_TO_SCENARIOS.get(event_type, [])
        for index, scenario_name in enumerate(scenario_names):
            mark_scenario(
                scenario_name,
                reason=f"activation {event_label}",
                score=900 - index,
                track=_OFFICIAL_TRACK,
            )
    elif event_type in HEURISTIC_EVENT_TYPE_TO_SCENARIOS:
        scenario_names = HEURISTIC_EVENT_TYPE_TO_SCENARIOS[event_type]
        for index, scenario_name in enumerate(scenario_names):
            mark_scenario(
                scenario_name,
                reason=f"activation {event_label}",
                score=700 - index,
                track=_HEURISTIC_TRACK,
            )

    _apply_event_capability_metadata(
        event_type=event_type,
        event_value=event_value,
        publisher_name=publisher_name,
        payload=payload,
        contributed_view_ids=contributed_view_ids,
        official_extra_capabilities=official_extra_capabilities,
    )


def _apply_view_trigger(
    *,
    event_value: str,
    contributed_view_ids: set[str],
    payload: TriggerPayload,
    mark_scenario: Callable[..., None],
    register_attempt: Callable[..., None],
    official_extra_capabilities: set[str],
) -> None:
    key = f"onView:{event_value}"
    if event_value in _BUILTIN_VIEW_IDS:
        register_attempt(
            event_type="onView",
            event_value=event_value,
            track=_HEURISTIC_TRACK,
            reason=f"built-in view trigger {key} is tracked as heuristic only",
        )
        scenario_names = HEURISTIC_EVENT_TYPE_TO_SCENARIOS.get(key, [])
        for index, scenario_name in enumerate(scenario_names):
            mark_scenario(
                scenario_name,
                reason=f"built-in view trigger {key} treated as heuristic coverage",
                score=1_000 - index,
                track=_HEURISTIC_TRACK,
            )
        return

    if event_value in contributed_view_ids:
        register_attempt(
            event_type="onView",
            event_value=event_value,
            track=_OFFICIAL_TRACK,
            reason=f"declared contributed view activation {key}",
        )
        if "webview" in event_value.lower():
            mark_scenario(
                "webview_probe",
                reason=f"contributed view trigger {key}",
                score=995,
                track=_OFFICIAL_TRACK,
            )
            official_extra_capabilities.add("webview")
            payload.webview_view_ids.append(event_value)
        else:
            mark_scenario(
                "project_exploration",
                reason=f"contributed view trigger {key}",
                score=990,
                track=_OFFICIAL_TRACK,
            )
        return

    register_attempt(
        event_type="onView",
        event_value=event_value,
        track=_HEURISTIC_TRACK,
        reason=(
            f"view trigger {key} was not matched to a contributed view and "
            "is therefore treated as heuristic"
        ),
    )
    mark_scenario(
        "project_exploration",
        reason=(
            f"unmapped view trigger {key} fell back to heuristic explorer coverage"
        ),
        score=250,
        track=_HEURISTIC_TRACK,
    )


def _apply_event_capability_metadata(
    *,
    event_type: str,
    event_value: str | None,
    publisher_name: str | None,
    payload: TriggerPayload,
    contributed_view_ids: set[str],
    official_extra_capabilities: set[str],
) -> None:
    if event_type == "onNotebook":
        payload.extra_notebook_files.append("notebooks/analysis.ipynb")
        official_extra_capabilities.add("notebooks")
    if event_type == "onRenderer":
        payload.extra_notebook_files.append("notebooks/analysis.ipynb")
        official_extra_capabilities.update({"notebooks", "webview"})
    if event_type == "onTaskType":
        payload.run_task_trigger = True
        official_extra_capabilities.add("terminal_tasks")
    if event_type in {"onTerminal", "onTerminalProfile", "onTerminalShellIntegration"}:
        official_extra_capabilities.add("terminal_tasks")
    if event_type == "onAuthenticationRequest":
        if event_value:
            payload.auth_provider_ids.append(str(event_value))
        official_extra_capabilities.add("authentication")
    if event_type == "onWebviewPanel":
        if event_value:
            payload.webview_view_ids.append(str(event_value))
        official_extra_capabilities.add("webview")
    if (
        event_type == "onView"
        and event_value
        and str(event_value) in contributed_view_ids
    ):
        official_extra_capabilities.add("window_ui")
    if event_type == "onWalkthrough":
        payload.run_walkthrough_trigger = True
        official_extra_capabilities.add("uri_walkthrough")
    if event_type == "onOpenExternalUri":
        official_extra_capabilities.add("uri_walkthrough")
    if event_type == "onUri" and publisher_name:
        payload.uri_trigger = f"vscode://{publisher_name}/activate"
        official_extra_capabilities.add("uri_walkthrough")
    if event_type in {"onFileSystem", "onEditSession"}:
        official_extra_capabilities.add("workspace_fs")
    if event_type == "onSearch":
        official_extra_capabilities.add("search_views")
    if event_type in {"onChatParticipant", "onLanguageModelTool"}:
        official_extra_capabilities.add("chat")
    if event_type == "onIssueReporterOpened":
        official_extra_capabilities.add("window_ui")


def _apply_contributes_metadata(
    *,
    payload: TriggerPayload,
    contributes_custom_editors: list[dict] | None,
    contributes_commands: list[dict] | None,
    contributes_authentication: list[dict] | None,
    contributes_views: dict[str, Any] | None,
    contributes_debuggers: list[dict] | None,
    contributes_walkthroughs: list[dict] | None,
    contributes_task_definitions: list[dict] | None,
    contributes_terminal_profiles: list[dict] | None,
    capability_metadata: dict[str, Any] | None,
    heuristic_extra_capabilities: set[str],
    official_extra_capabilities: set[str],
    mark_scenario: Callable[..., None],
) -> None:
    if contributes_custom_editors:
        for custom_editor in contributes_custom_editors:
            selectors = custom_editor.get("selector", [])
            for selector in selectors:
                glob_pattern = selector.get("filenamePattern", "")
                if not glob_pattern:
                    continue
                bait = _glob_to_bait_filename(glob_pattern)
                if bait:
                    payload.extra_custom_editor_files.append(bait)
                    heuristic_extra_capabilities.add("custom_editors")

    if contributes_commands:
        for command in contributes_commands:
            title = command.get("title", "")
            command_id = command.get("command_id", "") or command.get("command", "")
            if command_id:
                payload.command_targets[str(command_id)] = (
                    str(title) if title else str(command_id)
                )
            if title:
                payload.extra_commands.append(title)
                heuristic_extra_capabilities.add("commands")

    if contributes_authentication:
        mark_scenario(
            "authentication_probe",
            reason="contributes.authentication advertised provider metadata",
            score=520,
            track=_HEURISTIC_TRACK,
        )
        for provider in contributes_authentication:
            provider_id = provider.get("auth_id") or provider.get("id") or ""
            if provider_id:
                payload.auth_provider_ids.append(str(provider_id))
                heuristic_extra_capabilities.add("authentication")

    if contributes_views:
        if any(str(key).startswith("webview") for key in contributes_views):
            mark_scenario(
                "webview_probe",
                reason="contributes.views exposed a webview-oriented surface",
                score=510,
                track=_HEURISTIC_TRACK,
            )
            heuristic_extra_capabilities.add("webview")
        for location, views in contributes_views.items():
            if not isinstance(views, list):
                continue
            for view in views:
                if not isinstance(view, dict):
                    continue
                view_id = view.get("id") or ""
                if not view_id:
                    continue
                payload.view_targets[str(view_id)] = {
                    "container_id": str(location),
                    "view_type": str(view.get("type", "")),
                }
                if "webview" in str(view_id).lower():
                    payload.webview_view_ids.append(str(view_id))
                    heuristic_extra_capabilities.add("webview")

    if contributes_debuggers:
        official_extra_capabilities.add("debug")
    if contributes_walkthroughs:
        official_extra_capabilities.add("uri_walkthrough")
    if contributes_task_definitions or contributes_terminal_profiles:
        official_extra_capabilities.add("terminal_tasks")
    unsupported_trust = {
        "",
        "false",
        "unsupported",
    }
    if (
        capability_metadata
        and str(capability_metadata.get("untrusted_supported", "")).lower()
        not in unsupported_trust
    ):
        official_extra_capabilities.add("workspace_trust")


def _apply_default_fallback(
    *,
    selected_candidates: set[str],
    compiled_attempts: dict[tuple[str, str], dict[str, Any]],
    mark_scenario: Callable[..., None],
) -> None:
    if selected_candidates:
        return

    mark_scenario(
        "coding_session",
        reason=(
            "default fallback because activation metadata did not map to a "
            "stronger workflow"
        ),
        score=1,
        track=_HEURISTIC_TRACK,
    )
    compiled_attempts[(_HEURISTIC_TRACK, "heuristic:workspace_probe")] = {
        "attempt_id": "heuristic-workspace-probe",
        "declared_event": "heuristic:workspace_probe",
        "activation_event": "heuristic:workspace_probe",
        "event_family": "heuristic_workspace_probe",
        "event_value": "",
        "track": _HEURISTIC_TRACK,
        "selected_by": "fallback",
        "selection_reasons": [
            "default fallback because no declared activation event mapped cleanly"
        ],
        "pass_name": "ui_first_user_session",
        "backfill_pass_name": "",
        "prerequisite_keys": ["workspace_ready"],
        "verification_contract": ["automation_trace"],
        "trigger_method": "ui_simulation",
        "fallback_trigger_method": "",
        "executor_action": "scenario:coding_session",
        "backfill_executor_action": "",
        "legacy_scenarios": ["coding_session"],
        "capability_tags": [
            "commands",
            "languages_editor",
            "window_ui",
            "workspace_fs",
        ],
        "status": "planned",
        "trigger_method_used": "",
        "attempted_passes": [],
        "evidence": [],
        "verification_status": "not_attempted",
        "failure_reason_code": "",
        "blocked_reason_code": "",
        "result_details": "",
        "official": False,
        "heuristic": True,
    }


def _finalize_payload(
    *,
    payload: TriggerPayload,
    selected_candidates: set[str],
    official_candidates: set[str],
    heuristic_candidates: set[str],
    scenario_scores: dict[str, int],
    scenario_reasons: dict[str, set[str]],
    compiled_attempts: dict[tuple[str, str], dict[str, Any]],
    official_extra_capabilities: set[str],
    heuristic_extra_capabilities: set[str],
) -> TriggerPayload:
    payload.extra_commands = payload.extra_commands[:_MAX_EXTRA_COMMANDS]
    payload.auth_provider_ids = sorted(set(payload.auth_provider_ids))
    payload.webview_view_ids = sorted(set(payload.webview_view_ids))
    payload.extra_custom_editor_files = sorted(set(payload.extra_custom_editor_files))
    payload.extra_notebook_files = sorted(set(payload.extra_notebook_files))
    payload.event_attempts = [
        compiled_attempts[key]
        for key in sorted(compiled_attempts, key=lambda item: (item[0], item[1]))
    ]
    payload.stimulus_passes = _build_stimulus_passes(payload.event_attempts)
    payload.prerequisite_results = _build_prerequisite_results(payload.event_attempts)
    payload.selected_scenarios = _order_scenarios(selected_candidates, scenario_scores)
    payload.official_selected_scenarios = [
        scenario_name
        for scenario_name in payload.selected_scenarios
        if scenario_name in official_candidates
    ]
    payload.heuristic_selected_scenarios = [
        scenario_name
        for scenario_name in payload.selected_scenarios
        if scenario_name in heuristic_candidates
    ]
    payload.selection_reasons = {
        scenario_name: sorted(scenario_reasons.get(scenario_name, set()))
        for scenario_name in payload.selected_scenarios
    }
    payload.selected_scenario_details = [
        _serialize_scenario_definition(
            _SCENARIO_BY_NAME[scenario_name],
            payload.selection_reasons.get(scenario_name, []),
        )
        for scenario_name in payload.selected_scenarios
    ]
    payload.official_attempted_capabilities = _collect_active_capabilities(
        payload.official_selected_scenarios,
        payload=payload,
        track=_OFFICIAL_TRACK,
        extra_capabilities=official_extra_capabilities,
    )
    official_attempted = set(payload.official_attempted_capabilities)
    payload.heuristic_attempted_capabilities = [
        capability
        for capability in _collect_active_capabilities(
            payload.heuristic_selected_scenarios,
            payload=payload,
            track=_HEURISTIC_TRACK,
            extra_capabilities=heuristic_extra_capabilities,
        )
        if capability not in official_attempted
    ]
    official_matrix = build_coverage_matrix(payload, track=_OFFICIAL_TRACK)
    heuristic_matrix = build_coverage_matrix(payload, track=_HEURISTIC_TRACK)
    payload.coverage_summary = _summarize_coverage_matrix(official_matrix)
    payload.coverage_matrix = official_matrix
    payload.coverage_tracks = {
        _OFFICIAL_TRACK: {
            "source": _TRACK_SOURCE[_OFFICIAL_TRACK],
            "selected_scenarios": payload.official_selected_scenarios,
            "summary": payload.coverage_summary,
            "matrix": official_matrix,
        },
        _HEURISTIC_TRACK: {
            "source": _TRACK_SOURCE[_HEURISTIC_TRACK],
            "selected_scenarios": payload.heuristic_selected_scenarios,
            "summary": _summarize_coverage_matrix(heuristic_matrix),
            "matrix": heuristic_matrix,
        },
    }
    payload.official_event_coverage = _summarize_event_attempts(
        payload.event_attempts,
        track=_OFFICIAL_TRACK,
    )
    payload.heuristic_workflow_coverage = _summarize_event_attempts(
        payload.event_attempts,
        track=_HEURISTIC_TRACK,
    )
    return payload


def select_scenarios(
    activation_events: list[dict[str, str | None]],
    contributes_custom_editors: list[dict] | None = None,
    publisher_name: str | None = None,
    contributes_commands: list[dict] | None = None,
    contributes_authentication: list[dict] | None = None,
    contributes_views: dict[str, Any] | None = None,
    contributes_debuggers: list[dict] | None = None,
    contributes_walkthroughs: list[dict] | None = None,
    contributes_task_definitions: list[dict] | None = None,
    contributes_terminal_profiles: list[dict] | None = None,
    capability_metadata: dict[str, Any] | None = None,
) -> TriggerPayload:
    """Compile declared activation metadata into a layered stimulus payload."""

    selected_candidates: set[str] = set()
    official_candidates: set[str] = set()
    heuristic_candidates: set[str] = set()
    scenario_scores: dict[str, int] = {}
    scenario_reasons: dict[str, set[str]] = {}
    official_extra_capabilities: set[str] = set()
    heuristic_extra_capabilities: set[str] = set()
    payload = TriggerPayload(target_extension_id=publisher_name)
    contributed_view_ids = _collect_contributed_view_ids(contributes_views)

    def mark_scenario(
        name: str,
        *,
        reason: str,
        score: int,
        track: str,
    ) -> None:
        if name not in _SCENARIO_BY_NAME:
            return
        selected_candidates.add(name)
        scenario_scores[name] = max(score, scenario_scores.get(name, 0))
        scenario_reasons.setdefault(name, set()).add(reason)
        if track == _OFFICIAL_TRACK:
            official_candidates.add(name)
        else:
            heuristic_candidates.add(name)

    compiled_attempts: dict[tuple[str, str], dict[str, Any]] = {}

    def register_attempt(
        *,
        event_type: str,
        event_value: str | None,
        track: str,
        reason: str,
        selected_by: str = "activation_event",
    ) -> None:
        key = (track, _activation_label(event_type, event_value))
        if key in compiled_attempts:
            compiled_attempts[key]["selection_reasons"] = sorted(
                set(compiled_attempts[key]["selection_reasons"]) | {reason}
            )
            return
        strategy = OFFICIAL_EVENT_REGISTRY.get(event_type)
        if strategy is None:
            return
        compiled_attempts[key] = _build_event_attempt(
            strategy=strategy,
            event_type=event_type,
            event_value=event_value,
            track=track,
            reason=reason,
            publisher_name=publisher_name,
            selected_by=selected_by,
        )

    for event in activation_events:
        _apply_activation_event(
            event,
            payload=payload,
            publisher_name=publisher_name,
            contributed_view_ids=contributed_view_ids,
            official_extra_capabilities=official_extra_capabilities,
            mark_scenario=mark_scenario,
            register_attempt=register_attempt,
        )

    _apply_contributes_metadata(
        payload=payload,
        contributes_custom_editors=contributes_custom_editors,
        contributes_commands=contributes_commands,
        contributes_authentication=contributes_authentication,
        contributes_views=contributes_views,
        contributes_debuggers=contributes_debuggers,
        contributes_walkthroughs=contributes_walkthroughs,
        contributes_task_definitions=contributes_task_definitions,
        contributes_terminal_profiles=contributes_terminal_profiles,
        capability_metadata=capability_metadata,
        heuristic_extra_capabilities=heuristic_extra_capabilities,
        official_extra_capabilities=official_extra_capabilities,
        mark_scenario=mark_scenario,
    )
    _apply_default_fallback(
        selected_candidates=selected_candidates,
        compiled_attempts=compiled_attempts,
        mark_scenario=mark_scenario,
    )
    return _finalize_payload(
        payload=payload,
        selected_candidates=selected_candidates,
        official_candidates=official_candidates,
        heuristic_candidates=heuristic_candidates,
        scenario_scores=scenario_scores,
        scenario_reasons=scenario_reasons,
        compiled_attempts=compiled_attempts,
        official_extra_capabilities=official_extra_capabilities,
        heuristic_extra_capabilities=heuristic_extra_capabilities,
    )


def build_coverage_matrix(
    payload: TriggerPayload,
    *,
    track: str = _OFFICIAL_TRACK,
) -> list[dict[str, Any]]:
    """Build target-first coverage information for the selected payload."""

    if track == _OFFICIAL_TRACK:
        track_selected_scenarios = payload.official_selected_scenarios
        active_capabilities = set(payload.official_attempted_capabilities)
        support_map = _OFFICIAL_CAPABILITY_SUPPORT
    else:
        track_selected_scenarios = payload.heuristic_selected_scenarios
        active_capabilities = set(payload.heuristic_attempted_capabilities)
        support_map = _HEURISTIC_CAPABILITY_SUPPORT
    matrix: list[dict[str, Any]] = []

    for capability in CAPABILITY_TAXONOMY:
        supported_scenarios = [
            scenario.name
            for scenario in SCENARIO_REGISTRY
            if capability in scenario.api_capabilities
        ]
        capability_selected_scenarios = [
            scenario_name
            for scenario_name in track_selected_scenarios
            if capability in _SCENARIO_BY_NAME[scenario_name].api_capabilities
        ]
        support_level = support_map[capability]
        if support_level == "missing":
            status = "missing"
        elif capability in active_capabilities and support_level == "covered":
            status = "covered"
        else:
            status = "partial"

        matrix.append(
            {
                "capability": capability,
                "status": status,
                "track": track,
                "source": _TRACK_SOURCE[track],
                "support_status": support_level,
                "selected_scenarios": capability_selected_scenarios,
                "supported_scenarios": supported_scenarios,
                "is_active": capability in active_capabilities,
                "notes": _GLOBAL_CAPABILITY_NOTES.get(capability, ""),
                "selected": capability in active_capabilities,
            }
        )

    return matrix


def build_static_coverage_audit() -> dict[str, Any]:
    """Describe overall framework support independent of a specific extension."""

    official_matrix = _build_static_track_matrix(_OFFICIAL_TRACK)
    heuristic_matrix = _build_static_track_matrix(_HEURISTIC_TRACK)

    return {
        "summary": _summarize_coverage_matrix(official_matrix),
        "matrix": official_matrix,
        "coverage_tracks": {
            _OFFICIAL_TRACK: {
                "source": _TRACK_SOURCE[_OFFICIAL_TRACK],
                "summary": _summarize_coverage_matrix(official_matrix),
                "matrix": official_matrix,
            },
            _HEURISTIC_TRACK: {
                "source": _TRACK_SOURCE[_HEURISTIC_TRACK],
                "summary": _summarize_coverage_matrix(heuristic_matrix),
                "matrix": heuristic_matrix,
            },
        },
        "official_event_registry": [
            _serialize_event_strategy(strategy)
            for strategy in OFFICIAL_EVENT_REGISTRY.values()
        ],
        "scenarios": [
            _serialize_scenario_definition(scenario, [])
            for scenario in SCENARIO_REGISTRY
        ],
    }


def write_trigger_file(
    publisher: str,
    name: str,
    version: str,
    payload: TriggerPayload,
    output_dir: str = "output",
) -> str:
    """Write trigger payload to a JSON file on the shared volume."""

    filename = f"triggers_{publisher}.{name}-{version}.json"
    host_path = Path(output_dir) / filename
    host_path.parent.mkdir(parents=True, exist_ok=True)
    host_path.write_text(json.dumps(asdict(payload), indent=2), encoding="utf-8")
    return f"/results/{filename}"


def _order_scenarios(selected: set[str], scores: dict[str, int]) -> list[str]:
    ordered = sorted(
        selected,
        key=lambda name: (-scores.get(name, 0), _SCENARIO_PRIORITY.index(name)),
    )
    return ordered[:_MAX_SCENARIOS_PER_RUN]


def _collect_active_capabilities(
    selected_scenarios: list[str],
    *,
    payload: TriggerPayload,
    track: str,
    extra_capabilities: set[str] | None = None,
) -> list[str]:
    support_map = (
        _OFFICIAL_CAPABILITY_SUPPORT
        if track == _OFFICIAL_TRACK
        else _HEURISTIC_CAPABILITY_SUPPORT
    )
    capabilities: set[str] = set()
    for scenario_name in selected_scenarios:
        capabilities.update(_SCENARIO_BY_NAME[scenario_name].api_capabilities)
    for attempt in payload.event_attempts:
        if attempt.get("track") != track:
            continue
        if track == _OFFICIAL_TRACK and attempt.get("event_family") in {
            "*",
            "onStartupFinished",
        }:
            continue
        capabilities.update(
            str(item)
            for item in attempt.get("capability_tags", [])
            if str(item).strip()
        )
    if payload.extra_commands and track == _HEURISTIC_TRACK:
        capabilities.add("commands")
    if payload.extra_custom_editor_files:
        capabilities.add("custom_editors")
    if payload.extra_notebook_files and track == _OFFICIAL_TRACK:
        capabilities.add("notebooks")
    if payload.run_task_trigger and track == _OFFICIAL_TRACK:
        capabilities.add("terminal_tasks")
    if (
        payload.run_walkthrough_trigger or payload.uri_trigger
    ) and track == _OFFICIAL_TRACK:
        capabilities.add("uri_walkthrough")
    if "authentication_probe" in selected_scenarios:
        capabilities.add("authentication")
    if "webview_probe" in selected_scenarios:
        capabilities.add("webview")
    if extra_capabilities:
        capabilities.update(extra_capabilities)
    return sorted(
        capability
        for capability in capabilities
        if support_map.get(capability, "missing") == "covered"
    )


def _build_static_track_matrix(track: str) -> list[dict[str, Any]]:
    support_map = (
        _OFFICIAL_CAPABILITY_SUPPORT
        if track == _OFFICIAL_TRACK
        else _HEURISTIC_CAPABILITY_SUPPORT
    )
    return [
        {
            "capability": capability,
            "status": support_map[capability],
            "track": track,
            "source": _TRACK_SOURCE[track],
            "support_status": support_map[capability],
            "supported_scenarios": [
                scenario.name
                for scenario in SCENARIO_REGISTRY
                if capability in scenario.api_capabilities
            ],
            "notes": _GLOBAL_CAPABILITY_NOTES.get(capability, ""),
            "selected": False,
            "is_active": False,
            "selected_scenarios": [],
        }
        for capability in CAPABILITY_TAXONOMY
    ]


def _build_event_attempt(
    *,
    strategy: EventStrategy,
    event_type: str,
    event_value: str | None,
    track: str,
    reason: str,
    publisher_name: str | None,
    selected_by: str,
) -> dict[str, Any]:
    activation_event = _activation_label(event_type, event_value)
    executor_action = _resolve_executor_action(
        strategy.family,
        event_value,
        publisher_name=publisher_name,
    )
    backfill_executor_action = (
        f"harness:{strategy.harness_fallback}" if strategy.harness_fallback else ""
    )
    pass_name = _choose_primary_pass(strategy.family, track)
    backfill_pass_name = "unresolved_event_backfill" if backfill_executor_action else ""
    return {
        "attempt_id": _slugify(f"{track}-{activation_event}"),
        "declared_event": activation_event,
        "activation_event": activation_event,
        "event_family": strategy.family,
        "event_value": str(event_value or ""),
        "track": track,
        "selected_by": selected_by,
        "selection_reasons": [reason],
        "pass_name": pass_name,
        "backfill_pass_name": backfill_pass_name,
        "prerequisite_keys": list(strategy.prerequisites),
        "verification_contract": list(strategy.verification_contract),
        "trigger_method": _choose_trigger_method(strategy.family, executor_action),
        "fallback_trigger_method": "harness_api" if backfill_executor_action else "",
        "executor_action": executor_action,
        "backfill_executor_action": backfill_executor_action,
        "legacy_scenarios": list(strategy.legacy_scenarios),
        "capability_tags": list(strategy.capability_tags),
        "status": "planned",
        "trigger_method_used": "",
        "attempted_passes": [],
        "evidence": [],
        "verification_status": "not_attempted",
        "failure_reason_code": "",
        "blocked_reason_code": "",
        "result_details": "",
        "official": track == _OFFICIAL_TRACK,
        "heuristic": track == _HEURISTIC_TRACK,
        "ui_path": strategy.ui_path,
        "harness_fallback": strategy.harness_fallback or "",
    }


def _build_stimulus_passes(
    event_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    passes: dict[str, dict[str, Any]] = {
        pass_name: {
            "pass_id": pass_name,
            "label": _PASS_LABELS[pass_name],
            "order": index,
            "description": _PASS_DESCRIPTIONS[pass_name],
            "attempt_ids": [],
            "prerequisite_keys": [],
        }
        for index, pass_name in enumerate(_PASS_ORDER, start=1)
    }
    for attempt in event_attempts:
        pass_name = str(attempt.get("pass_name", "")).strip()
        if pass_name in passes:
            passes[pass_name]["attempt_ids"].append(str(attempt.get("attempt_id", "")))
            passes[pass_name]["prerequisite_keys"].extend(
                str(item) for item in attempt.get("prerequisite_keys", [])
            )
        backfill_pass = str(attempt.get("backfill_pass_name", "")).strip()
        if backfill_pass in passes and attempt.get("backfill_executor_action"):
            passes[backfill_pass]["attempt_ids"].append(
                str(attempt.get("attempt_id", ""))
            )
            passes[backfill_pass]["prerequisite_keys"].extend(
                str(item) for item in attempt.get("prerequisite_keys", [])
            )
    for pass_data in passes.values():
        pass_data["attempt_ids"] = [
            attempt_id
            for attempt_id in dict.fromkeys(pass_data["attempt_ids"])
            if attempt_id
        ]
        pass_data["prerequisite_keys"] = [
            item for item in dict.fromkeys(pass_data["prerequisite_keys"]) if item
        ]
        pass_data["status"] = "planned"
    return [passes[pass_name] for pass_name in _PASS_ORDER]


def _build_prerequisite_results(
    event_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prerequisites: dict[str, dict[str, Any]] = {}
    for attempt in event_attempts:
        attempt_id = str(attempt.get("attempt_id", ""))
        pass_name = str(attempt.get("pass_name", ""))
        for key in attempt.get("prerequisite_keys", []):
            prep_key = str(key).strip()
            if not prep_key:
                continue
            entry = prerequisites.setdefault(
                prep_key,
                {
                    "prerequisite_id": _slugify(f"prep-{prep_key}"),
                    "key": prep_key,
                    "label": prep_key.replace("_", " "),
                    "status": "planned",
                    "materializer": _materializer_for_prerequisite(prep_key),
                    "pass_name": pass_name,
                    "attempt_ids": [],
                    "detail": _detail_for_prerequisite(prep_key),
                },
            )
            entry["attempt_ids"].append(attempt_id)
    return [
        {
            **value,
            "attempt_ids": [
                attempt_id
                for attempt_id in dict.fromkeys(value["attempt_ids"])
                if attempt_id
            ],
        }
        for value in prerequisites.values()
    ]


def _summarize_event_attempts(
    attempts: list[dict[str, Any]],
    *,
    track: str,
) -> dict[str, Any]:
    selected = [attempt for attempt in attempts if attempt.get("track") == track]
    verified = [attempt for attempt in selected if attempt.get("status") == "verified"]
    attempted_only = [
        attempt for attempt in selected if attempt.get("status") == "attempted_only"
    ]
    failed = [attempt for attempt in selected if attempt.get("status") == "failed"]
    blocked = [attempt for attempt in selected if attempt.get("status") == "blocked"]
    return {
        "track": track,
        "declared": len(selected),
        "verified": len(verified),
        "attempted_only": len(attempted_only),
        "failed": len(failed),
        "blocked": len(blocked),
        "unresolved": max(len(selected) - len(verified), 0),
        "declared_events": [
            str(attempt.get("activation_event", ""))
            for attempt in selected
            if str(attempt.get("activation_event", "")).strip()
        ],
    }


def _choose_primary_pass(family: str, track: str) -> str:
    if track == _HEURISTIC_TRACK:
        return "ui_first_user_session"
    if family in {"workspaceContains", "*", "onStartupFinished"}:
        return "workspace_bootstrap"
    if family in {"onLanguage", "onCommand", "onSearch", "onView"}:
        return "ui_first_user_session"
    return "target_specific_activation"


def _choose_trigger_method(family: str, executor_action: str) -> str:
    if family in {"onCustomEditor", "workspaceContains"}:
        return "mixed"
    if executor_action.startswith("scenario:") or executor_action.startswith(
        "command:"
    ):
        return "ui_simulation"
    if executor_action.startswith("extra:"):
        return "mixed"
    if executor_action.startswith("harness:"):
        return "harness_api"
    if executor_action.startswith("fixture:"):
        return "workspace_fixture"
    return "ui_simulation"


def _resolve_executor_action(
    family: str,
    event_value: str | None,
    *,
    publisher_name: str | None,
) -> str:
    value = str(event_value or "").strip()
    if family == "onCommand":
        return "scenario:coding_session" if not value else "command:auto"
    if family == "onLanguage":
        return "scenario:coding_session"
    if family in {
        "onDebug",
        "onDebugAdapterProtocolTracker",
        "onDebugDynamicConfigurations",
        "onDebugInitialConfigurations",
        "onDebugResolve",
    }:
        return "extra:debug_lifecycle"
    if family == "workspaceContains":
        return "scenario:project_exploration"
    if family in {"onNotebook", "onRenderer"}:
        return "scenario:notebook_session"
    if family == "onTaskType":
        return "extra:task_trigger"
    if family in {"onTerminal", "onTerminalProfile", "onTerminalShellIntegration"}:
        return "scenario:terminal_usage"
    if family == "onAuthenticationRequest":
        return "harness:run_current_stimulus"
    if family in {"onChatParticipant", "onLanguageModelTool"}:
        return "harness:run_current_stimulus"
    if family == "onWebviewPanel":
        return "harness:run_current_stimulus"
    if family == "onWalkthrough":
        return "extra:walkthrough"
    if family == "onOpenExternalUri":
        return "harness:run_current_stimulus"
    if family == "onUri":
        if publisher_name:
            return "extra:uri_trigger"
        return "harness:run_current_stimulus"
    if family == "onCustomEditor":
        return "extra:custom_editor"
    if family == "onFileSystem":
        return "harness:run_current_stimulus"
    if family == "onEditSession":
        return "harness:run_current_stimulus"
    if family == "onIssueReporterOpened":
        return "command:Help: Report Issue"
    if family == "onSearch":
        return "scenario:search_workflow"
    if family in {"onStartupFinished", "*"}:
        return "fixture:startup_observe"
    if family == "onView":
        if value in _BUILTIN_VIEW_IDS:
            return f"command:View: Show {value}"
        return "harness:run_current_stimulus"
    return "harness:run_current_stimulus"


def _materializer_for_prerequisite(key: str) -> str:
    if key in {
        "language_fixture",
        "workspace_contains_fixture",
        "searchable_workspace",
    }:
        return "workspace_fixture"
    if key in {"custom_editor_bait_files", "notebook_fixture", "renderer_fixture"}:
        return "workspace_fixture"
    if key in {"debug_launch_config", "task_definition_target"}:
        return "workspace_fixture"
    return "harness_api"


def _detail_for_prerequisite(key: str) -> str:
    details = {
        "auth_request_target": (
            "Provider or consumer id must be available inside the sandbox."
        ),
        "chat_participant_target": (
            "Chat participant id is staged for local-only invocation."
        ),
        "command_target": (
            "Command title/id is resolved through contributes.commands when present."
        ),
        "custom_editor_bait_files": (
            "Create bait files that match contributes.customEditors selectors."
        ),
        "debug_launch_config": (
            "Ensure launch.json and debuggable files exist before the debug flow."
        ),
        "edit_session_fixture": (
            "Prepare edit-session commands or local stubs before stimulation."
        ),
        "filesystem_scheme_target": (
            "Custom filesystem scheme must be reachable locally."
        ),
        "language_fixture": (
            "Prepare a file that resolves to the declared language id."
        ),
        "language_model_tool_target": (
            "Language-model tool id is prepared for local-only invocation."
        ),
        "notebook_fixture": (
            "Create a notebook document and any required output content."
        ),
        "loopback_uri_target": (
            "Use a loopback-only URI target; no external service calls are allowed."
        ),
        "renderer_fixture": (
            "Materialize notebook output so renderer activation can be observed."
        ),
        "searchable_workspace": (
            "Prepare a workspace tree that VS Code can search deterministically."
        ),
        "task_definition_target": (
            "Task definitions must exist before Tasks: Run Task is invoked."
        ),
        "terminal_profile_target": (
            "Terminal profile ids must be available before profile launch."
        ),
        "terminal_shell_target": (
            "Terminal shell type must be selected before the terminal opens."
        ),
        "uri_target": (
            "Target vscode:// URI is staged from the publisher.name identifier."
        ),
        "view_target": "The contributed view id is prepared for expansion.",
        "walkthrough_target": (
            "Walkthrough id is prepared for the Getting Started flow."
        ),
        "webview_target": (
            "Restore context for the target webview panel before backfill."
        ),
        "workspace_contains_fixture": (
            "Create the file pattern expected by workspaceContains."
        ),
        "workspace_ready": (
            "VS Code workbench must finish loading before startup events are assessed."
        ),
    }
    return details.get(key, "")


def _collect_contributed_view_ids(contributes_views: dict[str, Any] | None) -> set[str]:
    view_ids: set[str] = set()
    if not contributes_views:
        return view_ids
    for views in contributes_views.values():
        if not isinstance(views, list):
            continue
        for view in views:
            if not isinstance(view, dict):
                continue
            view_id = view.get("id")
            if view_id:
                view_ids.add(str(view_id))
    return view_ids


def _serialize_scenario_definition(
    scenario: ScenarioDefinition,
    selection_reasons: list[str],
) -> dict[str, Any]:
    return {
        "name": scenario.name,
        "intent": scenario.intent,
        "activation_events": list(scenario.activation_events),
        "contributes_signals": list(scenario.contributes_signals),
        "api_capabilities": list(scenario.api_capabilities),
        "prerequisites": list(scenario.prerequisites),
        "success_signals": list(scenario.success_signals),
        "risk_of_noise": scenario.risk_of_noise,
        "selection_reasons": selection_reasons,
    }


def _serialize_event_strategy(strategy: EventStrategy) -> dict[str, Any]:
    return {
        "family": strategy.family,
        "capability_tags": list(strategy.capability_tags),
        "executor_group": strategy.executor_group,
        "prerequisites": list(strategy.prerequisites),
        "verification_contract": list(strategy.verification_contract),
        "legacy_scenarios": list(strategy.legacy_scenarios),
        "ui_path": strategy.ui_path,
        "harness_fallback": strategy.harness_fallback or "",
        "official": strategy.official,
        "heuristic": strategy.heuristic,
    }


def _summarize_coverage_matrix(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    covered = [
        entry["capability"] for entry in matrix if entry.get("status") == "covered"
    ]
    partial = [
        entry["capability"] for entry in matrix if entry.get("status") == "partial"
    ]
    missing = [
        entry["capability"] for entry in matrix if entry.get("status") == "missing"
    ]
    return {
        "covered": len(covered),
        "partial": len(partial),
        "missing": len(missing),
        "covered_capabilities": covered,
        "partial_capabilities": partial,
        "missing_capabilities": missing,
    }


def _activation_label(event_type: str, event_value: str | None) -> str:
    if event_value:
        return f"{event_type}:{event_value}"
    return event_type


def _glob_to_bait_filename(pattern: str) -> str | None:
    """Convert a VS Code filenamePattern glob to a concrete bait filename."""

    name_part = pattern.rsplit("/", maxsplit=1)[-1]

    if name_part.startswith("*."):
        ext = name_part[2:]
        if ext.startswith("{") and "}" in ext:
            ext = ext[1 : ext.index("}")]
            if "," in ext:
                ext = ext.split(",")[0]
        return f"bait.{ext}"

    if "*" not in name_part and "?" not in name_part:
        return name_part

    return None


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()


__all__ = [
    "CAPABILITY_TAXONOMY",
    "EVENT_TYPE_TO_SCENARIOS",
    "OFFICIAL_EVENT_REGISTRY",
    "SCENARIO_REGISTRY",
    "ScenarioDefinition",
    "TriggerPayload",
    "_glob_to_bait_filename",
    "build_coverage_matrix",
    "build_static_coverage_audit",
    "select_scenarios",
    "write_trigger_file",
]
