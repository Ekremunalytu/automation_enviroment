"""
Container-side trigger payload loading.

Reads the JSON trigger file written by the host-side ``scanner.triggers``
module and returns a ``TriggerPayload`` so the entrypoint can select
scenarios and run extra activation triggers.
"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TriggerPayload:
    """Mirror of ``scanner.triggers.TriggerPayload``."""

    analysis_profile: str = "layered_deep"
    selected_scenarios: list[str] = field(default_factory=list)
    official_selected_scenarios: list[str] = field(default_factory=list)
    heuristic_selected_scenarios: list[str] = field(default_factory=list)
    selected_scenario_details: list[dict[str, object]] = field(default_factory=list)
    selection_reasons: dict[str, list[str]] = field(default_factory=dict)
    coverage_tracks: dict[str, dict[str, object]] = field(default_factory=dict)
    coverage_summary: dict[str, object] = field(default_factory=dict)
    coverage_matrix: list[dict[str, object]] = field(default_factory=list)
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
    stimulus_passes: list[dict[str, object]] = field(default_factory=list)
    event_attempts: list[dict[str, object]] = field(default_factory=list)
    prerequisite_results: list[dict[str, object]] = field(default_factory=list)
    official_event_coverage: dict[str, object] = field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, object] = field(default_factory=dict)


def load_trigger_file(path: str) -> TriggerPayload | None:
    """Load a trigger payload from a JSON file.

    Args:
        path: Absolute path to the trigger JSON file inside the container.

    Returns:
        A ``TriggerPayload`` if the file exists and is valid, otherwise ``None``.
    """
    p = Path(path)
    if not p.exists():
        return None

    try:
        data = json.loads(p.read_text())
        if not isinstance(data, dict):
            return None
        payload = TriggerPayload(
            analysis_profile=str(data.get("analysis_profile", "layered_deep")),
            selected_scenarios=data.get("selected_scenarios", []),
            official_selected_scenarios=data.get("official_selected_scenarios", []),
            heuristic_selected_scenarios=data.get(
                "heuristic_selected_scenarios",
                [],
            ),
            selected_scenario_details=data.get("selected_scenario_details", []),
            selection_reasons=data.get("selection_reasons", {}),
            coverage_tracks=data.get("coverage_tracks", {}),
            coverage_summary=data.get("coverage_summary", {}),
            coverage_matrix=data.get("coverage_matrix", []),
            official_attempted_capabilities=data.get(
                "official_attempted_capabilities",
                [],
            ),
            heuristic_attempted_capabilities=data.get(
                "heuristic_attempted_capabilities",
                [],
            ),
            target_extension_id=data.get("target_extension_id"),
            command_targets=data.get("command_targets", {}),
            view_targets=data.get("view_targets", {}),
            extra_notebook_files=data.get("extra_notebook_files", []),
            extra_custom_editor_files=data.get("extra_custom_editor_files", []),
            extra_commands=data.get("extra_commands", []),
            auth_provider_ids=data.get("auth_provider_ids", []),
            webview_view_ids=data.get("webview_view_ids", []),
            uri_trigger=data.get("uri_trigger"),
            run_task_trigger=data.get("run_task_trigger", False),
            run_walkthrough_trigger=data.get("run_walkthrough_trigger", False),
            stimulus_passes=data.get("stimulus_passes", []),
            event_attempts=data.get("event_attempts", []),
            prerequisite_results=data.get("prerequisite_results", []),
            official_event_coverage=data.get("official_event_coverage", {}),
            heuristic_workflow_coverage=data.get(
                "heuristic_workflow_coverage",
                {},
            ),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    finally:
        # Clean up the trigger file after reading
        with contextlib.suppress(OSError):
            p.unlink()

    return payload
