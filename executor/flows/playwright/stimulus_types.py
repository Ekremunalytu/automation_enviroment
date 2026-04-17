"""Data types and shared paths for layered stimulus execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_HARNESS_CONTEXT_DIR = Path("/workspace/.extrace-harness")
_HARNESS_CONTEXT_PATH = _HARNESS_CONTEXT_DIR / "context.json"
_TASKS_PATH = Path("/workspace/.vscode/tasks.json")
_LAUNCH_PATH = Path("/workspace/.vscode/launch.json")


@dataclass
class StimulusExecutionResult:
    """Execution result for a layered stimulus plan."""

    executed_scenarios: list[str] = field(default_factory=list)
    failed_scenarios: list[str] = field(default_factory=list)
    extra_trigger_failures: list[str] = field(default_factory=list)


@dataclass
class PrerequisiteMaterialization:
    status: str
    detail: str = ""
    reason_code: str = ""
    resolved_targets: dict[str, Any] = field(default_factory=dict)


@dataclass
class AttemptExecutionRecord:
    status: str
    result_details: str = ""
    failure_reason_code: str = ""
