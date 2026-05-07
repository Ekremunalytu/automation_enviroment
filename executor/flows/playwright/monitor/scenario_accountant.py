"""Scenario / event-attempt accounting collaborator (W11-4).

Encapsulates the scenario-lifecycle and event-attempt accounting that
previously lived on the ``ExtensionMonitor`` facade in
``monitor_lifecycle``:

* trigger-plan and execution-result intake
  (``mark_trigger_plan_applied`` / ``mark_trigger_plan_missing`` /
  ``record_failed_scenarios`` / ``record_execution_result``);
* scenario lifecycle bookkeeping (``record_scenario_event``,
  ``finalize_running_scenarios``, ``_synchronize_scenario_truth``,
  ``_active_scenarios`` dict);
* event-attempt status mutation (``record_event_attempt_start`` /
  ``record_event_attempt_end``);
* activation-window log derivation
  (``append_activation_log_entries``);
* W11-4 producer signal for ``[FOLLOWUP target-log-lifecycle-instrumentation]``:
  ``emit_intermediate_state_events`` walks ``report.event_attempts``
  after ``ReportAssembler.refresh_derived_state`` has run
  ``reconcile_event_attempts`` and surfaces the ``activation_seen`` /
  ``target_log_seen`` promotions in the live automation timeline. The
  reconciler already mutates ``verification_status`` to those literals
  (W10-6 alphabet + ``health_reconciliation`` consumer side); this is
  the missing producer-side vocabulary that W11-4 closes.

The owning ``ExtensionMonitor`` facade composes this collaborator and
keeps thin one-line shims so the W11-1 / W11-2 / W11-3 facade pin
file's bound-method-identity assertions
(``runtime.finalize_scenarios == mon._finalize_running_scenarios``,
``runtime.append_activation_log_entries == mon._append_activation_log_entries``)
remain green. Cross-module side effects (recording automation events,
persisting the report) are passed in as callbacks at construction time
so the accountant stays free of facade-ownership responsibilities.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..attribution import (
    _format_epoch_timestamp,
    _relative_time,
    _scenario_name_for_timestamp,
)
from ..runtime_capture._shared import _parse_iso_timestamp
from .records import (
    LogStreamEntry,
    PrerequisiteResult,
    ScenarioTrace,
    SkippedScenarioRecord,
    StimulusPassTrace,
    _assert_target_stream_invariant,
)
from .runtime import (
    _build_activation_log_message,
    _build_event_attempt_log_message,
    _build_prerequisite_log_message,
    _build_scenario_log_message,
    _build_stimulus_pass_log_message,
    _count_target_activations,
    _find_event_attempt,
)
from .support import resolve_monitor_api
from .types import ActivationReport

PersistCallback = Callable[[bool], None]
RecordAutomationEventCallback = Callable[..., None]


class ScenarioAccountant:
    """Owns scenario / event-attempt accounting for ``ExtensionMonitor``.

    Constructed by :class:`ExtensionMonitor`. Mutates the shared
    ``ActivationReport`` in place. Cross-module operations
    (``record_automation_event``, ``persist``) are wired in via
    callbacks so the facade keeps ownership of timeline emission and
    persistence debouncing.
    """

    def __init__(
        self,
        *,
        report: ActivationReport,
        record_automation_event: RecordAutomationEventCallback,
        persist: PersistCallback,
    ) -> None:
        self._report = report
        self._record_automation_event = record_automation_event
        self._persist = persist
        self._active_scenarios: dict[str, ScenarioTrace] = {}
        self._emitted_intermediate_state_attempts: set[str] = set()

    # ------------------------------------------------------------------
    # Trigger-plan + execution-result intake
    # ------------------------------------------------------------------

    def mark_trigger_plan_applied(
        self,
        *,
        scenarios: list[str] | None = None,
        trigger_path: str | None = None,
    ) -> None:
        self._report.trigger_plan_applied = True
        if scenarios:
            self._report.requested_scenarios = list(scenarios)
        if trigger_path:
            self._report.trigger_plan_path = trigger_path
        self._persist(False)

    def mark_trigger_plan_missing(self, trigger_path: str = "") -> None:
        self._report.trigger_plan_requested = True
        self._report.trigger_plan_loaded = False
        if trigger_path:
            self._report.trigger_plan_path = trigger_path
        self._persist(False)

    def record_failed_scenarios(self, failed_scenarios: list[str]) -> None:
        self._report.failed_scenarios = sorted(set(failed_scenarios))
        self._synchronize_scenario_truth()
        self._persist(False)

    def record_execution_result(self, result: Any) -> None:
        self._report.requested_scenarios = [
            str(name).strip()
            for name in getattr(result, "requested_scenarios", []) or []
            if str(name).strip()
        ]
        self._report.skipped_scenarios = [
            SkippedScenarioRecord(
                name=str(getattr(item, "name", "")).strip(),
                reason_code=str(getattr(item, "reason_code", "")).strip(),
                detail=str(getattr(item, "detail", "")).strip(),
            )
            for item in getattr(result, "skipped_scenarios", []) or []
            if str(getattr(item, "name", "")).strip()
            and str(getattr(item, "reason_code", "")).strip()
        ]
        self._report.extra_trigger_failures = [
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
        self._validate_scenario_conservation()

    # ------------------------------------------------------------------
    # Stimulus passes + prerequisites
    # ------------------------------------------------------------------

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
            (item for item in self._report.stimulus_passes if item.pass_id == pass_id),
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
                self._report.stimulus_passes.append(trace)
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
                self._report.stimulus_passes.append(trace)
            else:
                trace.ended_at = now
                trace.status = status or "completed"
        self._record_automation_event(
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
                for item in self._report.prerequisite_results
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
            self._report.prerequisite_results.append(existing)
        existing.status = status
        if detail:
            existing.detail = detail
        if reason_code:
            existing.reason_code = reason_code
        if resolved_targets:
            existing.resolved_targets = dict(resolved_targets)
        self._record_automation_event(
            "prerequisite",
            _build_prerequisite_log_message(existing),
            status=status,
        )

    # ------------------------------------------------------------------
    # Event-attempt mutations
    # ------------------------------------------------------------------

    def record_event_attempt_start(
        self,
        attempt_id: str,
        *,
        pass_name: str = "",
    ) -> None:
        attempt = _find_event_attempt(self._report, attempt_id)
        if attempt is None:
            return
        attempt.status = "running"
        if pass_name:
            attempt.attempted_passes = list(
                dict.fromkeys([*attempt.attempted_passes, pass_name])
            )
        self._record_automation_event(
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
        attempt = _find_event_attempt(self._report, attempt_id)
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
        self._record_automation_event(
            "event_attempt",
            _build_event_attempt_log_message(attempt),
            status=status,
            activation_event=attempt.activation_event,
        )

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

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
            self._report.scenario_traces.append(started_trace)
        elif action == "end":
            finished_trace = (
                self._active_scenarios.pop(name)
                if name in self._active_scenarios
                else None
            )
            if finished_trace is None:
                finished_trace = ScenarioTrace(name=name, started_at=now)
                self._report.scenario_traces.append(finished_trace)
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
        self._report.log_entries.append(
            LogStreamEntry(
                timestamp=_format_epoch_timestamp(now),
                rel_time_s=_relative_time(now, self._report.monitoring_start),
                stream="automation",
                kind="scenario",
                message=message,
                scenario_name=name,
                status=status or ("running" if action == "start" else "completed"),
            )
        )
        self._synchronize_scenario_truth()
        self._persist(False)

    def finalize_running_scenarios(self) -> None:
        """End every still-running ``ScenarioTrace`` at monitoring close.

        Wired into ``MonitorRuntime.stop()`` as the
        ``finalize_scenarios`` callback (via the facade shim
        ``ExtensionMonitor._finalize_running_scenarios``). Idempotent:
        repeated calls clear ``_active_scenarios`` and synchronize
        scenario-truth derivation again with no further mutation.
        """
        ended_at = self._report.monitoring_end or time.time()
        for trace in self._active_scenarios.values():
            trace.ended_at = ended_at
            if trace.status == "running":
                trace.status = "completed"
        self._active_scenarios.clear()
        self._synchronize_scenario_truth()
        self._validate_scenario_conservation()

    def _validate_scenario_conservation(self) -> None:
        """Enforce W7 §10.7 scenario-dropout honesty as a downstream guard.

        Pin: every entry in ``requested_scenarios`` must appear in exactly
        one of ``scenarios_run`` / ``failed_scenarios`` / ``skipped_scenarios``.
        Anything missing is appended to ``skipped_scenarios`` with
        ``reason_code='unaccounted_dropout'`` so the JSON cannot silently
        lose a scenario. Upstream layers (planner, ``stimulus_passes``,
        harness) should still record their own drop reasons; this is the
        last-mile catch that keeps the W7 §10.7 invariant honest even if
        an upstream layer leaks. Idempotent — a second call after the
        missing entries are appended sees an empty difference.
        """
        requested = {
            str(name).strip()
            for name in self._report.requested_scenarios
            if str(name).strip()
        }
        accounted = (
            {
                str(name).strip()
                for name in self._report.scenarios_run
                if str(name).strip()
            }
            | {
                str(name).strip()
                for name in self._report.failed_scenarios
                if str(name).strip()
            }
            | {
                str(record.name).strip()
                for record in self._report.skipped_scenarios
                if str(record.name).strip()
            }
        )
        for name in sorted(requested - accounted):
            self._report.skipped_scenarios.append(
                SkippedScenarioRecord(
                    name=name,
                    reason_code="unaccounted_dropout",
                    detail=(
                        "Scenario was requested but never recorded as run, "
                        "failed, or skipped by the upstream planner / "
                        "executor / harness."
                    ),
                )
            )

    def _synchronize_scenario_truth(self) -> None:
        self._report.scenarios_run = [
            trace.name
            for trace in self._report.scenario_traces
            if str(trace.name).strip()
        ]
        self._report.failed_scenarios = list(
            dict.fromkeys(
                trace.name
                for trace in self._report.scenario_traces
                if str(trace.name).strip() and str(trace.status).strip() == "failed"
            )
        )

    # ------------------------------------------------------------------
    # Target reaction verification
    # ------------------------------------------------------------------

    def verify_target_reaction(
        self,
        baseline: dict[str, int | bool],
        log_offsets: dict[str, int],
        *,
        capability: str,
        trigger_label: str,
        activation_event: str = "",
        success_signal: bool = False,
    ) -> bool:
        """Decide whether a trigger produced a verified target reaction.

        W11-5 moved this from the facade to the accountant. ``log_offsets``
        is now an explicit argument because the runtime owns it; the
        facade pulls them from ``MonitorRuntime.log_offsets`` and forwards.
        """
        api = resolve_monitor_api()
        current_target_activations = _count_target_activations(
            api.parse_all_exthost_logs(start_offsets=log_offsets),
            self._report.target_extension_id,
        )
        new_activity = len(self._report.target_file_events) > int(
            baseline.get("target_file_events", 0)
        ) or len(self._report.target_network_events) > int(
            baseline.get("target_network_events", 0)
        )
        ui_blocked = len(self._report.ui_blocker_entries) > int(
            baseline.get("ui_blockers", 0)
        )
        activation_seen = current_target_activations > int(
            baseline.get("target_activations", 0)
        )
        verified = activation_seen or new_activity or success_signal
        if verified:
            if capability in self._report.attempted_capabilities:
                self._report.verified_capabilities = sorted(
                    set(self._report.verified_capabilities) | {capability}
                )
            if capability in self._report.heuristic_attempted_capabilities:
                self._report.heuristic_verified_capabilities = sorted(
                    set(self._report.heuristic_verified_capabilities) | {capability}
                )
        status = "completed" if verified else "failed"
        message = (
            f"Verified {capability} trigger {trigger_label}"
            if verified
            else f"Trigger {trigger_label} did not produce a verified target reaction"
        )
        if ui_blocked and not verified:
            message += " because a UI blocker interrupted the flow"
        self._record_automation_event(
            "command_verification",
            message,
            status=status,
            activation_event=activation_event,
        )
        return verified

    # ------------------------------------------------------------------
    # Activation-window log derivation
    # ------------------------------------------------------------------

    def append_activation_log_entries(self) -> None:
        """Mirror each ``ActivationEntry`` into the timeline log streams.

        Wired into ``MonitorRuntime.stop()`` as the
        ``append_activation_log_entries`` callback (via the facade
        shim). Skips entries already represented in ``log_entries`` so
        repeated calls are idempotent.
        """
        existing_keys = {
            (
                entry.stream,
                entry.kind,
                entry.extension_id,
                entry.activation_event,
                entry.timestamp,
                entry.message,
            )
            for entry in self._report.log_entries
        }
        for entry in self._report.activated:
            rel_time = _relative_time(
                _parse_iso_timestamp(entry.timestamp),
                self._report.monitoring_start,
            )
            scenario_name = _scenario_name_for_timestamp(
                entry.timestamp,
                rel_time,
                self._report.scenario_traces,
                self._report.monitoring_start,
            )
            is_target = bool(
                self._report.target_extension_id
                and entry.extension_id == self._report.target_extension_id
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
            self._report.log_entries.append(
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
                self._report.log_entries[-1], self._report.target_extension_id
            )

    # ------------------------------------------------------------------
    # W11-4 producer signal: intermediate-state vocabulary
    # ------------------------------------------------------------------

    def emit_intermediate_state_events(self) -> None:
        """Surface ``activation_seen`` / ``target_log_seen`` promotions.

        ``[FOLLOWUP target-log-lifecycle-instrumentation]`` producer
        side. ``reconcile_event_attempts`` (consumer side, owned by
        ``health_reconciliation``) already promotes upgradeable
        attempts to ``activation_seen`` or ``target_log_seen`` based on
        target activation matches and target-owned log evidence. Until
        this method ran, no automation-timeline event reflected the
        promotion — analysts saw the final ``verification_status`` on
        the attempt, but the live log stream had no entry pinning the
        moment of transition. The W10-6 alphabet had no vocabulary.

        Wired into ``MonitorRuntime.stop()`` *after*
        ``refresh_derived_state`` (which runs the reconciler) so the
        emitted events reflect the post-reconcile truth. Idempotent:
        each attempt fires at most once via
        ``_emitted_intermediate_state_attempts`` so a future
        re-invocation (e.g. a second ``stop()`` call in tests) does not
        double-log.
        """
        for attempt in self._report.event_attempts:
            attempt_id = str(getattr(attempt, "attempt_id", "")).strip()
            if (
                not attempt_id
                or attempt_id in self._emitted_intermediate_state_attempts
            ):
                continue
            verification_status = str(
                getattr(attempt, "verification_status", "")
            ).strip()
            if verification_status not in {"activation_seen", "target_log_seen"}:
                continue
            self._emitted_intermediate_state_attempts.add(attempt_id)
            event_label = (
                getattr(attempt, "activation_event", "")
                or getattr(attempt, "event_family", "")
                or attempt_id
            )
            if verification_status == "activation_seen":
                message = (
                    f"Target activation observed for event attempt {event_label}; "
                    "full verification (runtime capability / harness trace) pending."
                )
            else:
                message = (
                    "Target activation and target-owned log evidence observed for "
                    f"event attempt {event_label}; runtime capability / harness "
                    "completion still unverified."
                )
            self._record_automation_event(
                "event_attempt",
                message,
                status=verification_status,
                activation_event=getattr(attempt, "activation_event", ""),
            )


__all__ = ["ScenarioAccountant"]
