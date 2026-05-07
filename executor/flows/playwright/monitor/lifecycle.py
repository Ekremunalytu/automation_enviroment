"""Extension monitor lifecycle and orchestration helpers."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import time
from pathlib import Path
from types import TracebackType
from typing import Any

from playwright.sync_api import Page

from ..attribution import (
    format_epoch_timestamp,
    relative_time,
)
from .payload import populate_report_from_trigger_payload
from .records import (
    LogStreamEntry,
    _assert_target_stream_invariant,
)
from .report_assembler import ReportAssembler
from .runtime_state import MonitorRuntime
from .scenario_accountant import ScenarioAccountant
from .support import resolve_monitor_api
from .types import ActivationReport

# ``_assert_target_stream_invariant`` is re-exported so the existing
# test pin keeps importing it from this module after W11-4 moved
# the helper to ``monitor_records``.
__all__ = [
    "ExtensionMonitor",
    "_assert_target_stream_invariant",
    "check_extension_activated",
]


class ExtensionMonitor:
    """Context manager that captures extension activations around scenario execution.

    W11-5 collapsed the facade into a thin composition over three
    collaborators (`MonitorRuntime`, `ReportAssembler`,
    `ScenarioAccountant`). Runtime callbacks bind directly to the
    collaborator methods — no shim layer in between. Tests that need to
    swap a collaborator pass a pre-built instance through the keyword
    arguments at construction.
    """

    def __init__(
        self,
        page: Page,
        report_path: str | Path | None = None,
        target_extension_id: str = "",
        *,
        report: ActivationReport | None = None,
        assembler: ReportAssembler | None = None,
        accountant: ScenarioAccountant | None = None,
        runtime: MonitorRuntime | None = None,
    ) -> None:
        self.report_path = None if report_path is None else Path(report_path)
        self.report = report or ActivationReport(
            target_extension_id=target_extension_id
        )
        self._assembler = assembler or ReportAssembler(
            report=self.report,
            report_path=self.report_path,
        )
        self._scenario_accountant = accountant or ScenarioAccountant(
            report=self.report,
            record_automation_event=self.record_automation_event,
            persist=self._assembler.persist,
        )
        self._runtime = runtime or MonitorRuntime(
            page=page,
            report=self.report,
            persist=self._assembler.persist,
            record_automation_event=self.record_automation_event,
            finalize_scenarios=self._scenario_accountant.finalize_running_scenarios,
            append_activation_log_entries=self._scenario_accountant.append_activation_log_entries,
            refresh_derived_state=self._assembler.refresh_derived_state,
            set_discovery_strategies=self._assembler.set_discovery_strategies,
            emit_intermediate_state_events=self._scenario_accountant.emit_intermediate_state_events,
        )

    @property
    def page(self) -> Page:
        return self._runtime.page

    @page.setter
    def page(self, value: Page) -> None:
        self._runtime.page = value

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

    def start(self) -> None:
        self._runtime.start()

    def stop(self) -> ActivationReport:
        return self._runtime.stop()

    def attach_runtime_tracers(self) -> None:
        self._runtime.attach_runtime_tracers()

    def capture_runtime_snapshot(self) -> dict[str, int | bool]:
        return self._runtime.capture_runtime_snapshot()

    def apply_trigger_payload(self, payload: Any) -> None:
        """Attach trigger-selection metadata to the in-progress report."""
        populate_report_from_trigger_payload(self.report, payload)
        self._assembler.persist(force=True)

    def set_trigger_execution_mode(self, mode: str) -> None:
        self.report.trigger_execution_mode = str(mode or "").strip()
        self._assembler.persist(force=False)

    def mark_trigger_plan_applied(
        self,
        *,
        scenarios: list[str] | None = None,
        trigger_path: str | None = None,
    ) -> None:
        self._scenario_accountant.mark_trigger_plan_applied(
            scenarios=scenarios,
            trigger_path=trigger_path,
        )

    def mark_trigger_plan_missing(self, trigger_path: str = "") -> None:
        self._scenario_accountant.mark_trigger_plan_missing(trigger_path)

    def record_failed_scenarios(self, failed_scenarios: list[str]) -> None:
        self._scenario_accountant.record_failed_scenarios(failed_scenarios)

    def record_execution_result(self, result: Any) -> None:
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
        self._scenario_accountant.record_stimulus_pass_event(
            action,
            pass_id,
            label=label,
            order=order,
            trigger_method=trigger_method,
            status=status,
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
        self._scenario_accountant.record_prerequisite_result(
            prerequisite_id,
            status=status,
            detail=detail,
            reason_code=reason_code,
            resolved_targets=resolved_targets,
        )

    def record_event_attempt_start(
        self,
        attempt_id: str,
        *,
        pass_name: str = "",
    ) -> None:
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
        self._scenario_accountant.record_scenario_event(action, name, status, metadata)

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
                timestamp=format_epoch_timestamp(now),
                rel_time_s=relative_time(now, self.report.monitoring_start),
                stream=stream,
                kind=kind,
                message=message,
                scenario_name=scenario_name,
                activation_event=activation_event,
                status=status,
            )
        )
        # PR345 PR4: defensive — automation/ui_blocker streams cannot
        # legally land on target_extension_host; invariant call locks
        # the route if a future kind ever picks that key.
        _assert_target_stream_invariant(
            self.report.log_entries[-1], self.report.target_extension_id
        )
        self._assembler.persist(force=False)

    def verify_target_reaction(
        self,
        baseline: dict[str, int | bool],
        *,
        capability: str,
        trigger_label: str,
        activation_event: str = "",
        success_signal: bool = False,
    ) -> bool:
        return self._scenario_accountant.verify_target_reaction(
            baseline,
            self._runtime.log_offsets,
            capability=capability,
            trigger_label=trigger_label,
            activation_event=activation_event,
            success_signal=success_signal,
        )

    def set_runner_status(self, exit_code: int) -> None:
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
