"""Authoritative backend-owned analysis contracts."""

from __future__ import annotations

import warnings
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

# W10-1: Proactive schema evolution discipline for ActivationReport.
# Bumped on breaking changes; minor bumps emit DeprecationWarning, major
# bumps are rejected under model_validate(..., context={"strict_schema": True}).
# W10-4: 1.0 -> 2.0 — automation_health and coverage_summary slots became
# typed models (AutomationHealth, CoverageSummary) instead of dict[str, Any].
# W11-3: 2.0 -> 2.1 — activation_discovery_strategies (W12-2 renamed to
# activation_discovery_strategy_outcomes and reshaped from list[str] to
# dict[str, str] for per-strategy outcome detail), runner_exit_code, and
# runner_status added; runner_status keys off RunnerStatusLiteral.
ACTIVATION_REPORT_SCHEMA_VERSION = "2.1"


# W11-3: Top-level outcome classification for the entrypoint runner. The
# producer (`executor/flows/playwright/entrypoint_runner.py`) raises
# `SystemExit(0)` on a clean run and `SystemExit(1)` on any control-path
# failure today; "unknown" survives the case where the report is persisted
# without the runner ever calling `set_runner_status` (e.g. cancelled jobs
# whose monitor stopped before runner cleanup, or report-only ingest).
RunnerStatusLiteral = Literal["success", "error", "unknown"]


class StrictContractModel(BaseModel):
    """Common base for backend-owned contract models."""

    model_config = ConfigDict(extra="forbid")


# Imports placed below StrictContractModel so the typed-projection modules
# (which import StrictContractModel from this file) can resolve without
# bringing in a half-initialized contracts module.
from packages.analysis_contracts.automation import (  # noqa: E402
    AutomationHealth,
    AutomationHealthStatusLiteral,  # noqa: F401  (re-exported via __init__)
)
from packages.analysis_contracts.coverage import CoverageSummary  # noqa: E402


class ActivationEntry(StrictContractModel):
    extension_id: str
    activation_event: str = ""
    duration_ms: int | None = None
    timestamp: str = ""
    success: bool = True
    source: str = ""
    # PR345 PR3: lifecycle marker type from exthost.log parsers.
    # "" = activation (legacy default); "activate_fn_entry",
    # "activate_fn_exit", "command_register", "provider_register".
    marker_type: str = ""


class RunningExtension(StrictContractModel):
    extension_id: str
    name: str = ""
    activation_time_ms: int | None = None
    status: str = "active"


class NetworkEvent(StrictContractModel):
    timestamp: str = ""
    rel_time_s: float | None = None
    protocol: str = ""
    event_type: str = ""
    source_ip: str = ""
    destination_ip: str = ""
    destination_port: int | None = None
    host: str = ""
    path: str = ""
    http_method: str = ""
    http_status_code: int | None = None
    http_content_type: str = ""
    request_body_sha256: str = ""
    request_body_preview: str = ""
    request_body_truncated: bool = False
    response_body_sha256: str = ""
    response_body_preview: str = ""
    response_body_truncated: bool = False
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    noise_reason: str = ""
    summary: str = ""


class FileEvent(StrictContractModel):
    timestamp: str = ""
    rel_time_s: float | None = None
    operation: str = ""
    path: str = ""
    secondary_path: str = ""
    source: str = ""
    observer: str = ""
    scenario_name: str = ""
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    noise_reason: str = ""
    artifact_class: str = ""
    flags: str = ""
    sensitive: bool = False
    summary: str = ""


class ScenarioTrace(StrictContractModel):
    name: str
    started_at: float
    ended_at: float = 0.0
    status: str = "running"
    failure_reason_code: str = ""
    error_detail: str = ""


class SkippedScenarioRecord(StrictContractModel):
    name: str
    reason_code: str
    detail: str = ""


class StimulusPassTrace(StrictContractModel):
    pass_id: str
    label: str
    order: int
    started_at: float
    ended_at: float = 0.0
    status: str = "running"
    trigger_method: str = ""


class PrerequisiteResult(StrictContractModel):
    prerequisite_id: str
    key: str
    label: str
    status: str = "planned"
    materializer: str = ""
    pass_name: str = ""
    attempt_ids: list[str] = Field(default_factory=list)
    detail: str = ""
    reason_code: str = ""
    resolved_targets: dict[str, Any] = Field(default_factory=dict)


