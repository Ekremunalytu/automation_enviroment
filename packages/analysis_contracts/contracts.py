"""Authoritative backend-owned analysis contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictContractModel(BaseModel):
    """Common base for backend-owned contract models."""

    model_config = ConfigDict(extra="forbid")


class ActivationEntry(StrictContractModel):
    extension_id: str
    activation_event: str = ""
    duration_ms: int | None = None
    timestamp: str = ""
    success: bool = True
    source: str = ""


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
    report_version: int
    target_extension_expected: str
    automation_health: dict[str, Any]
    verdict: dict[str, Any]
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
    coverage_summary: dict[str, Any] = Field(default_factory=dict)
    coverage_matrix: list[dict[str, Any]] = Field(default_factory=list)
    coverage_tracks: dict[str, dict[str, Any]] = Field(default_factory=dict)
    official_event_coverage: dict[str, Any] = Field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, Any] = Field(default_factory=dict)
    extension_host_output_lines: int = 0
    extension_host_output: str = ""
    log_file: str = ""


class TriggerPayload(StrictContractModel):
    analysis_profile: str = "layered_deep"
    selected_scenarios: list[str] = Field(default_factory=list)
    official_selected_scenarios: list[str] = Field(default_factory=list)
    heuristic_selected_scenarios: list[str] = Field(default_factory=list)
    selected_scenario_details: list[TriggerScenarioDetail] = Field(default_factory=list)
    selection_reasons: dict[str, list[str]] = Field(default_factory=dict)
    coverage_tracks: dict[str, dict[str, Any]] = Field(default_factory=dict)
    coverage_summary: dict[str, Any] = Field(default_factory=dict)
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
