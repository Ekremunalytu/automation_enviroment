"""Public activation report surface for the monitor facade."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..annotation import build_attribution_summary
from ..attribution import (
    build_evidence_bundle,
    build_risk_signals,
    build_risk_summary,
)
from ..capture import summarize_extension_host_logs
from ..health import (
    build_automation_health,
    build_log_health,
    build_run_quality,
    count_target_activations,
    is_background_activation,
)
from ..report_builder import build_report_data, build_summary, save_report_payload
from ..runtime_capture._shared import _log
from ..runtime_capture.events import (
    ActivationEntry,
    FileEvent,
    NetworkEvent,
    OutputSignalEvent,
    ProcessEvent,
)
from .records import (
    EventAttemptRecord,
    EvidenceEvent,
    EvidenceLink,
    LogStreamEntry,
    PrerequisiteResult,
    RiskSignal,
    RunningExtension,
    ScenarioTrace,
    SkippedScenarioRecord,
    StimulusPassTrace,
)
from .runtime import (
    _derive_runtime_attempted_capabilities,
    _derive_runtime_verified_capabilities,
    _filter_supported_capabilities,
    _matrix_entries_for_track,
)
from .support import resolve_monitor_api

_DEMOTE_WARNING_EMITTED: set[tuple[str, str]] = set()


def _log_stream_demote_warning(entry: LogStreamEntry, target_id: str) -> None:
    """Emit a one-shot warning per (extension_id, target_id) demote.

    PR345 PR4 serialization-time defense: when an entry assigned to
    ``target_extension_host`` violates the invariant the build-path
    guard enforces, we demote it to ``other_extension_host`` and log
    once so the leak is observable without spamming the report build.
    """
    key = (entry.extension_id or "", target_id or "")
    if key in _DEMOTE_WARNING_EMITTED:
        return
    _DEMOTE_WARNING_EMITTED.add(key)
    _log(
        "Demoted target_extension_host log entry to other_extension_host: "
        f"extension_id={entry.extension_id!r} "
        f"is_target_extension={entry.is_target_extension} "
        f"target={target_id!r}"
    )


@dataclass
class ActivationReport:
    """Aggregated monitoring results."""

    report_version: int = 2
    activated: list[ActivationEntry] = field(default_factory=list)
    running_extensions: list[RunningExtension] = field(default_factory=list)
    network_events: list[NetworkEvent] = field(default_factory=list)
    file_events: list[FileEvent] = field(default_factory=list)
    process_events: list[ProcessEvent] = field(default_factory=list)
    output_signal_events: list[OutputSignalEvent] = field(default_factory=list)
    scenario_traces: list[ScenarioTrace] = field(default_factory=list)
    skipped_scenarios: list[SkippedScenarioRecord] = field(default_factory=list)
    stimulus_passes: list[StimulusPassTrace] = field(default_factory=list)
    prerequisite_results: list[PrerequisiteResult] = field(default_factory=list)
    event_attempts: list[EventAttemptRecord] = field(default_factory=list)
    evidence_links: list[EvidenceLink] = field(default_factory=list)
    log_entries: list[LogStreamEntry] = field(default_factory=list)
    coverage_tracks: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage_summary: dict[str, Any] = field(default_factory=dict)
    coverage_matrix: list[dict[str, Any]] = field(default_factory=list)
    official_event_coverage: dict[str, Any] = field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, Any] = field(default_factory=dict)
    attempted_capabilities: list[str] = field(default_factory=list)
    verified_capabilities: list[str] = field(default_factory=list)
    heuristic_attempted_capabilities: list[str] = field(default_factory=list)
    heuristic_verified_capabilities: list[str] = field(default_factory=list)
    signal_summary: dict[str, Any] = field(default_factory=dict)
    trigger_plan_requested: bool = False
    trigger_plan_loaded: bool = False
    trigger_plan_applied: bool = False
    trigger_plan_path: str = ""
    trigger_execution_mode: str = ""
    requested_scenarios: list[str] = field(default_factory=list)
    failed_scenarios: list[str] = field(default_factory=list)
    extra_trigger_failures: list[str] = field(default_factory=list)
    network_capture_error: str = ""
    file_capture_error: str = ""
    file_capture_diagnostics: dict[str, Any] = field(default_factory=dict)
    extension_host_output: str = ""
    # W13-1 (Codex H6): per-launch HMAC secret loaded by the entrypoint
    # from /results/_extrace_harness_python_secret (written by
    # launch_vscode.sh). When non-empty, reconciliation requires every
    # ``[extrace-harness] {phase:"complete"}`` marker to carry a valid
    # HMAC-SHA256 nonce; missing or invalid signatures route the attempt
    # through ``_mark_unverified_harness_attempt`` (fail-closed). Empty
    # value preserves the pre-W13-1 contract for unit tests that
    # construct reports without the orchestration handshake.
    expected_harness_nonce: str = field(default="", repr=False)
    # W13-12 (Codex F2 close-pass for W13-1 H6): production paths set this
    # True at ``setup_monitor`` time so an empty ``expected_harness_nonce``
    # (eager-consume miss, FileNotFoundError, OSError, bind-mount race)
    # routes through fail-closed in
    # ``_attempt_has_harness_completion_trace`` instead of the legacy
    # phase-only branch. Test fixtures that construct ActivationReport
    # directly (without setup_monitor) keep the default ``False`` so the
    # pre-W13-1 regression surface stays GREEN.
    harness_handshake_required: bool = field(default=False, repr=False)
    log_file_path: str = ""
    log_offsets_snapshot: dict[str, int] = field(default_factory=dict, repr=False)
    target_extension_id: str = ""
    monitoring_start: float = 0.0
    monitoring_end: float = 0.0
    monitoring_started_monotonic: float = field(default=0.0, repr=False)
    monitoring_ended_monotonic: float = field(default=0.0, repr=False)
    scenarios_run: list[str] = field(default_factory=list)
    # W11-3 producer; W12-2 [FOLLOWUP activation-discovery-strategy-outcome-detail]
    # upgrades from list[str] (succeeded-and-produced-net-new) to
    # dict[str, str] (per-strategy outcome). Outcomes use the literals
    # ``"succeeded_with_new_activations"``, ``"succeeded_no_new_activations"``,
    # and ``"failed:<ExcClassName>"``. ReportAssembler writes via
    # set_discovery_strategy_outcomes after stop's final strategy completes.
    activation_discovery_strategy_outcomes: dict[str, str] = field(default_factory=dict)
    # W11-3: runner exit code captured by entrypoint_runner just before
    # SystemExit. None when the runner never reaches set_runner_status.
    runner_exit_code: int | None = None
    # W11-3: derived from runner_exit_code (`0`/`!=0`/`None` ->
    # `success`/`error`/`unknown`); the assembler is the single owner of
    # the mapping so the contract literal stays the source of truth.
    runner_status: str = "unknown"

    @property
    def duration_s(self) -> float:
        if (
            self.monitoring_started_monotonic > 0
            and self.monitoring_ended_monotonic > 0
        ):
            return self.monitoring_ended_monotonic - self.monitoring_started_monotonic
        return self.monitoring_end - self.monitoring_start

    @property
    def activated_ids(self) -> set[str]:
        return {entry.extension_id for entry in self.activated}

    @property
    def runtime_ids(self) -> set[str]:
        return {ext.extension_id for ext in self.running_extensions}

    @property
    def network_hosts(self) -> set[str]:
        hosts: set[str] = set()
        for entry in self.network_events:
            host = entry.host or entry.destination_ip
            if host:
                hosts.add(host)
        return hosts

    @property
    def sensitive_file_events(self) -> list[FileEvent]:
        return [entry for entry in self.file_events if entry.sensitive]

    @property
    def target_file_events(self) -> list[FileEvent]:
        return [entry for entry in self.file_events if entry.is_target_extension_event]

    @property
    def target_network_events(self) -> list[NetworkEvent]:
        return [
            entry for entry in self.network_events if entry.is_target_extension_event
        ]

    @property
    def ui_blocker_entries(self) -> list[LogStreamEntry]:
        return [entry for entry in self.log_entries if entry.stream == "ui_blockers"]

    @property
    def target_output_signal_events(self) -> list[OutputSignalEvent]:
        """Output channel events attributed to the target extension.

        PR345 PR5 + ADR 0006: events emitted by the harness Output
        channel hook whose attribution resolved to the target extension
        (timestamp within ATTRIBUTION_WINDOW_S of a target activation).
        """
        return [
            entry
            for entry in self.output_signal_events
            if entry.is_target_extension_event
        ]

    @property
    def target_extension_observed(self) -> bool:
        if not self.target_extension_id:
            return False
        return bool(
            any(
                entry.extension_id == self.target_extension_id
                for entry in self.activated
            )
            or any(
                entry.extension_id == self.target_extension_id
                for entry in self.running_extensions
            )
            or self.target_file_events
            or self.target_network_events
            or self.target_output_signal_events
        )

    @property
    def verification_gap(self) -> int:
        attempted = len(set(self.runtime_official_attempted_capabilities))
        verified = len(set(self.official_verified_capabilities))
        return max(attempted - verified, 0)

    @property
    def official_attempted_capabilities(self) -> list[str]:
        return _filter_supported_capabilities(
            self.attempted_capabilities,
            _matrix_entries_for_track(self, "official"),
        )

    @property
    def official_verified_capabilities(self) -> list[str]:
        return _derive_runtime_verified_capabilities(self, track="official")

    @property
    def runtime_official_attempted_capabilities(self) -> list[str]:
        return _derive_runtime_attempted_capabilities(self, track="official")

    @property
    def heuristic_verification_gap(self) -> int:
        attempted = len(set(self.runtime_heuristic_attempted_capabilities))
        verified = len(set(self.supported_heuristic_verified_capabilities))
        return max(attempted - verified, 0)

    @property
    def run_quality_reasons(self) -> list[str]:
        _, reasons = build_run_quality(self, self.automation_health)
        return reasons

    @property
    def supported_heuristic_attempted_capabilities(self) -> list[str]:
        return _filter_supported_capabilities(
            self.heuristic_attempted_capabilities,
            _matrix_entries_for_track(self, "heuristic"),
        )

    @property
    def runtime_heuristic_attempted_capabilities(self) -> list[str]:
        return _derive_runtime_attempted_capabilities(self, track="heuristic")

    @property
    def supported_heuristic_verified_capabilities(self) -> list[str]:
        return _derive_runtime_verified_capabilities(self, track="heuristic")

    @property
    def attribution_summary(self) -> dict[str, Any]:
        return build_attribution_summary(
            self,
            count_target_activations=count_target_activations,
            is_background_activation=is_background_activation,
        )

    @property
    def _log_capture_health(self) -> dict[str, Any]:
        log_paths = resolve_monitor_api().find_exthost_logs()
        return summarize_extension_host_logs(self.log_offsets_snapshot, log_paths)

    @property
    def log_health(self) -> dict[str, Any]:
        capture_health = self._log_capture_health
        return build_log_health(
            self,
            extension_host_log_found=bool(
                capture_health.get("extension_host_log_found", False)
            ),
            extension_host_log_present=bool(
                capture_health.get("extension_host_log_present", False)
            ),
        )

    @property
    def automation_health(self) -> dict[str, Any]:
        capture_health = self._log_capture_health
        return build_automation_health(
            self,
            extension_host_log_found=bool(
                capture_health.get("extension_host_log_found", False)
            ),
            extension_host_log_present=bool(
                capture_health.get("extension_host_log_present", False)
            ),
        )

    @property
    def run_quality(self) -> str:
        quality, _ = build_run_quality(self, self.automation_health)
        return quality

    @property
    def risk_signals(self) -> list[RiskSignal]:
        return build_risk_signals(self)

    @property
    def risk_summary(self) -> dict[str, Any]:
        return build_risk_summary(self.risk_signals)

    @property
    def summary(self) -> dict[str, Any]:
        return build_summary(
            self,
            run_quality=self.run_quality,
            automation_health=self.automation_health,
            log_health=self.log_health,
            attribution_summary=self.attribution_summary,
            risk_summary=self.risk_summary,
        )

    @property
    def network_summary(self) -> dict[str, Any]:
        protocols = sorted(
            {event.protocol for event in self.network_events if event.protocol}
        )
        event_types = sorted(
            {event.event_type for event in self.network_events if event.event_type}
        )
        return {
            "total_events": len(self.network_events),
            "unique_hosts": len(self.network_hosts),
            "protocols": protocols,
            "event_types": event_types,
            "capture_error": self.network_capture_error,
        }

    @property
    def file_summary(self) -> dict[str, Any]:
        sources: dict[str, int] = {}
        operations: dict[str, int] = {}
        attribution_statuses: dict[str, int] = {}
        for event in self.file_events:
            sources[event.source] = sources.get(event.source, 0) + 1
            operations[event.operation] = operations.get(event.operation, 0) + 1
            attribution_statuses[event.attribution_status] = (
                attribution_statuses.get(event.attribution_status, 0) + 1
            )

        return {
            "total_events": len(self.file_events),
            "sensitive_events": len(self.sensitive_file_events),
            "sources": sources,
            "operations": operations,
            "attribution_statuses": attribution_statuses,
            "capture_error": self.file_capture_error,
        }

    @property
    def evidence_events(self) -> list[EvidenceEvent]:
        events, _ = build_evidence_bundle(self)
        return events

    @property
    def canonical_evidence_links(self) -> list[EvidenceLink]:
        _, links = build_evidence_bundle(self)
        return links

    @property
    def log_streams(self) -> dict[str, list[LogStreamEntry]]:
        grouped: dict[str, list[LogStreamEntry]] = {
            "target_extension_host": [],
            "other_extension_host": [],
            "automation": [],
            "ui_blockers": [],
        }
        target_id = self.target_extension_id
        for entry in sorted(
            self.log_entries,
            key=lambda item: (
                item.rel_time_s is None,
                item.rel_time_s if item.rel_time_s is not None else 0.0,
                item.timestamp,
                item.message,
            ),
        ):
            stream = entry.stream
            # PR345 PR4: serialization-time invariant defense.
            # Build-path guard in monitor_lifecycle._assert_target_stream_invariant
            # is the primary contract; this demote handles entries that
            # somehow slipped past it (legacy fixtures, manual report
            # construction in tests). Half-correct over crashing report
            # delivery in production.
            if stream == "target_extension_host" and (
                not entry.is_target_extension
                or not target_id
                or entry.extension_id != target_id
            ):
                _log_stream_demote_warning(entry, target_id)
                stream = "other_extension_host"
            grouped.setdefault(stream, []).append(entry)
        return grouped

    def save(self, path: str | Path, announce: bool = True) -> Path:
        """Save full report as JSON."""
        evidence_events, evidence_links = build_evidence_bundle(self)
        data = build_report_data(
            self,
            evidence_events=evidence_events,
            evidence_links=evidence_links,
            risk_signals=self.risk_signals,
            risk_summary=self.risk_summary,
            run_quality=self.run_quality,
            automation_health=self.automation_health,
            log_health=self.log_health,
            attribution_summary=self.attribution_summary,
            summary=self.summary,
        )
        return save_report_payload(path, data, announce=announce, logger=_log)

    def print_summary(self) -> None:
        """Print a human-readable summary to stdout."""
        print("\n" + "=" * 60)
        print(" Extension Activation Report")
        print("=" * 60)
        print(f"  Monitoring duration : {self.duration_s:.1f}s")
        print(f"  Activations found   : {len(self.activated)}")
        print(f"  Unique extensions   : {len(self.activated_ids)}")
        print(f"  Running extensions  : {len(self.running_extensions)}")
        print(f"  Network events      : {len(self.network_events)}")
        print(f"  Network hosts       : {len(self.network_hosts)}")
        print(f"  File events         : {len(self.file_events)}")
        print(f"  Sensitive file I/O  : {len(self.sensitive_file_events)}")
        print(f"  Target observed     : {self.target_extension_observed}")
        print(f"  Automation health   : {self.automation_health['status']}")
        print(f"  Run quality         : {self.run_quality}")
        print(f"  Verification gap    : {self.verification_gap}")
        if self.activated:
            print("\n  Activated extensions:")
            for entry in self.activated:
                event_label = (
                    f" [{entry.activation_event}]" if entry.activation_event else ""
                )
                timing = f" ({entry.duration_ms}ms)" if entry.duration_ms else ""
                src = f" via {entry.source}" if entry.source else ""
                print(f"    - {entry.extension_id}{event_label}{timing}{src}")
        if self.running_extensions:
            print("\n  Running extensions (from UI):")
            for ext in self.running_extensions:
                name = f" ({ext.name})" if ext.name else ""
                timing = (
                    f" {ext.activation_time_ms}ms" if ext.activation_time_ms else ""
                )
                print(f"    - {ext.extension_id}{name}{timing}")
        if self.network_events:
            print("\n  Network activity:")
            for network_event in self.network_events[:10]:
                host = f" {network_event.host}" if network_event.host else ""
                port = (
                    f":{network_event.destination_port}"
                    if network_event.destination_port is not None
                    else ""
                )
                rel = (
                    f" @{network_event.rel_time_s:.3f}s"
                    if network_event.rel_time_s is not None
                    else ""
                )
                print(
                    "    - "
                    f"{network_event.event_type or network_event.protocol}"
                    f"{host}{port}{rel}"
                )
        if self.file_events:
            print("\n  File activity:")
            for file_event in self.file_events[:10]:
                rel = (
                    f" @{file_event.rel_time_s:.3f}s"
                    if file_event.rel_time_s is not None
                    else ""
                )
                source = f" [{file_event.source}]" if file_event.source else ""
                print(f"    - {file_event.operation}{source} {file_event.path}{rel}")
        print("=" * 60 + "\n")


__all__ = [
    "ActivationReport",
    "EventAttemptRecord",
    "EvidenceEvent",
    "EvidenceLink",
    "LogStreamEntry",
    "PrerequisiteResult",
    "RiskSignal",
    "RunningExtension",
    "ScenarioTrace",
    "StimulusPassTrace",
]