# Allowed values for ``EventAttemptRecord.status``. Transition graph:
#
#   planned
#      └─ running
#           ├─ attempted_only      (harness stimulus ran, nothing verified)
#           │     └─ activation_seen   (exthost log shows target activated)
#           │           └─ target_log_seen  (target-owned log/output evidence)
#           │                 └─ verified   (+ runtime capability evidence)
#           ├─ blocked             (prerequisite unmet; skipped by policy)
#           └─ failed              (attempt errored out)
#
# ``activation_seen`` and ``target_log_seen`` are weaker-than-``verified``
# intermediate observation states so the report can distinguish "the target
# extension genuinely reacted to the stimulus" from "the harness ran but we
# have no target-owned evidence" (today both collapse into ``attempted_only``
# / ``verified`` with no finer gradation). See the
# ``Target activation lifecycle + target log instrumentation`` workstream
# in ``documents/POST_POC_BACKLOG.md``.
EVENT_ATTEMPT_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {
        "planned",
        "running",
        "attempted_only",
        "activation_seen",
        "target_log_seen",
        "verified",
        "blocked",
        "failed",
    }
)


class EventAttemptRecord(StrictContractModel):
    attempt_id: str
    declared_event: str
    activation_event: str
    event_family: str
    event_value: str = ""
    track: str = "official"
    selected_by: str = ""
    selection_reasons: list[str] = Field(default_factory=list)
    pass_name: str = ""
    backfill_pass_name: str = ""
    prerequisite_keys: list[str] = Field(default_factory=list)
    verification_contract: list[str] = Field(default_factory=list)
    trigger_method: str = ""
    fallback_trigger_method: str = ""
    executor_action: str = ""
    backfill_executor_action: str = ""
    legacy_scenarios: list[str] = Field(default_factory=list)
    capability_tags: list[str] = Field(default_factory=list)
    status: str = "planned"
    trigger_method_used: str = ""
    attempted_passes: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    verification_status: str = "not_attempted"
    failure_reason_code: str = ""
    blocked_reason_code: str = ""
    result_details: str = ""
    official: bool = True
    heuristic: bool = False
    ui_path: str = ""
    harness_fallback: str = ""

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        if value not in EVENT_ATTEMPT_LIFECYCLE_STATES:
            raise ValueError(
                f"EventAttemptRecord.status {value!r} is not one of "
                f"{sorted(EVENT_ATTEMPT_LIFECYCLE_STATES)}"
            )
        return value


class EvidenceEvent(StrictContractModel):
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
    raw_context: dict[str, Any] = Field(default_factory=dict)


class ProcessEvent(StrictContractModel):
    timestamp: str = ""
    rel_time_s: float | None = None
    pid: int
    ppid: int | None = None
    operation: str = ""
    command: str = ""
    arguments_preview: str = ""
    cwd: str = ""
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    summary: str = ""


class OutputSignalEvent(StrictContractModel):
    """A target-extension Output channel write captured by the harness hook.

    PR345 PR5 + ADR 0006: emitted by the harness extension's
    createOutputChannel proxy as an [extrace-harness] JSON-line marker;
    parsed into this dataclass and routed into the evidence chain by
    ``_build_evidence_bundle`` as ``EvidenceEvent.kind ==
    "output_channel_appendline"``.
    """

    timestamp: str = ""
    rel_time_s: float | None = None
    channel: str = ""
    text: str = ""
    extension_id: str = ""
    activation_event: str = ""
    is_target_extension_event: bool = False
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    summary: str = ""


class EvidenceLink(StrictContractModel):
    from_event_id: str
    to_event_id: str
    link_type: str
    confidence: float
    reason: str


class LogStreamEntry(StrictContractModel):
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


class RiskSignal(StrictContractModel):
    signal_id: str
    category: str
    severity: str
    confidence: float
    confidence_tier: str = ""
    evidence_event_ids: list[str] = Field(default_factory=list)
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class TriggerStimulusPass(StrictContractModel):
    pass_id: str
    label: str
    order: int
    description: str = ""
    attempt_ids: list[str] = Field(default_factory=list)
    prerequisite_keys: list[str] = Field(default_factory=list)
    status: str = "planned"
    trigger_method: str = ""


