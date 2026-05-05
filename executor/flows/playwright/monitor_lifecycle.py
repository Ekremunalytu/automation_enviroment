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
)
from .monitor_payload import populate_report_from_trigger_payload
from .monitor_records import (
    LogStreamEntry,
    PrerequisiteResult,
    StimulusPassTrace,
    _assert_target_stream_invariant,
)
from .monitor_report_assembler import ReportAssembler
from .monitor_runtime import (
    _build_prerequisite_log_message,
    _build_stimulus_pass_log_message,
    _count_target_activations,
)
from .monitor_runtime_state import MonitorRuntime
from .monitor_scenario_accountant import ScenarioAccountant
from .monitor_support import resolve_monitor_api
from .monitor_types import ActivationReport
from .runtime_capture.events import FileEvent, NetworkEvent, ProcessEvent

# ``_assert_target_stream_invariant`` is re-exported so the existing
# test pin ``from executor.flows.playwright.monitor_lifecycle import
# _assert_target_stream_invariant`` keeps working after W11-4 moved
# the helper to ``monitor_records`` (next to ``LogStreamEntry``).
__all__ = [
    "ExtensionMonitor",
    "_assert_target_stream_invariant",
    "check_extension_activated",
]


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
        # W11-2: derived-state refresh + persist debounce moved into
        # ReportAssembler. The facade keeps thin _refresh_…/_persist_…
        # shims (below) so the W11-1 facade pin file's bound-method
        # identity assertions stay green.
        self._assembler = ReportAssembler(
            report=self.report,
            report_path=self.report_path,
        )
        # W11-4: scenario / event-attempt accounting and the producer
        # signal for ``[FOLLOWUP target-log-lifecycle-instrumentation]``
        # live on ScenarioAccountant. The facade keeps thin shims for
        # ``mark_trigger_plan_*`` / ``record_*`` /
        # ``_finalize_running_scenarios`` / ``_append_activation_log_entries``
        # / ``_synchronize_scenario_truth`` so the W11-1 facade pin
        # file's bound-method-identity assertions
        # (``runtime.finalize_scenarios == mon._finalize_running_scenarios``,
        # ``runtime.append_activation_log_entries == mon._append_activation_log_entries``)
        # remain green until W11-5 collapses the facade.
        self._scenario_accountant = ScenarioAccountant(
            report=self.report,
            record_automation_event=self.record_automation_event,
            persist=self._persist_report,
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
            emit_intermediate_state_events=self._emit_intermediate_state_events,
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
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.mark_trigger_plan_applied(
            scenarios=scenarios,
            trigger_path=trigger_path,
        )

    def mark_trigger_plan_missing(self, trigger_path: str = "") -> None:
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.mark_trigger_plan_missing(trigger_path)

    def record_failed_scenarios(self, failed_scenarios: list[str]) -> None:
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.record_failed_scenarios(failed_scenarios)

    def record_execution_result(self, result: Any) -> None:
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.record_execution_result(result)

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
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.record_event_attempt_start(
            attempt_id,
            pass_name=pass_name,
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
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.record_event_attempt_end(
            attempt_id,
            status=status,
            pass_name=pass_name,
            trigger_method_used=trigger_method_used,
            result_details=result_details,
            failure_reason_code=failure_reason_code,
            blocked_reason_code=blocked_reason_code,
        )

    def record_scenario_event(
        self,
        action: str,
        name: str,
        status: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``."""
        self._scenario_accountant.record_scenario_event(action, name, status, metadata)

    def _append_activation_log_entries(self) -> None:
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``.

        Kept on the facade so ``runtime.append_activation_log_entries
        == mon._append_activation_log_entries`` (W11-1 bound-method
        identity invariant) holds until W11-5 collapses the facade.
        """
        self._scenario_accountant.append_activation_log_entries()

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
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``.

        Kept on the facade so ``runtime.finalize_scenarios ==
        mon._finalize_running_scenarios`` (W11-1 bound-method identity
        invariant) holds until W11-5 collapses the facade.
        """
        self._scenario_accountant.finalize_running_scenarios()

    def _synchronize_scenario_truth(self) -> None:
        """W11-4 transitional shim: delegates to ``ScenarioAccountant``.

        Kept on the facade for direct callers that bypass
        ``record_*_scenarios`` (none today, but the shim keeps the
        public-ish surface stable until W11-5).
        """
        self._scenario_accountant._synchronize_scenario_truth()

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

    def _emit_intermediate_state_events(self) -> None:
        """W11-4 transitional shim: producer signal for intermediate states.

        Wired into ``MonitorRuntime.stop()`` after
        ``_refresh_derived_report_state`` so emitted events reflect the
        post-reconcile truth. Delegates to
        ``ScenarioAccountant.emit_intermediate_state_events`` which
        appends an automation-stream log entry for every event_attempt
        whose verification_status reached ``activation_seen`` or
        ``target_log_seen``. The shim shape mirrors W11-2/W11-3 so the
        facade pin file can keep its bound-method-identity invariants
        green.
        """
        self._scenario_accountant.emit_intermediate_state_events()


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
