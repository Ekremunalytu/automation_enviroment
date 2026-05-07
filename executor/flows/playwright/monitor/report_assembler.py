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

``ExtensionMonitor`` composed this collaborator at construction time
through W11-2..W11-4 and kept thin one-line shims
(``_refresh_derived_report_state`` / ``_persist_report``) so the W11-1
facade pin file (``tests/executor/test_extension_monitor_facade.py``)
held its ``runtime.persist == mon._persist_report`` bound-method
identity invariant. W11-5 (``2026-05-05``) then collapsed that facade
and migrated the fat methods to ``ScenarioAccountant``; the assembler
is now reached directly from ``MonitorRuntime`` while preserving the
behavior the W11-1/W11-2 pin files lock in.

Two acceptance sub-tasks that this collaborator was the natural
landing for — ``runner_exit_code``/``runner_status`` first-class
fields (``[FOLLOWUP runner-status-contract]``) and the
``activation_seen``/``target_log_seen`` intermediate-state emission
(``[FOLLOWUP target-log-lifecycle-instrumentation]``) — landed with
W11-3 (contract bump, ``d4f513f``) and W11-4 (``ScenarioAccountant``
producer side, ``2026-05-05``) respectively.

The assembler holds the ``ActivationReport`` by reference (mirroring
``MonitorRuntime`` from W11-1) and never mutates ``report_path`` after
init; the facade also never mutates its own ``report_path`` post-init,
so the two views cannot drift.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from pathlib import Path

from ..attribution import (
    _annotate_file_events,
    _annotate_network_events,
    _annotate_process_events,
    _build_signal_summary,
)
from ..health import (
    derive_verified_capabilities,
    reconcile_event_attempts,
    summarize_event_attempts_for_report,
)
from ..runtime_capture._shared import _log
from .runtime import _reconcile_coverage_verification
from .types import ActivationReport


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

    def set_runner_status(self, exit_code: int) -> None:
        """Record the entrypoint runner's exit code on the report.

        W11-3: producer side of `[FOLLOWUP runner-status-contract]`. The
        runner calls this from `entrypoint_runner.py` immediately before
        `SystemExit(exit_code)`; the report's `runner_status` enum is
        derived here so the contract stays the single source of truth on
        the (exit_code -> status) mapping (`0 -> success`, `!= 0 -> error`,
        no call -> `unknown` default on the field).
        """
        self._report.runner_exit_code = exit_code
        self._report.runner_status = "success" if exit_code == 0 else "error"

    def set_discovery_strategies(self, strategies: Iterable[str]) -> None:
        """Record which discovery strategies produced activations.

        W11-3: producer side of `activation_discovery_strategies`. The
        runtime collaborator (`MonitorRuntime.stop()`) emits this list
        once per scan; entries are deduped + sorted for deterministic
        diffs across re-runs of the same target.
        """
        self._report.activation_discovery_strategies = sorted(set(strategies))

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
