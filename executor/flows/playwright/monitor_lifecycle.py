"""Extension monitor lifecycle and orchestration helpers."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import time
from pathlib import Path
from types import TracebackType
from typing import Any

from playwright.sync_api import Page

from .attribution import (
    _format_epoch_timestamp,
    _relative_time,
    _scenario_name_for_timestamp,
)
from .monitor_payload import populate_report_from_trigger_payload
from .monitor_records import (
    LogStreamEntry,
    PrerequisiteResult,
    ScenarioTrace,
    SkippedScenarioRecord,
    StimulusPassTrace,
)
from .monitor_report_assembler import ReportAssembler
from .monitor_runtime import (
    _build_activation_log_message,
    _build_event_attempt_log_message,
    _build_prerequisite_log_message,
    _build_scenario_log_message,
    _build_stimulus_pass_log_message,
    _count_target_activations,
    _find_event_attempt,
)
from .monitor_runtime_state import MonitorRuntime
from .monitor_support import resolve_monitor_api
from .monitor_types import ActivationReport
from .runtime_capture._shared import _parse_iso_timestamp
from .runtime_capture.events import FileEvent, NetworkEvent, ProcessEvent


def _assert_target_stream_invariant(
    entry: LogStreamEntry, target_extension_id: str
) -> None:
    """Reject log entries that violate the target_extension_host invariant.

    PR345 PR4: every entry assigned to the ``target_extension_host`` stream
    must have ``is_target_extension=True`` and ``extension_id`` matching
    ``target_extension_id``. Build-path callers enforce this so detection
    rules reading the target stream cannot see a leaked sibling-extension
    entry. Caller must invoke immediately after appending a LogStreamEntry.
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


