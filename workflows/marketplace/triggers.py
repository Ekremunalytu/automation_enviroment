"""Trigger selection helpers for the marketplace analysis workflow."""

from __future__ import annotations

import json
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
    "custom_editors": "partial",
    "uri_walkthrough": "partial",
    "authentication": "covered",
    "chat": "missing",
    "comments": "missing",
    "testing": "missing",
    "webview": "covered",
    "workspace_trust": "missing",
}

_GLOBAL_CAPABILITY_NOTES: dict[str, str] = {
    "custom_editors": (
        "Custom editor coverage is bait-file driven and does not verify "
        "target-specific "
        "editor behavior deeply."
    ),
    "uri_walkthrough": (
        "URI and walkthrough triggers are exercised through generic launch flows only."
    ),
    "authentication": (
        "Authentication coverage exercises provider and account flows, but still "
        "depends on generic VS Code account surfaces rather than provider-specific "
        "consent automation."
    ),
    "chat": "Chat participant and chat UI automation do not exist yet.",
    "comments": "Comments panel and thread interactions are not automated yet.",
    "testing": "Testing API and test explorer workflows are not automated yet.",
    "webview": (
        "Webview coverage exercises preview and panel surfaces, but target-specific "
        "DOM assertions remain best-effort."
    ),
    "workspace_trust": (
        "Workspace trust prompts and trust-state transitions are not covered."
    ),
}


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
        activation_events=("onView:search",),
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
        activation_events=("onTaskType", "onTerminalProfile"),
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
        activation_events=("onNotebook",),
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
        activation_events=("onWebviewPanel",),
        contributes_signals=("commands", "views", "viewsWelcome"),
        api_capabilities=("commands", "window_ui", "webview"),
        prerequisites=("previewable workspace file available",),
        success_signals=("preview open", "webview surface"),
        risk_of_noise="medium",
    ),
)

_SCENARIO_BY_NAME = {scenario.name: scenario for scenario in SCENARIO_REGISTRY}
_SCENARIO_PRIORITY = [scenario.name for scenario in SCENARIO_REGISTRY]


@dataclass
class TriggerPayload:
    """Data passed from host to container to guide scenario selection."""

    selected_scenarios: list[str] = field(default_factory=list)
    selected_scenario_details: list[dict[str, Any]] = field(default_factory=list)
    selection_reasons: dict[str, list[str]] = field(default_factory=dict)
    coverage_summary: dict[str, Any] = field(default_factory=dict)
    coverage_matrix: list[dict[str, Any]] = field(default_factory=list)
    target_extension_id: str | None = None
    extra_notebook_files: list[str] = field(default_factory=list)
    extra_custom_editor_files: list[str] = field(default_factory=list)
    extra_commands: list[str] = field(default_factory=list)
    auth_provider_ids: list[str] = field(default_factory=list)
    webview_view_ids: list[str] = field(default_factory=list)
    uri_trigger: str | None = None
    run_task_trigger: bool = False
    run_walkthrough_trigger: bool = False


EVENT_TYPE_TO_SCENARIOS: dict[str, list[str]] = {
    "onLanguage": ["coding_session", "project_exploration"],
    "onCommand": ["coding_session", "refactor_workflow"],
    "onDebug": ["debug_session"],
    "onDebugResolve": ["debug_session"],
    "onDebugAdapterProtocolTracker": ["debug_session"],
    "onView:scm": ["git_workflow"],
    "onView:extensions": ["extension_browsing"],
    "onView:explorer": ["project_exploration"],
    "onView:search": ["search_workflow"],
    "onView:output": ["diagnostics_check"],
    "onConfiguration": ["settings_modification"],
    "workspaceContains": ["project_exploration"],
    "onNotebook": ["notebook_session"],
    "onTaskType": ["terminal_usage"],
    "onTerminalProfile": ["terminal_usage"],
    "onAuthenticationRequest": ["authentication_probe"],
    "onWebviewPanel": ["webview_probe"],
    "onWalkthrough": [],
    "onUri": [],
    "onCustomEditor": [],
    "*": [],
    "onStartupFinished": [],
}