class TriggerScenarioDetail(StrictContractModel):
    name: str
    intent: str = ""
    activation_events: list[str] = Field(default_factory=list)
    contributes_signals: list[str] = Field(default_factory=list)
    api_capabilities: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    success_signals: list[str] = Field(default_factory=list)
    risk_of_noise: str = ""
    selection_reasons: list[str] = Field(default_factory=list)


class ActivationReportFileSummary(StrictContractModel):
    filename: str
    size_bytes: int
    modified: float


class ActivationReport(StrictContractModel):
    schema_version: str = ACTIVATION_REPORT_SCHEMA_VERSION
    report_version: int
    target_extension_expected: str
    # W10-FIXUP-2: outer field stays required (matches pre-W10 contract). Inner
    # AutomationHealth fields keep their defaults so skip_automation's 5-field
    # subset still validates; the rationale for inner defaults does not extend
    # to the outer slot.
    automation_health: AutomationHealth
    signal_summary: dict[str, Any]
    summary: dict[str, Any]
    scenario_traces: list[ScenarioTrace]
    skipped_scenarios: list[SkippedScenarioRecord] = Field(default_factory=list)
    evidence_events: list[EvidenceEvent]
    network_events: list[NetworkEvent]
    file_events: list[FileEvent]
    process_events: list[ProcessEvent] = Field(default_factory=list)
    log_streams: dict[str, list[LogStreamEntry]]
    target_extension_observed: bool = False
    trigger_plan_requested: bool = False
    trigger_plan_loaded: bool = False
    trigger_plan_applied: bool = False
    trigger_plan_path: str = ""
    trigger_execution_mode: str = ""
    requested_scenarios: list[str] = Field(default_factory=list)
    failed_scenarios: list[str] = Field(default_factory=list)
    extra_trigger_failures: list[str] = Field(default_factory=list)
    verification_gap: int = 0
    heuristic_verification_gap: int = 0
    run_quality: str = ""
    run_quality_reasons: list[str] = Field(default_factory=list)
    log_health: dict[str, Any] = Field(default_factory=dict)
    attribution_summary: dict[str, Any] = Field(default_factory=dict)
    risk_signals: list[RiskSignal] = Field(default_factory=list)
    risk_summary: dict[str, Any] = Field(default_factory=dict)
    attempted_capabilities: list[str] = Field(default_factory=list)
    verified_capabilities: list[str] = Field(default_factory=list)
    official_attempted_capabilities: list[str] = Field(default_factory=list)
    official_verified_capabilities: list[str] = Field(default_factory=list)
    heuristic_attempted_capabilities: list[str] = Field(default_factory=list)
    heuristic_verified_capabilities: list[str] = Field(default_factory=list)
    network_capture_error: str = ""
    file_capture_error: str = ""
    file_capture_diagnostics: dict[str, Any] = Field(default_factory=dict)
    activated: list[ActivationEntry] = Field(default_factory=list)
    running_extensions: list[RunningExtension] = Field(default_factory=list)
    stimulus_passes: list[StimulusPassTrace] = Field(default_factory=list)
    prerequisite_results: list[PrerequisiteResult] = Field(default_factory=list)
    event_attempts: list[EventAttemptRecord] = Field(default_factory=list)
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    network_summary: dict[str, Any] = Field(default_factory=dict)
    file_summary: dict[str, Any] = Field(default_factory=dict)
    coverage_summary: CoverageSummary = Field(default_factory=CoverageSummary)
    coverage_matrix: list[dict[str, Any]] = Field(default_factory=list)
    coverage_tracks: dict[str, dict[str, Any]] = Field(default_factory=dict)
    official_event_coverage: dict[str, Any] = Field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, Any] = Field(default_factory=dict)
    extension_host_output_lines: int = 0
    extension_host_output: str = ""
    log_file: str = ""
    output_signal_events: list[OutputSignalEvent] = Field(default_factory=list)
    # W11-3 producer; W12-2 [FOLLOWUP activation-discovery-strategy-outcome-detail]
    # upgrades from list[str] (only succeeded-and-produced-new) to
    # dict[str, str] mapping strategy id -> outcome literal so analysts can
    # distinguish ran-and-was-redundant, ran-and-failed, and never-reached.
    # Strategy ids: "exthost_log_parse" (strategy 1), "running_extensions_ui"
    # (strategy 2), "exthost_output_parse" (strategy 3). Outcome literals:
    # "succeeded_with_new_activations", "succeeded_no_new_activations",
    # "failed:<ExcClassName>".
    activation_discovery_strategy_outcomes: dict[str, str] = Field(default_factory=dict)
    # W11-3: runner exit code (0 / non-zero). `None` if the runner never
    # finalized — the report was persisted before the runner reached its
    # `set_runner_status` call.
    runner_exit_code: int | None = None
    # W11-3: derived from runner_exit_code; `success` for 0, `error` for
    # any non-zero, `unknown` if the runner never finalized.
    runner_status: RunnerStatusLiteral = "unknown"

    @model_validator(mode="before")
    @classmethod
    def _validate_schema_version(cls, data: object, info: ValidationInfo) -> object:
        # W10-1: proactive schema evolution. Missing or stale schema_version
        # emits DeprecationWarning; model_validate(..., context={"strict_schema": True})
        # rejects instead of warning. See ACTIVATION_REPORT_SCHEMA_VERSION.
        if not isinstance(data, dict):
            return data
        context = info.context or {}
        strict = bool(context.get("strict_schema", False))
        version = data.get("schema_version")
        if version is None:
            if strict:
                raise ValueError(
                    "ActivationReport ingest rejected: schema_version missing "
                    "under strict_schema=True"
                )
            warnings.warn(
                f"ActivationReport ingested without schema_version; defaulting to "
                f"current {ACTIVATION_REPORT_SCHEMA_VERSION!r}",
                DeprecationWarning,
                stacklevel=2,
            )
            data = dict(data)
            data["schema_version"] = ACTIVATION_REPORT_SCHEMA_VERSION
        elif version != ACTIVATION_REPORT_SCHEMA_VERSION:
            if strict:
                raise ValueError(
                    f"ActivationReport ingest rejected: schema_version={version!r} "
                    f"does not match current {ACTIVATION_REPORT_SCHEMA_VERSION!r}"
                )
            warnings.warn(
                f"ActivationReport ingested with stale schema_version={version!r}; "
                f"current is {ACTIVATION_REPORT_SCHEMA_VERSION!r}",
                DeprecationWarning,
                stacklevel=2,
            )
        return data

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_verdict(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if "signal_summary" in data or "verdict" not in data:
            return data
        migrated = dict(data)
        migrated["signal_summary"] = migrated.pop("verdict")
        return migrated


class TriggerPayload(StrictContractModel):
    analysis_profile: str = "layered_deep"
    selected_scenarios: list[str] = Field(default_factory=list)
    official_selected_scenarios: list[str] = Field(default_factory=list)
    heuristic_selected_scenarios: list[str] = Field(default_factory=list)
    selected_scenario_details: list[TriggerScenarioDetail] = Field(default_factory=list)
    selection_reasons: dict[str, list[str]] = Field(default_factory=dict)
    coverage_tracks: dict[str, dict[str, Any]] = Field(default_factory=dict)
    coverage_summary: CoverageSummary = Field(default_factory=CoverageSummary)
    coverage_matrix: list[dict[str, Any]] = Field(default_factory=list)
    official_attempted_capabilities: list[str] = Field(default_factory=list)
    heuristic_attempted_capabilities: list[str] = Field(default_factory=list)
    target_extension_id: str | None = None
    command_targets: dict[str, str] = Field(default_factory=dict)
    view_targets: dict[str, dict[str, str]] = Field(default_factory=dict)
    extra_notebook_files: list[str] = Field(default_factory=list)
    extra_custom_editor_files: list[str] = Field(default_factory=list)
    extra_commands: list[str] = Field(default_factory=list)
    auth_provider_ids: list[str] = Field(default_factory=list)
    webview_view_ids: list[str] = Field(default_factory=list)
    uri_trigger: str | None = None
    run_task_trigger: bool = False
    run_walkthrough_trigger: bool = False
    stimulus_passes: list[TriggerStimulusPass] = Field(default_factory=list)
    event_attempts: list[EventAttemptRecord] = Field(default_factory=list)
    prerequisite_results: list[PrerequisiteResult] = Field(default_factory=list)
    official_event_coverage: dict[str, Any] = Field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, Any] = Field(default_factory=dict)
