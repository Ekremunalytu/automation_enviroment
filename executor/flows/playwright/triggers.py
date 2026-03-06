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
    extra_notebook_files: list[str] = field(default_factory=list)
    extra_custom_editor_files: list[str] = field(default_factory=list)
    extra_commands: list[str] = field(default_factory=list)
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
            extra_notebook_files=data.get("extra_notebook_files", []),
            extra_custom_editor_files=data.get("extra_custom_editor_files", []),
            extra_commands=data.get("extra_commands", []),
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