_MAX_SCENARIOS_PER_RUN = 5
_MAX_EXTRA_COMMANDS = 6


def select_scenarios(
    activation_events: list[dict[str, str | None]],
    contributes_custom_editors: list[dict] | None = None,
    publisher_name: str | None = None,
    contributes_commands: list[dict] | None = None,
    contributes_authentication: list[dict] | None = None,
    contributes_views: dict[str, Any] | None = None,
) -> TriggerPayload:
    """Select automation scenarios based on an extension's activation events."""
    selected: set[str] = set()
    scenario_scores: dict[str, int] = {}
    scenario_reasons: dict[str, set[str]] = {}
    payload = TriggerPayload(target_extension_id=publisher_name)

    def mark_scenario(name: str, *, reason: str, score: int) -> None:
        if name not in _SCENARIO_BY_NAME:
            return
        selected.add(name)
        scenario_scores[name] = max(score, scenario_scores.get(name, 0))
        scenario_reasons.setdefault(name, set()).add(reason)

    for event in activation_events:
        event_type = event.get("event_type", "") or ""
        event_value = event.get("event_value")
        event_label = (
            f"{event_type}:{event_value}"
            if event_value and event_type != "onView"
            else event_type
        )

        if event_type in {"*", "onStartupFinished"}:
            for index, scenario_name in enumerate(_SCENARIO_PRIORITY):
                mark_scenario(
                    scenario_name,
                    reason=f"activation {event_type} requests broad workspace coverage",
                    score=10_000 - index,
                )
            continue

        if event_type == "onView" and event_value:
            key = f"onView:{event_value}"
            mapped = EVENT_TYPE_TO_SCENARIOS.get(key)
            if mapped:
                for index, scenario_name in enumerate(mapped):
                    mark_scenario(
                        scenario_name,
                        reason=f"view trigger {key}",
                        score=1_000 - index,
                    )
            else:
                mark_scenario(
                    "project_exploration",
                    reason=(
                        f"unmapped view trigger {key} fell back to explorer coverage"
                    ),
                    score=250,
                )
        elif event_type in EVENT_TYPE_TO_SCENARIOS:
            for index, scenario_name in enumerate(EVENT_TYPE_TO_SCENARIOS[event_type]):
                mark_scenario(
                    scenario_name,
                    reason=f"activation {event_label}",
                    score=900 - index,
                )

        if event_type == "onNotebook":
            payload.extra_notebook_files.append("notebooks/analysis.ipynb")
        if event_type == "onTaskType":
            payload.run_task_trigger = True
        if event_type == "onAuthenticationRequest":
            mark_scenario(
                "authentication_probe",
                reason=f"activation {event_label}",
                score=940,
            )
            if event_value:
                payload.auth_provider_ids.append(str(event_value))
        if event_type == "onWebviewPanel":
            mark_scenario(
                "webview_probe",
                reason=f"activation {event_label}",
                score=930,
            )
            if event_value:
                payload.webview_view_ids.append(str(event_value))
        if event_type == "onWalkthrough":
            payload.run_walkthrough_trigger = True
        if event_type == "onUri" and publisher_name:
            payload.uri_trigger = f"vscode://{publisher_name}/activate"

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

    if contributes_commands:
        for command in contributes_commands:
            title = command.get("title", "")
            if title:
                payload.extra_commands.append(title)

    if contributes_authentication:
        mark_scenario(
            "authentication_probe",
            reason="contributes.authentication advertised provider metadata",
            score=520,
        )
        for provider in contributes_authentication:
            provider_id = provider.get("auth_id") or provider.get("id") or ""
            if provider_id:
                payload.auth_provider_ids.append(str(provider_id))

    if contributes_views:
        if any(str(key).startswith("webview") for key in contributes_views):
            mark_scenario(
                "webview_probe",
                reason="contributes.views exposed a webview-oriented surface",
                score=510,
            )
        for _location, views in contributes_views.items():
            if not isinstance(views, list):
                continue
            for view in views:
                if not isinstance(view, dict):
                    continue
                view_id = view.get("id") or ""
                if view_id and "webview" in str(view_id).lower():
                    payload.webview_view_ids.append(str(view_id))

    if not selected:
        mark_scenario(
            "coding_session",
            reason=(
                "default fallback because activation metadata did not map to a "
                "stronger workflow"
            ),
            score=1,
        )

    payload.extra_commands = payload.extra_commands[:_MAX_EXTRA_COMMANDS]
    payload.auth_provider_ids = sorted(set(payload.auth_provider_ids))
    payload.webview_view_ids = sorted(set(payload.webview_view_ids))
    payload.selected_scenarios = _order_scenarios(selected, scenario_scores)
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
    payload.coverage_matrix = build_coverage_matrix(payload)
    payload.coverage_summary = _summarize_coverage_matrix(payload.coverage_matrix)
    return payload


