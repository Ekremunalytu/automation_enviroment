"""Public dataclasses shared by monitor helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunningExtension:
    """An extension entry scraped from Running Extensions UI."""

    extension_id: str
    name: str = ""
    activation_time_ms: int | None = None
    status: str = "active"


@dataclass
class ScenarioTrace:
    """Lifecycle timing for an executed automation scenario."""

    name: str
    started_at: float
    ended_at: float = 0.0
    status: str = "running"
    failure_reason_code: str = ""
    error_detail: str = ""


@dataclass
class SkippedScenarioRecord:
    """Authoritative record for a requested scenario that never executed."""

    name: str
    reason_code: str
    detail: str = ""


@dataclass
class StimulusPassTrace:
    """Lifecycle timing for a layered stimulus pass."""

    pass_id: str
    label: str
    order: int
    started_at: float
    ended_at: float = 0.0
    status: str = "running"
    trigger_method: str = ""


@dataclass
class PrerequisiteResult:
    """Materialization state for a prerequisite used by one or more attempts."""

    prerequisite_id: str
    key: str
    label: str
    status: str = "planned"
    materializer: str = ""
    pass_name: str = ""
    attempt_ids: list[str] = field(default_factory=list)
    detail: str = ""
    reason_code: str = ""
    resolved_targets: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventAttemptRecord:
    """Per-event execution ledger entry."""

    attempt_id: str
    declared_event: str
    activation_event: str
    event_family: str
    event_value: str = ""
    track: str = "official"
    selected_by: str = ""
    selection_reasons: list[str] = field(default_factory=list)
    pass_name: str = ""
    backfill_pass_name: str = ""
    prerequisite_keys: list[str] = field(default_factory=list)
    verification_contract: list[str] = field(default_factory=list)
    trigger_method: str = ""
    fallback_trigger_method: str = ""
    executor_action: str = ""
    backfill_executor_action: str = ""
    legacy_scenarios: list[str] = field(default_factory=list)
    capability_tags: list[str] = field(default_factory=list)
    status: str = "planned"
    trigger_method_used: str = ""
    attempted_passes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    verification_status: str = "not_attempted"
    failure_reason_code: str = ""
    blocked_reason_code: str = ""
    result_details: str = ""
    official: bool = True
    heuristic: bool = False
    ui_path: str = ""
    harness_fallback: str = ""


@dataclass
class EvidenceEvent:
    """Canonical evidence event shared across telemetry sources."""

    event_id: str
    kind: str
    timestamp: str = ""
    rel_time_s: float | None = None
    collector: str = ""
    actor: str = "unknown"
    scenario_name: str = ""
    extension_id: str = ""
    activation_event: str = ""
    operation: str = ""
    protocol: str = ""
    host: str = ""
    path: str = ""
    destination_ip: str = ""
    destination_port: int | None = None
    attribution_status: str = ""
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    noise_reason: str = ""
    artifact_class: str = ""
    sensitive: bool = False
    summary: str = ""
    raw_context: dict[str, str | int | float | bool | None] = field(
        default_factory=dict
    )


@dataclass
class EvidenceLink:
    """Explicit relationship between two evidence events."""

    from_event_id: str
    to_event_id: str
    link_type: str
    confidence: float
    reason: str


@dataclass
class LogStreamEntry:
    """A timeline row for live automation/exthost streams."""

    timestamp: str = ""
    rel_time_s: float | None = None
    stream: str = ""
    kind: str = ""
    message: str = ""
    extension_id: str = ""
    activation_event: str = ""
    scenario_name: str = ""
    status: str = ""
    is_target_extension: bool = False


@dataclass
class RiskSignal:
    """Risk signal emitted by post-processing helpers."""

    signal_id: str
    category: str
    severity: str = "info"
    confidence: float = 0.0
    confidence_tier: str = ""
    evidence_event_ids: list[str] = field(default_factory=list)
    summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def _assert_target_stream_invariant(
    entry: LogStreamEntry, target_extension_id: str
) -> None:
    """Reject log entries that violate the target_extension_host invariant.

    PR345 PR4: every entry assigned to the ``target_extension_host`` stream
    must have ``is_target_extension=True`` and ``extension_id`` matching
    ``target_extension_id``. Build-path callers enforce this so detection
    rules reading the target stream cannot see a leaked sibling-extension
    entry. Caller must invoke immediately after appending a LogStreamEntry.

    Lives in ``monitor_records`` (next to ``LogStreamEntry``) so that
    both ``monitor_lifecycle`` and ``monitor_scenario_accountant`` can
    import it without a circular dependency. ``monitor_lifecycle``
    re-exports the symbol so the existing
    ``from executor.flows.playwright.monitor.lifecycle import
    _assert_target_stream_invariant`` test pin in
    ``tests/executor/test_playwright_monitor_lifecycle.py`` keeps
    working.
    """
    if entry.stream != "target_extension_host":
        return
    if not entry.is_target_extension:
        raise ValueError(
            "target_extension_host log entry must have is_target_extension=True; "
            f"got entry for {entry.extension_id!r} with is_target_extension=False"
        )
    if not target_extension_id or entry.extension_id != target_extension_id:
        raise ValueError(
            "target_extension_host log entry must have extension_id matching "
            f"target ({target_extension_id!r}); got {entry.extension_id!r}"
        )
