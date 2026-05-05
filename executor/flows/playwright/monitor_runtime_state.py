"""Runtime state machine for ``ExtensionMonitor`` (W11-1).

Encapsulates the playwright capture lifecycle (start/stop), tracer
attachment, low-level runtime event handlers, and runtime snapshot.
The owning ``ExtensionMonitor`` facade in ``monitor_lifecycle`` composes
this collaborator and forwards public-surface calls; report assembly,
scenario accounting, and persistence stay on the facade until W11-2 /
W11-4 / W11-5 collapse the orchestration further.

Cross-module side effects (recording automation events, persisting the
report, finalizing scenarios on stop, appending activation log entries
between discovery strategies, refreshing derived report state at the
end of stop) are passed in as callbacks at construction time so that
the runtime stays free of accountant / assembler / persistence
responsibilities.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from types import TracebackType
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from .monitor_runtime import (
    _count_target_activations,
    _merge_activation_entries,
    _requires_startup_grace,
)
from .monitor_support import resolve_monitor_api
from .monitor_types import ActivationReport
from .output_signals import (
    annotate_output_signal_events,
    merge_output_signal_events,
    parse_output_signal_events,
    read_output_channel_logs,
)
from .runtime_capture._shared import _log
from .runtime_capture.events import FileEvent, NetworkEvent, ProcessEvent

PersistCallback = Callable[[bool], None]
RecordAutomationEventCallback = Callable[..., None]
NoArgCallback = Callable[[], None]
SetDiscoveryStrategiesCallback = Callable[[list[str]], None]


class MonitorRuntime:
    """Runtime state machine that owns the capture lifecycle.

    Constructed by :class:`ExtensionMonitor`. Holds the captures and the
    log-offset snapshot taken at ``start()``; mutates the shared
    ``ActivationReport`` in place. Cross-module operations
    (``record_automation_event``, ``_persist_report``,
    ``_finalize_running_scenarios``, ``_append_activation_log_entries``,
    ``_refresh_derived_report_state``) are wired in via callbacks so the
    facade keeps ownership of report assembly and accounting.
    """

    def __init__(
        self,
        *,
        page: Page,
        report: ActivationReport,
        persist: PersistCallback,
        record_automation_event: RecordAutomationEventCallback,
        finalize_scenarios: NoArgCallback,
        append_activation_log_entries: NoArgCallback,
        refresh_derived_state: NoArgCallback,
        set_discovery_strategies: SetDiscoveryStrategiesCallback,
        emit_intermediate_state_events: NoArgCallback,
    ) -> None:
        self._page = page
        self._report = report
        self._persist = persist
        self._record_automation = record_automation_event
        self._finalize_scenarios = finalize_scenarios
        self._append_activation_log_entries = append_activation_log_entries
        self._refresh_derived_state = refresh_derived_state
        self._set_discovery_strategies = set_discovery_strategies
        # W11-4: producer signal for
        # ``[FOLLOWUP target-log-lifecycle-instrumentation]``. Fires after
        # ``refresh_derived_state`` so emitted events reflect the
        # post-reconcile verification_status (the intermediate
        # ``activation_seen`` / ``target_log_seen`` literals).
        self._emit_intermediate_state_events = emit_intermediate_state_events
        self._started: bool = False
        self._log_offsets: dict[str, int] = {}
        self._network_capture: Any = None
        self._file_capture: Any = None
        self._extension_file_capture: Any = None

    @property
    def log_offsets(self) -> dict[str, int]:
        """Snapshot of log offsets recorded at ``start()``.

        Read by report-assembly methods that still live on the facade
        (``verify_target_reaction``) until W11-2 collapses them into the
        ``ReportAssembler`` collaborator.
        """
        return self._log_offsets

    @property
    def page(self) -> Page:
        return self._page

    @page.setter
    def page(self, value: Page) -> None:
        self._page = value

    @property
    def started(self) -> bool:
        return self._started

    def start(self) -> None:
        api = resolve_monitor_api()
        self._report.monitoring_start = time.time()
        self._report.monitoring_started_monotonic = api.time.monotonic()
        self._log_offsets = api._snapshot_log_offsets()
        self._report.log_offsets_snapshot = dict(self._log_offsets)
        self._network_capture = api.NetworkCapture(
            monitoring_start=self._report.monitoring_start,
            on_event=self._handle_network_event,
        )
        self._network_capture.start()
        network_capture_error = getattr(
            self._network_capture, "capture_error", ""
        ) or getattr(self._network_capture, "start_error", "")
        if network_capture_error:
            self._report.network_capture_error = network_capture_error
            self._record_automation(
                "network_capture",
                f"Network capture unavailable: {network_capture_error}",
                status="failed",
            )
        self._file_capture = api.FileSystemCapture(
            monitoring_start=self._report.monitoring_start,
            on_event=self._handle_file_event,
        )
        self._file_capture.start()
        if self._file_capture.start_error:
            self._report.file_capture_error = self._file_capture.start_error
        self._started = True
        self._persist(True)
        _log("Monitoring started")

    def attach_runtime_tracers(self) -> None:
        api = resolve_monitor_api()
        if self._extension_file_capture is not None:
            return

        try:
            self._extension_file_capture = api.ExtensionHostFileCapture(
                monitoring_start=self._report.monitoring_start,
                on_event=self._handle_file_event,
                on_process_event=self._handle_process_event,
            )
        except TypeError:
            self._extension_file_capture = api.ExtensionHostFileCapture(
                monitoring_start=self._report.monitoring_start,
                on_event=self._handle_file_event,
            )
        self._extension_file_capture.start()
        self._report.file_capture_diagnostics = dict(
            self._extension_file_capture.diagnostics
        )
        if (
            self._extension_file_capture.start_error
            and not self._report.file_capture_error
        ):
            self._report.file_capture_error = self._extension_file_capture.start_error
        if self._extension_file_capture.start_error:
            self._record_automation(
                "runtime_tracer_attach",
                (
                    "Extension Host file capture unavailable after "
                    f"{self._extension_file_capture.attach_attempts} attempt(s): "
                    f"{self._extension_file_capture.start_error}"
                ),
                status="failed",
            )
        else:
            self._record_automation(
                "runtime_tracer_attach",
                (
                    "Extension Host file capture attached to pid "
                    f"{self._extension_file_capture.pid} after "
                    f"{self._extension_file_capture.attach_attempts} attempt(s)."
                ),
                status="completed",
            )
        self._persist(True)

    def stop(self) -> ActivationReport:
        api = resolve_monitor_api()
        if not self._started:
            _log("Warning: stop() called without start()")
            self._report.monitoring_start = time.time()
            self._report.monitoring_started_monotonic = api.time.monotonic()

        if self._network_capture is not None:
            self._report.network_events = self._network_capture.stop()
            network_capture_error = getattr(
                self._network_capture, "capture_error", ""
            ) or getattr(self._network_capture, "start_error", "")
            if network_capture_error:
                if self._report.network_capture_error != network_capture_error:
                    self._record_automation(
                        "network_capture",
                        f"Network capture collector failed: {network_capture_error}",
                        status="failed",
                    )
                self._report.network_capture_error = network_capture_error
        if self._file_capture is not None:
            self._report.file_events = self._file_capture.stop()
            if self._file_capture.start_error and not self._report.file_capture_error:
                self._report.file_capture_error = self._file_capture.start_error
        if self._extension_file_capture is not None:
            extension_events = self._extension_file_capture.stop()
            if (
                self._extension_file_capture.start_error
                and not self._report.file_capture_error
            ):
                self._report.file_capture_error = (
                    self._extension_file_capture.start_error
                )
            self._report.file_events.extend(extension_events)

        if _requires_startup_grace(self._report):
            _log("Waiting 2.0s for startup-only activation evidence to flush...")
            api.time.sleep(2.0)

        self._report.monitoring_end = time.time()
        self._report.monitoring_ended_monotonic = api.time.monotonic()
        self._finalize_scenarios()
        _log(f"Monitoring stopped ({self._report.duration_s:.1f}s elapsed)")
        self._persist(True)

        # W11-3: track which discovery strategies returned at least one
        # entry. The list is shipped to the report via the assembler
        # callback at the end of stop() so analysts can see which path
        # produced the activation evidence.
        succeeded_strategies: list[str] = []

        try:
            _log("Strategy 1: Parsing Extension Host logs...")
            self._report.activated = api.parse_all_exthost_logs(
                start_offsets=self._log_offsets
            )
            if self._report.activated:
                log_files = api.find_exthost_logs()
                self._report.log_file_path = str(log_files[0]) if log_files else ""
                succeeded_strategies.append("exthost_log_parse")
        except (OSError, ValueError) as exc:
            _log(f"Strategy 1 failed: {exc}")
        self._persist(True)

        try:
            _log("Strategy 2: Scraping Running Extensions UI...")
            self._report.running_extensions = api.get_running_extensions(self._page)
            if self._report.running_extensions:
                succeeded_strategies.append("running_extensions_ui")
        except (PlaywrightError, OSError, ValueError) as exc:
            _log(f"Strategy 2 failed: {exc}")
            try:
                self._page.keyboard.press("Escape")
                self._page.wait_for_timeout(300)
            except PlaywrightError as esc_exc:
                _log(f"Strategy 2 recovery failed: {esc_exc}")
        self._persist(True)

        try:
            _log("Strategy 3: Reading Extension Host output...")
            self._report.extension_host_output = api.read_extension_host_output()
            pre_merge_count = len(self._report.activated)
            self._report.activated = _merge_activation_entries(
                self._report.activated,
                api.parse_activations_from_output(
                    self._report.extension_host_output,
                    monitoring_start=self._report.monitoring_start,
                ),
            )
            if len(self._report.activated) > pre_merge_count:
                succeeded_strategies.append("exthost_output_parse")
        except OSError as exc:
            _log(f"Strategy 3 failed: {exc}")
        self._set_discovery_strategies(succeeded_strategies)
        self._append_activation_log_entries()
        # PR345 PR5 + W8-0 capture-pipeline fix: merge two source streams
        # before attribution. The legacy stream (parse_output_signal_events)
        # consumes ``[extrace-harness]`` markers from the captured exthost
        # output; the W8-0 fix stream (read_output_channel_logs) reads
        # VS Code 1.105+ per-channel persistence files directly because
        # ``console.log`` from extensions no longer reaches exthost.log
        # in 1.105+. ADR 0006 §2-§4 owns the contract.
        self._report.output_signal_events = annotate_output_signal_events(
            merge_output_signal_events(
                parse_output_signal_events(
                    self._report.extension_host_output,
                    monitoring_start=self._report.monitoring_start,
                ),
                read_output_channel_logs(
                    monitoring_start=self._report.monitoring_start,
                ),
            ),
            activations=self._report.activated,
            target_extension_id=self._report.target_extension_id,
            monitoring_start=self._report.monitoring_start,
        )
        self._refresh_derived_state()
        # W11-4: surface intermediate-state promotions
        # (``activation_seen`` / ``target_log_seen``) on the live
        # automation timeline. Runs after ``refresh_derived_state``
        # because the reconciler inside it is what assigns those
        # ``verification_status`` literals; running before would emit
        # nothing. Pinned by
        # ``test_stop_emits_intermediate_state_events_after_refresh``.
        self._emit_intermediate_state_events()
        self._persist(True)

        return self._report

    def __enter__(self) -> MonitorRuntime:
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
        self._report.network_events.append(event)
        self._persist(False)

    def _handle_process_event(self, event: ProcessEvent) -> None:
        self._report.process_events.append(event)
        self._persist(False)

    def _handle_file_event(self, event: FileEvent) -> None:
        self._report.file_events.append(event)
        self._persist(False)

    def capture_runtime_snapshot(self) -> dict[str, int | bool]:
        api = resolve_monitor_api()
        target_activations = _count_target_activations(
            api.parse_all_exthost_logs(start_offsets=self._log_offsets),
            self._report.target_extension_id,
        )
        target_running = any(
            entry.extension_id == self._report.target_extension_id
            for entry in api.get_running_extensions(self._page)
        )
        return {
            "target_activations": target_activations,
            "target_running": target_running,
            "target_file_events": len(self._report.target_file_events),
            "target_network_events": len(self._report.target_network_events),
            "ui_blockers": len(self._report.ui_blocker_entries),
        }


__all__ = ["MonitorRuntime"]