def build_coverage_matrix(payload: TriggerPayload) -> list[dict[str, Any]]:
    """Build target-first coverage information for the selected payload."""
    active_capabilities = _collect_active_capabilities(payload)
    matrix: list[dict[str, Any]] = []

    for capability in CAPABILITY_TAXONOMY:
        supported_scenarios = [
            scenario.name
            for scenario in SCENARIO_REGISTRY
            if capability in scenario.api_capabilities
        ]
        selected_scenarios = [
            scenario_name
            for scenario_name in payload.selected_scenarios
            if capability in _SCENARIO_BY_NAME[scenario_name].api_capabilities
        ]
        support_level = _GLOBAL_CAPABILITY_SUPPORT[capability]
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
                "selected_scenarios": selected_scenarios,
                "supported_scenarios": supported_scenarios,
                "is_active": capability in active_capabilities,
                "notes": _GLOBAL_CAPABILITY_NOTES.get(capability, ""),
                "selected": capability in active_capabilities,
            }
        )

    return matrix


def build_static_coverage_audit() -> dict[str, Any]:
    """Describe overall framework support independent of a specific extension."""
    matrix: list[dict[str, Any]] = []
    for capability in CAPABILITY_TAXONOMY:
        supported_scenarios = [
            scenario.name
            for scenario in SCENARIO_REGISTRY
            if capability in scenario.api_capabilities
        ]
        matrix.append(
            {
                "capability": capability,
                "status": _GLOBAL_CAPABILITY_SUPPORT[capability],
                "supported_scenarios": supported_scenarios,
                "notes": _GLOBAL_CAPABILITY_NOTES.get(capability, ""),
            }
        )

    return {
        "summary": _summarize_coverage_matrix(matrix),
        "matrix": matrix,
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


def _collect_active_capabilities(payload: TriggerPayload) -> set[str]:
    capabilities: set[str] = set()
    for scenario_name in payload.selected_scenarios:
        capabilities.update(_SCENARIO_BY_NAME[scenario_name].api_capabilities)
    if payload.extra_commands:
        capabilities.add("commands")
    if payload.extra_custom_editor_files:
        capabilities.add("custom_editors")
    if payload.extra_notebook_files:
        capabilities.add("notebooks")
    if payload.run_task_trigger:
        capabilities.add("terminal_tasks")
    if payload.run_walkthrough_trigger or payload.uri_trigger:
        capabilities.add("uri_walkthrough")
    if (
        payload.auth_provider_ids
        or "authentication_probe" in payload.selected_scenarios
    ):
        capabilities.add("authentication")
    if payload.webview_view_ids or "webview_probe" in payload.selected_scenarios:
        capabilities.add("webview")
    return capabilities


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


__all__ = [
    "CAPABILITY_TAXONOMY",
    "EVENT_TYPE_TO_SCENARIOS",
    "SCENARIO_REGISTRY",
    "ScenarioDefinition",
    "TriggerPayload",
    "_glob_to_bait_filename",
    "build_coverage_matrix",
    "build_static_coverage_audit",
    "select_scenarios",
    "write_trigger_file",
]
