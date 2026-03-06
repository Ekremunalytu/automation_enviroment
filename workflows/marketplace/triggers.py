"""Trigger selection helpers for the marketplace analysis workflow."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class TriggerPayload:
    """Data passed from host to container to guide scenario selection."""

    selected_scenarios: list[str] = field(default_factory=list)
    extra_notebook_files: list[str] = field(default_factory=list)
    extra_custom_editor_files: list[str] = field(default_factory=list)
    extra_commands: list[str] = field(default_factory=list)
    uri_trigger: str | None = None
    run_task_trigger: bool = False
    run_walkthrough_trigger: bool = False


# -------------------------------------------------------------------------
# Event type → scenario mapping
# -------------------------------------------------------------------------

EVENT_TYPE_TO_SCENARIOS: dict[str, list[str]] = {
    "onLanguage": ["coding_session", "project_exploration"],
    "onCommand": ["coding_session"],
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
    "onWalkthrough": [],
    "onUri": [],
    "onCustomEditor": [],
    "*": [],  # wildcard = all scenarios (handled specially)
    "onStartupFinished": [],  # same as wildcard
}

# All known scenario names for the wildcard / fallback case
_ALL_SCENARIO_NAMES: list[str] = [
    "coding_session",
    "debug_session",
    "terminal_usage",
    "git_workflow",
    "extension_browsing",
    "settings_modification",
    "project_exploration",
    "search_workflow",
    "diagnostics_check",
    "refactor_workflow",
    "notebook_session",
]


def select_scenarios(
    activation_events: list[dict[str, str | None]],
    contributes_custom_editors: list[dict] | None = None,
    publisher_name: str | None = None,
    contributes_commands: list[dict] | None = None,
) -> TriggerPayload:
    """Select automation scenarios based on an extension's activation events.

    Args:
        activation_events: List of dicts with ``event_type`` and ``event_value``.
        contributes_custom_editors: Optional ``contributes.customEditors`` JSON
            from the database (list of objects with ``viewType``, ``selector``).
        publisher_name: Publisher.name identifier (used for onUri scheme).

    Returns:
        A TriggerPayload with the scenarios and extra triggers to run.
    """
    scenarios: set[str] = set()
    payload = TriggerPayload()

    for event in activation_events:
        event_type = event.get("event_type", "")
        event_value = event.get("event_value")

        # Handle wildcard / onStartupFinished → run everything
        if event_type in ("*", "onStartupFinished"):
            scenarios.update(_ALL_SCENARIO_NAMES)
            continue

        # Handle onView:* (the event_type in DB is "onView", value is the view id)
        if event_type == "onView" and event_value:
            key = f"onView:{event_value}"
            if key in EVENT_TYPE_TO_SCENARIOS:
                scenarios.update(EVENT_TYPE_TO_SCENARIOS[key])
            else:
                # Unknown view — at least run project_exploration
                scenarios.add("project_exploration")
            continue

        # Standard mapping
        if event_type in EVENT_TYPE_TO_SCENARIOS:
            scenarios.update(EVENT_TYPE_TO_SCENARIOS[event_type])

        # Extra triggers that don't map to a named scenario
        if event_type == "onNotebook":
            payload.extra_notebook_files.append("notebooks/analysis.ipynb")

        if event_type == "onTaskType":
            payload.run_task_trigger = True

        if event_type == "onWalkthrough":
            payload.run_walkthrough_trigger = True

        if event_type == "onUri" and publisher_name:
            payload.uri_trigger = f"vscode://{publisher_name}/activate"

    # Build custom editor bait files from contributes.customEditors
    if contributes_custom_editors:
        for ce in contributes_custom_editors:
            selectors = ce.get("selector", [])
            for sel in selectors:
                glob_pattern = sel.get("filenamePattern", "")
                if glob_pattern:
                    # Convert glob to a concrete filename
                    bait = _glob_to_bait_filename(glob_pattern)
                    if bait:
                        payload.extra_custom_editor_files.append(bait)

    # Collect extension-specific commands from contributes.commands
    if contributes_commands:
        for cmd in contributes_commands:
            title = cmd.get("title", "")
            if title:
                payload.extra_commands.append(title)

    # If no scenarios were selected, fall back to coding_session
    if not scenarios:
        scenarios.add("coding_session")

    payload.selected_scenarios = sorted(scenarios)
    return payload


def write_trigger_file(
    publisher: str,
    name: str,
    version: str,
    payload: TriggerPayload,
    output_dir: str = "output",
) -> str:
    """Write trigger payload to a JSON file on the shared volume.

    Args:
        publisher: Extension publisher.
        name: Extension name.
        version: Extension version.
        payload: The trigger payload to write.
        output_dir: Host-side output directory (mapped to /results in container).

    Returns:
        Container path to the trigger file.
    """
    filename = f"triggers_{publisher}.{name}-{version}.json"
    host_path = Path(output_dir) / filename
    host_path.parent.mkdir(parents=True, exist_ok=True)
    host_path.write_text(json.dumps(asdict(payload), indent=2))
    return f"/results/{filename}"


def _glob_to_bait_filename(pattern: str) -> str | None:
    """Convert a VS Code filenamePattern glob to a concrete bait filename.

    Examples:
        "*.myext"  → "bait.myext"
        "*.{png,jpg}" → "bait.png"
        "**/*.csv" → "data/bait.csv"
    """
    # Strip leading directory patterns
    name_part = pattern.rsplit("/", maxsplit=1)[-1]

    if name_part.startswith("*."):
        ext = name_part[2:]
        # Handle brace expansion: take first option
        if ext.startswith("{") and "}" in ext:
            ext = ext[1 : ext.index("}")]
            if "," in ext:
                ext = ext.split(",")[0]
        return f"bait.{ext}"

    # If it's a concrete filename, use as-is
    if "*" not in name_part and "?" not in name_part:
        return name_part

    return None