class ExtensionMonitor:
    """Context manager that captures extension activations around scenario execution."""

    def __init__(
        self,
        page: Page,
        report_path: str | Path | None = None,
        target_extension_id: str = "",
    ) -> None:
        self.page = page
        self.report_path = None if report_path is None else Path(report_path)
        self.report = ActivationReport(target_extension_id=target_extension_id)
        self._active_scenarios: dict[str, ScenarioTrace] = {}
        # W11-2: derived-state refresh + persist debounce moved into
        # ReportAssembler. The facade keeps thin _refresh_…/_persist_…
        # shims (below) so the W11-1 facade pin file's bound-method
        # identity assertions stay green.
        self._assembler = ReportAssembler(
            report=self.report,
            report_path=self.report_path,
        )
        # W11-1: runtime state machine (captures, log offsets, event handlers)
        # is owned by MonitorRuntime; runtime callbacks are wired through the
        # facade shims so the W11-1 pin file's identity assertions remain
        # untouched until W11-5 collapses the facade.
        self._runtime = MonitorRuntime(
            page=self.page,
            report=self.report,
            persist=self._persist_report,
            record_automation_event=self.record_automation_event,
            finalize_scenarios=self._finalize_running_scenarios,
            append_activation_log_entries=self._append_activation_log_entries,
            refresh_derived_state=self._refresh_derived_report_state,
            set_discovery_strategies=self._set_discovery_strategies,
        )

    @property
    def _log_offsets(self) -> dict[str, int]:
        """W11-1 transitional shim: log offsets live on MonitorRuntime now.

        Report-assembly methods that still live on this facade
        (``verify_target_reaction``) read offsets through this property
        until W11-2 lands the ``ReportAssembler`` collaborator.
        """
        return self._runtime.log_offsets

    def apply_trigger_payload(self, payload: Any) -> None:
        """Attach trigger-selection metadata to the in-progress report."""
        populate_report_from_trigger_payload(self.report, payload)
        self._persist_report(force=True)

    def set_trigger_execution_mode(self, mode: str) -> None:
        self.report.trigger_execution_mode = str(mode or "").strip()
        self._persist_report(force=False)

    def start(self) -> None:
        """Delegate to MonitorRuntime; preserved for facade public surface."""
        self._runtime.start()

    def attach_runtime_tracers(self) -> None:
        """Delegate to MonitorRuntime; preserved for facade public surface."""
        self._runtime.attach_runtime_tracers()

    def stop(self) -> ActivationReport:
        """Delegate to MonitorRuntime; preserved for facade public surface."""
        return self._runtime.stop()

    def __enter__(self) -> ExtensionMonitor:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        _ = (exc_type, exc, tb)
        self.stop()

    def _handle_network_event(self, event: NetworkEvent) -> None:
        """W11-1 transitional shim: forward to runtime handler."""
        self._runtime._handle_network_event(event)

    def _handle_process_event(self, event: ProcessEvent) -> None:
        """W11-1 transitional shim: forward to runtime handler."""
        self._runtime._handle_process_event(event)

    def _handle_file_event(self, event: FileEvent) -> None:
        """W11-1 transitional shim: forward to runtime handler."""
        self._runtime._handle_file_event(event)

    def capture_runtime_snapshot(self) -> dict[str, int | bool]:
        """Delegate to MonitorRuntime; preserved for facade public surface."""
        return self._runtime.capture_runtime_snapshot()

    def mark_trigger_plan_applied(
        self,
        *,
        scenarios: list[str] | None = None,
        trigger_path: str | None = None,
    ) -> None:
        self.report.trigger_plan_applied = True
        if scenarios:
            self.report.requested_scenarios = list(scenarios)
        if trigger_path:
            self.report.trigger_plan_path = trigger_path
        self._persist_report(force=False)

    def mark_trigger_plan_missing(self, trigger_path: str = "") -> None:
        self.report.trigger_plan_requested = True
        self.report.trigger_plan_loaded = False
        if trigger_path:
            self.report.trigger_plan_path = trigger_path
        self._persist_report(force=False)

    def record_failed_scenarios(self, failed_scenarios: list[str]) -> None:
        self.report.failed_scenarios = sorted(set(failed_scenarios))
        self._synchronize_scenario_truth()
        self._persist_report(force=False)

    def record_execution_result(self, result: Any) -> None:
        self.report.requested_scenarios = [
            str(name).strip()
            for name in getattr(result, "requested_scenarios", []) or []
            if str(name).strip()
        ]
        self.report.skipped_scenarios = [
            SkippedScenarioRecord(
                name=str(getattr(item, "name", "")).strip(),
                reason_code=str(getattr(item, "reason_code", "")).strip(),
                detail=str(getattr(item, "detail", "")).strip(),
            )
            for item in getattr(result, "skipped_scenarios", []) or []
            if str(getattr(item, "name", "")).strip()
            and str(getattr(item, "reason_code", "")).strip()
        ]
        self.report.extra_trigger_failures = [
            str(item).strip()
            for item in getattr(result, "extra_trigger_failures", []) or []
            if str(item).strip()
        ]
        self.record_failed_scenarios(
            [
                str(name).strip()
                for name in getattr(result, "failed_scenarios", []) or []
                if str(name).strip()
            ]
        )

    def record_stimulus_pass_event(
        self,
        action: str,
        pass_id: str,
        *,
        label: str = "",
        order: int = 0,
        trigger_method: str = "",
        status: str = "",
    ) -> None:
        now = time.time()
        trace = next(
            (item for item in self.report.stimulus_passes if item.pass_id == pass_id),
            None,
        )
        if action == "start":
            if trace is None:
                trace = StimulusPassTrace(
                    pass_id=pass_id,
                    label=label or pass_id,
                    order=order,
                    started_at=now,
                    status="running",
                    trigger_method=trigger_method,
                )
                self.report.stimulus_passes.append(trace)
            else:
                trace.started_at = now
                trace.status = "running"
                if label:
                    trace.label = label
                if order:
                    trace.order = order
                if trigger_method:
                    trace.trigger_method = trigger_method
        else:
            if trace is None:
                trace = StimulusPassTrace(
                    pass_id=pass_id,
                    label=label or pass_id,
                    order=order,
                    started_at=now,
                    ended_at=now,
                    status=status or "completed",
                    trigger_method=trigger_method,
                )
                self.report.stimulus_passes.append(trace)
            else:
                trace.ended_at = now
                trace.status = status or "completed"
        self.record_automation_event(
            "stimulus_pass",
            _build_stimulus_pass_log_message(
                action,
                label or pass_id,
                status=status or ("running" if action == "start" else "completed"),
            ),
            status=status or ("running" if action == "start" else "completed"),
        )

    def record_prerequisite_result(
        self,
        prerequisite_id: str,
        *,
        status: str,
        detail: str = "",
        reason_code: str = "",
        resolved_targets: dict[str, Any] | None = None,
    ) -> None:
        existing = next(
            (
                item
                for item in self.report.prerequisite_results
                if item.prerequisite_id == prerequisite_id
            ),
            None,
        )
        if existing is None:
            existing = PrerequisiteResult(
                prerequisite_id=prerequisite_id,
                key=prerequisite_id,
                label=prerequisite_id,
            )
            self.report.prerequisite_results.append(existing)
        existing.status = status
        if detail:
            existing.detail = detail
        if reason_code:
            existing.reason_code = reason_code
        if resolved_targets:
            existing.resolved_targets = dict(resolved_targets)
        self.record_automation_event(
            "prerequisite",
            _build_prerequisite_log_message(existing),
            status=status,
        )

    def record_event_attempt_start(
        self,
        attempt_id: str,
        *,
        pass_name: str = "",
    ) -> None:
        attempt = _find_event_attempt(self.report, attempt_id)
        if attempt is None:
            return
        attempt.status = "running"
        if pass_name:
            attempt.attempted_passes = list(
                dict.fromkeys([*attempt.attempted_passes, pass_name])
            )
        self.record_automation_event(
            "event_attempt",
            f"Starting event attempt {attempt.activation_event or attempt.event_family}",
            status="running",
            activation_event=attempt.activation_event,
        )

    def record_event_attempt_end(
        self,
        attempt_id: str,
        *,
        status: str,
        pass_name: str = "",
        trigger_method_used: str = "",
        result_details: str = "",
        failure_reason_code: str = "",
        blocked_reason_code: str = "",
    ) -> None:
        attempt = _find_event_attempt(self.report, attempt_id)
        if attempt is None:
            return
        attempt.status = status
        if pass_name:
            attempt.attempted_passes = list(
                dict.fromkeys([*attempt.attempted_passes, pass_name])
            )
        if trigger_method_used:
            attempt.trigger_method_used = trigger_method_used
        if result_details:
            attempt.result_details = result_details
        if failure_reason_code:
            attempt.failure_reason_code = failure_reason_code
        if blocked_reason_code:
            attempt.blocked_reason_code = blocked_reason_code
        attempt.verification_status = (
            "verified"
            if status == "verified"
            else "attempted_only"
            if status == "attempted_only"
            else "failed"
            if status == "failed"
            else "blocked"
            if status == "blocked"
            else attempt.verification_status
        )
        self.record_automation_event(
            "event_attempt",
            _build_event_attempt_log_message(attempt),
            status=status,
            activation_event=attempt.activation_event,
        )

    def record_scenario_event(
        self,
        action: str,
        name: str,
        status: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        now = time.time()
        if action == "start":
            started_trace = ScenarioTrace(name=name, started_at=now)
            self._active_scenarios[name] = started_trace
            self.report.scenario_traces.append(started_trace)
        elif action == "end":
            finished_trace = (
                self._active_scenarios.pop(name)
                if name in self._active_scenarios
                else None
            )
            if finished_trace is None:
                finished_trace = ScenarioTrace(name=name, started_at=now)
                self.report.scenario_traces.append(finished_trace)
            finished_trace.ended_at = now
            finished_trace.status = status or "completed"
            if metadata:
                reason_code = str(metadata.get("failure_reason_code", "") or "")
                if reason_code:
                    finished_trace.failure_reason_code = reason_code
                error_detail = str(metadata.get("error", "") or "")
                if error_detail:
                    finished_trace.error_detail = error_detail[:500]
        message = _build_scenario_log_message(action, name, status, metadata)
        self.report.log_entries.append(
            LogStreamEntry(
                timestamp=_format_epoch_timestamp(now),
                rel_time_s=_relative_time(now, self.report.monitoring_start),
                stream="automation",
                kind="scenario",
                message=message,
                scenario_name=name,
                status=status or ("running" if action == "start" else "completed"),
            )
        )
        self._synchronize_scenario_truth()
        self._persist_report(force=False)

    def _append_activation_log_entries(self) -> None:
        existing_keys = {
            (
                entry.stream,
                entry.kind,
                entry.extension_id,
                entry.activation_event,
                entry.timestamp,
                entry.message,
            )
            for entry in self.report.log_entries
        }
        for entry in self.report.activated:
            rel_time = _relative_time(
                _parse_iso_timestamp(entry.timestamp),
                self.report.monitoring_start,
            )
            scenario_name = _scenario_name_for_timestamp(
                entry.timestamp,
                rel_time,
                self.report.scenario_traces,
                self.report.monitoring_start,
            )
            is_target = bool(
                self.report.target_extension_id
                and entry.extension_id == self.report.target_extension_id
            )
            message = _build_activation_log_message(entry)
            key = (
                "target_extension_host" if is_target else "other_extension_host",
                "activation",
                entry.extension_id,
                entry.activation_event,
                entry.timestamp,
                message,
            )
            if key in existing_keys:
                continue
            existing_keys.add(key)
            self.report.log_entries.append(
                LogStreamEntry(
                    timestamp=entry.timestamp,
                    rel_time_s=rel_time,
                    stream="target_extension_host"
                    if is_target
                    else "other_extension_host",
                    kind="activation",
                    message=message,
                    extension_id=entry.extension_id,
                    activation_event=entry.activation_event,
                    scenario_name=scenario_name,
                    status="completed" if entry.success else "failed",
                    is_target_extension=is_target,
                )
            )
            _assert_target_stream_invariant(
                self.report.log_entries[-1], self.report.target_extension_id
            )

    def record_automation_event(
        self,
        kind: str,
        message: str,
        status: str = "",
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        now = time.time()
        stream = "ui_blockers" if kind.startswith("ui_blocker") else "automation"
        self.report.log_entries.append(
            LogStreamEntry(
                timestamp=_format_epoch_timestamp(now),
                rel_time_s=_relative_time(now, self.report.monitoring_start),
                stream=stream,
                kind=kind,
                message=message,
                scenario_name=scenario_name,
                activation_event=activation_event,
                status=status,
            )
        )
        # PR345 PR4: defensive — automation/ui_blocker streams cannot
        # legally land on target_extension_host; invariant call is a no-op
        # today but locks the route if a future kind ever picks that key.
        _assert_target_stream_invariant(
            self.report.log_entries[-1], self.report.target_extension_id
        )
        self._persist_report(force=False)

    def verify_target_reaction(
        self,
        baseline: dict[str, int | bool],
        *,
        capability: str,
        trigger_label: str,
        activation_event: str = "",
        success_signal: bool = False,
    ) -> bool:
        api = resolve_monitor_api()
        current_target_activations = _count_target_activations(
            api.parse_all_exthost_logs(start_offsets=self._log_offsets),
            self.report.target_extension_id,
        )
        new_activity = len(self.report.target_file_events) > int(
            baseline.get("target_file_events", 0)
        ) or len(self.report.target_network_events) > int(
            baseline.get("target_network_events", 0)
        )
        ui_blocked = len(self.report.ui_blocker_entries) > int(
            baseline.get("ui_blockers", 0)
        )
        activation_seen = current_target_activations > int(
            baseline.get("target_activations", 0)
        )
        verified = activation_seen or new_activity or success_signal
        if verified:
            if capability in self.report.attempted_capabilities:
                self.report.verified_capabilities = sorted(
                    set(self.report.verified_capabilities) | {capability}
                )
            if capability in self.report.heuristic_attempted_capabilities:
                self.report.heuristic_verified_capabilities = sorted(
                    set(self.report.heuristic_verified_capabilities) | {capability}
                )
        status = "completed" if verified else "failed"
        message = (
            f"Verified {capability} trigger {trigger_label}"
            if verified
            else f"Trigger {trigger_label} did not produce a verified target reaction"
        )
        if ui_blocked and not verified:
            message += " because a UI blocker interrupted the flow"
        self.record_automation_event(
            "command_verification",
            message,
            status=status,
            activation_event=activation_event,
        )
        return verified

    def _finalize_running_scenarios(self) -> None:
        ended_at = self.report.monitoring_end or time.time()
        for trace in self._active_scenarios.values():
            trace.ended_at = ended_at
            if trace.status == "running":
                trace.status = "completed"
        self._active_scenarios.clear()
        self._synchronize_scenario_truth()

    def _synchronize_scenario_truth(self) -> None:
        self.report.scenarios_run = [
            trace.name
            for trace in self.report.scenario_traces
            if str(trace.name).strip()
        ]
        self.report.failed_scenarios = list(
            dict.fromkeys(
                trace.name
                for trace in self.report.scenario_traces
                if str(trace.name).strip() and str(trace.status).strip() == "failed"
            )
        )

    def _refresh_derived_report_state(self) -> None:
        """W11-2 transitional shim: report assembly lives on ``ReportAssembler``.

        Kept on the facade so the W11-1 pin file's
        ``runtime.refresh_derived_state == mon._refresh_derived_report_state``
        bound-method-identity assertion remains stable until W11-5
        collapses the facade.
        """
        self._assembler.refresh_derived_state()

    def _persist_report(self, force: bool) -> None:
        """W11-2 transitional shim: persist debounce lives on ``ReportAssembler``.

        Kept on the facade so the W11-1 pin file's
        ``runtime.persist == mon._persist_report`` bound-method-identity
        assertion remains stable until W11-5 collapses the facade.
        """
        self._assembler.persist(force)

    def _set_discovery_strategies(self, strategies: list[str]) -> None:
        """W11-3 transitional shim: discovery strategies live on ``ReportAssembler``.

        Kept on the facade so the runtime collaborator's bound-method
        identity matches the assembler delegation pattern from W11-1 /
        W11-2 (callbacks routed through facade, never directly to the
        assembler) until W11-5 collapses the facade.
        """
        self._assembler.set_discovery_strategies(strategies)

    def set_runner_status(self, exit_code: int) -> None:
        """W11-3: surface runner exit status on the report.

        Called by ``entrypoint_runner`` immediately before
        ``SystemExit(exit_code)``; the assembler derives ``runner_status``
        from the code and writes both fields to the live
        ``ActivationReport``. A subsequent ``_persist_report(force=True)``
        is the runner's responsibility so the new fields hit disk.
        """
        self._assembler.set_runner_status(exit_code)


def check_extension_activated(extension_id: str, page: Page | None = None) -> bool:
    """Quick check: is a specific extension activated?"""
    api = resolve_monitor_api()
    for entry in api.parse_all_exthost_logs():
        if entry.extension_id == extension_id:
            return True

    if page is not None:
        for ext in api.get_running_extensions(page):
            if ext.extension_id == extension_id:
                return True

    return False


__all__ = ["ExtensionMonitor", "check_extension_activated"]
