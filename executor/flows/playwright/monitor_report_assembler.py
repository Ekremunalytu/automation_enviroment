"""Report assembly collaborator for ``ExtensionMonitor`` (W11-2).

Encapsulates the two report-side responsibilities that previously lived
on the ``ExtensionMonitor`` facade in ``monitor_lifecycle``:

* ``refresh_derived_state`` — re-annotates network/file/process events
  with target/scenario attribution, derives verified-vs-heuristic
  capability sets, reconciles event_attempts, populates the coverage
  tuple, builds the ``signal_summary`` (which is where ADR 0003 verdict
  rollup sits), and refreshes ``evidence_links``.
* ``persist`` — debounce-throttled write of the live ``ActivationReport``
  to ``report_path`` when one is configured. Owns the ``_last_persist_at``
  throttle state.

The owning ``ExtensionMonitor`` facade composes this collaborator at
construction time and keeps thin one-line shims
(``_refresh_derived_report_state`` / ``_persist_report``) so that the
W11-1 facade pin file (``tests/executor/test_extension_monitor_facade.py``)
keeps its ``runtime.persist == mon._persist_report`` bound-method
identity invariant intact until W11-5 collapses the facade. Future
acceptance sub-tasks that the assembler is the natural landing for —
``runner_exit_code``/``runner_status`` first-class fields
(``[FOLLOWUP runner-status-contract]``) and the ``activation_seen``/
``target_log_seen`` intermediate-state emission
(``[FOLLOWUP target-log-lifecycle-instrumentation]``) — are deferred to
W11-3 (contract bump) and W11-4 (``ScenarioAccountant`` producer side)
respectively, so this round stays a pure code-restructure.

The assembler holds the ``ActivationReport`` by reference (mirroring
``MonitorRuntime`` from W11-1) and never mutates ``report_path`` after
init; the facade also never mutates its own ``report_path`` post-init,
so the two views cannot drift.
"""

from __future__ import annotations

import time
from pathlib import Path

from .attribution import (
    _annotate_file_events,
    _annotate_network_events,
    _annotate_process_events,
    _build_signal_summary,
)
from .health import (
    derive_verified_capabilities,
    reconcile_event_attempts,
    summarize_event_attempts_for_report,
)
from .monitor_runtime import _reconcile_coverage_verification
from .monitor_types import ActivationReport
from .runtime_capture._shared import _log


class ReportAssembler:
    """Owns derived-report-state refresh and persistence debounce.

    Constructed by :class:`ExtensionMonitor`. Mutates the shared
    ``ActivationReport`` in place. The persist throttle state
    (``_last_persist_at``) is private; only :meth:`persist` reads or
    writes it.
    """

    def __init__(
        self,
        *,
        report: ActivationReport,
        report_path: Path | None,
    ) -> None:
        self._report = report
        self._report_path = report_path
        self._last_persist_at: float = 0.0

    def refresh_derived_state(self) -> None:
        """Recompute every derived field on the report from raw events.

        Called by ``MonitorRuntime.stop()`` as the final assembly step
        before the closing persist, and by report-mutating helpers on
        the facade that need a fresh view (today, none — but the shim
        keeps the call path stable for W11-3+ subscribers).
        """
        self._report.network_events = _annotate_network_events(
            self._report.network_events,
            self._report.activated,
            self._report.scenario_traces,
            self._report.target_extension_id,
        )
        self._report.file_events = _annotate_file_events(
            self._report.file_events,
            self._report.activated,
            self._report.scenario_traces,
            self._report.target_extension_id,
        )
        self._report.process_events = _annotate_process_events(
            self._report.process_events,
            self._report.activated,
            self._report.scenario_traces,
            self._report.target_extension_id,
        )
        derived_verified = set(derive_verified_capabilities(self._report))
        self._report.verified_capabilities = sorted(
            set(self._report.verified_capabilities)
            | (derived_verified & set(self._report.official_attempted_capabilities))
        )
        self._report.heuristic_verified_capabilities = sorted(
            set(self._report.heuristic_verified_capabilities)
            | (derived_verified & set(self._report.heuristic_attempted_capabilities))
        )
        self._report.event_attempts = reconcile_event_attempts(self._report)
        self._report.official_event_coverage = summarize_event_attempts_for_report(
            self._report,
            track="official",
        )
        self._report.heuristic_workflow_coverage = summarize_event_attempts_for_report(
            self._report,
            track="heuristic",
        )
        (
            self._report.coverage_summary,
            self._report.coverage_matrix,
            self._report.coverage_tracks,
        ) = _reconcile_coverage_verification(self._report)
        self._report.signal_summary = _build_signal_summary(self._report)
        self._report.evidence_links = self._report.canonical_evidence_links

    def persist(self, force: bool) -> None:
        """Write the report if forced or if a debounce threshold tripped.

        Throttle (matches the pre-W11-2 lifecycle behavior bit-for-bit):
        skip when none of the following are true — ``force=True``, the
        network-event count is divisible by 5, the file-event count is
        divisible by 5, the scenario-trace count is divisible by 2, or
        the last successful save was more than one second ago.
        """
        if self._report_path is None:
            return

        now = time.time()
        file_count = len(self._report.file_events)
        scenario_count = len(self._report.scenario_traces)
        if (
            not force
            and (len(self._report.network_events) % 5 != 0)
            and (file_count % 5 != 0)
            and (scenario_count % 2 != 0)
            and (now - self._last_persist_at < 1.0)
        ):
            return

        try:
            self._report.save(self._report_path, announce=False)
            self._last_persist_at = now
        except OSError as exc:
            _log(f"Live report persistence failed: {exc}")


__all__ = ["ReportAssembler"]
