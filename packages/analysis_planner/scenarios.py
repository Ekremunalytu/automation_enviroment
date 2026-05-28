"""Scenario definitions and lookup helpers.

W10-3 split from former monolithic ``registry.py``. Pure data; no behavior.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    ScenarioDefinition(
        name="workspace_trust_transition",
        intent=(
            "Capture workspace trust transitions for extensions that declare "
            "untrusted-workspace support, recording baseline state and "
            "trust-granted events through the harness."
        ),
        activation_events=("onStartupFinished",),
        contributes_signals=("capabilities",),
        api_capabilities=("commands", "window_ui", "workspace_trust"),
        prerequisites=("workspace trust API available",),
        success_signals=("workspace trust baseline", "workspace trust granted"),
        risk_of_noise="low",
    ),
    ScenarioDefinition(
        name="local_test_controller",
        intent=(
            "Exercise the local VS Code Test Controller surface "
            "(TestItems + run/debug profiles) through the harness so "
            "extensions that contribute test discovery have a verifiable "
            "coverage path without calling external test services."
        ),
        activation_events=("onStartupFinished",),
        contributes_signals=("capabilities",),
        api_capabilities=("commands", "window_ui", "testing"),
        prerequisites=("test controller API available",),
        success_signals=("test run invoked", "test debug invoked"),
        risk_of_noise="low",
    ),
    ScenarioDefinition(
        name="local_comments_controller",
        intent=(
            "Exercise the local VS Code Comments API surface "
            "(CommentController + CommentThread create/dispose) through "
            "the harness so extensions that contribute discussion flows "
            "have a verifiable coverage path while staying inside the "
            "sandbox."
        ),
        activation_events=("onStartupFinished",),
        contributes_signals=("capabilities",),
        api_capabilities=("commands", "window_ui", "comments"),
        prerequisites=("comments API available",),
        success_signals=("comment thread created", "comment thread disposed"),
        risk_of_noise="low",
    ),
    ScenarioDefinition(
        name="local_chat_participant_controller",
        intent=(
            "Exercise the local VS Code Chat Participant API surface "
            "(vscode.chat.createChatParticipant + no-op handler) through "
            "the harness so extensions that contribute chat participants "
            "have a verifiable coverage path while staying inside the "
            "sandbox. Per ADR 0014 Option C: registration alone fires "
            "the onChatParticipant:* activation event family; no chat "
            "model interaction occurs."
        ),
        activation_events=("onStartupFinished",),
        contributes_signals=("capabilities",),
        api_capabilities=("commands", "window_ui", "chat"),
        prerequisites=("chat participant API available",),
        success_signals=(
            "chat participant registered",
            "chat participant disposed",
        ),
        risk_of_noise="low",
    ),
    ScenarioDefinition(
        name="local_language_model_tool_controller",
        intent=(
            "Exercise the local VS Code Language Model Tool API surface "
            "(vscode.lm.registerTool + vscode.lm.invokeTool against a "
            "no-op tool) through the harness so extensions that "
            "contribute LM tools have a verifiable coverage path while "
            "staying inside the sandbox. Per ADR 0014 Option C: tool "
            "registration + invocation fire the onLanguageModelTool:* "
            "activation event family without any chat-model round-trip; "
            "the invoke handler returns a canned LanguageModelToolResult."
        ),
        activation_events=("onStartupFinished",),
        contributes_signals=("capabilities",),
        api_capabilities=("commands", "window_ui", "chat"),
        prerequisites=("language model tool API available",),
        success_signals=(
            "lm tool registered",
            "lm tool invoked",
            "lm tool disposed",
        ),
        risk_of_noise="low",
    ),
)


_SCENARIO_BY_NAME: dict[str, ScenarioDefinition] = {
    scenario.name: scenario for scenario in SCENARIO_REGISTRY
}
_SCENARIO_PRIORITY: list[str] = [scenario.name for scenario in SCENARIO_REGISTRY]
