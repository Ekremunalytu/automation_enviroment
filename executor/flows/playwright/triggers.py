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

    selected_scenarios: list[str] = field(default_factory=list)
    selected_scenario_details: list[dict[str, object]] = field(default_factory=list)
    selection_reasons: dict[str, list[str]] = field(default_factory=dict)
    coverage_summary: dict[str, object] = field(default_factory=dict)
    coverage_matrix: list[dict[str, object]] = field(default_factory=list)
    target_extension_id: str | None = None
    extra_notebook_files: list[str] = field(default_factory=list)
    extra_custom_editor_files: list[str] = field(default_factory=list)
    extra_commands: list[str] = field(default_factory=list)
    auth_provider_ids: list[str] = field(default_factory=list)
    webview_view_ids: list[str] = field(default_factory=list)
    uri_trigger: str | None = None
    run_task_trigger: bool = False
    run_walkthrough_trigger: bool = False


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
        payload = TriggerPayload(
            selected_scenarios=data.get("selected_scenarios", []),
            selected_scenario_details=data.get("selected_scenario_details", []),
            selection_reasons=data.get("selection_reasons", {}),
            coverage_summary=data.get("coverage_summary", {}),
            coverage_matrix=data.get("coverage_matrix", []),
            target_extension_id=data.get("target_extension_id"),
            extra_notebook_files=data.get("extra_notebook_files", []),
            extra_custom_editor_files=data.get("extra_custom_editor_files", []),
            extra_commands=data.get("extra_commands", []),
            auth_provider_ids=data.get("auth_provider_ids", []),
            webview_view_ids=data.get("webview_view_ids", []),
            uri_trigger=data.get("uri_trigger"),
            run_task_trigger=data.get("run_task_trigger", False),
            run_walkthrough_trigger=data.get("run_walkthrough_trigger", False),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    finally:
        # Clean up the trigger file after reading
        with contextlib.suppress(OSError):
            p.unlink()

    return payload
