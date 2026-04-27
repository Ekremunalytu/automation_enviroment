"""Data types and shared paths for layered stimulus execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_HARNESS_CONTEXT_DIR = Path("/workspace/.extrace-harness")
_HARNESS_CONTEXT_PATH = _HARNESS_CONTEXT_DIR / "context.json"
_HARNESS_READY_PATH = _HARNESS_CONTEXT_DIR / "ready.json"
_TASKS_PATH = Path("/workspace/.vscode/tasks.json")
_LAUNCH_PATH = Path("/workspace/.vscode/launch.json")


HARNESS_COMMAND_UNAVAILABLE_REASON = "harness_command_unavailable"

# W8-0: typed sub-reasons that split the legacy "harness_command_unavailable"
# bucket into actionable failure modes. The Python parser raises
# HarnessUnavailableError with the matching code so reports surface
# *why* the harness was unreachable instead of a single generic label.
HARNESS_READY_MARKER_MISSING_REASON = "harness_ready_marker_missing"
HARNESS_READY_MARKER_STALE_REASON = "harness_ready_marker_stale"
HARNESS_READY_MARKER_INVALID_REASON = "harness_ready_marker_invalid"
HARNESS_ACTIVATION_TIMEOUT_REASON = "harness_activation_timeout"


class HarnessUnavailableError(RuntimeError):
    """Raised when the harness extension's command never registers in time."""

    reason_code = HARNESS_COMMAND_UNAVAILABLE_REASON

    def __init__(
        self,
        message: str = (
            "Harness extension did not register "
            "extrace.harness.runCurrentStimulus in time."
        ),
        *,
        reason_code: str = "",
    ) -> None:
        super().__init__(message)
        if reason_code:
            self.reason_code = reason_code


@dataclass
class SkippedScenarioRecord:
    name: str
    reason_code: str
    detail: str = ""


@dataclass
class AutomationExecutionResult:
    """Normalized executor result shared across all automation modes."""

    requested_scenarios: list[str] = field(default_factory=list)
    executed_scenarios: list[str] = field(default_factory=list)
    failed_scenarios: list[str] = field(default_factory=list)
    skipped_scenarios: list[SkippedScenarioRecord] = field(default_factory=list)
    extra_trigger_failures: list[str] = field(default_factory=list)


StimulusExecutionResult = AutomationExecutionResult


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
