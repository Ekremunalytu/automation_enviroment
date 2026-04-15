"""State-free planner registries and support maps."""

from __future__ import annotations

from dataclasses import dataclass

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
        ui_path="Open a file that resolves to the requested language id",
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
