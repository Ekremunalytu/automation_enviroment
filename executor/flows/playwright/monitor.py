"""Extension Host activation monitoring.

Three complementary strategies to verify extension activations:

1. **VS Code log file parsing** (``--log trace``)
   Most detailed. Parses Extension Host logs for activation entries.
   Works post-hoc after scenarios have run.

2. **Running Extensions UI snapshot** (Playwright)
   Opens "Developer: Show Running Extensions" and scrapes the editor
   content for a list of activated extensions with timing.

3. **Extension Host Output channel** (Playwright)
   Reads the "Log (Extension Host)" output channel for real-time events.

Usage::

    from playwright.sync_api import sync_playwright
    import vscode, automation, monitor

    with sync_playwright() as pw:
        browser, page = vscode.connect(pw)
        vscode.wait_until_ready(page)

        mon = monitor.ExtensionMonitor(page)
        mon.start()

        automation.run_all_scenarios(page)

        report = mon.stop()
        report.save("/results/activation_report.json")
"""

from __future__ import annotations

import re
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any

import commands
import keyboard
from annotation import build_attribution_summary
from capture import summarize_extension_host_logs
from health import (
    build_automation_health,
    build_log_health,
    build_run_quality,
    count_target_activations,
    derive_verified_capabilities,
    is_background_activation,
    reconcile_coverage_verification,
    reconcile_event_attempts,
    summarize_event_attempts_for_report,
)
from report_builder import build_report_data, build_summary, save_report_payload
from signals import build_risk_signals, build_risk_summary, build_verdict

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

VSCODE_USER_DATA = Path("/home/executor/.vscode")
VSCODE_LOGS_DIR = VSCODE_USER_DATA / "logs"
RESULTS_DIR = Path("/results")

_FILE_WATCH_PATHS = [
    Path("/workspace"),
    Path("/home/executor/.ssh"),
    Path("/home/executor/.aws"),
    Path("/home/executor/.kube"),
    Path("/home/executor/.docker"),
    Path("/home/executor/.config/gcloud"),
    Path("/home/executor/credentials"),
    Path("/home/executor/.wallet"),
]
_SENSITIVE_PATH_PREFIXES = (
    "/workspace/.env",
    "/workspace/credentials",
    "/workspace/.wallet",
    "/home/executor/.ssh",
    "/home/executor/.aws",
    "/home/executor/.kube",
    "/home/executor/.docker",
    "/home/executor/.config/gcloud",
    "/home/executor/.npmrc",
    "/home/executor/.git-credentials",
)
_NOISY_PATH_PREFIXES = (
    "/proc/",
    "/dev/",
    "/sys/",
    "/usr/",
    "/etc/",
    "/home/executor/.vscode/logs/",
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ActivationEntry:
    """A single extension activation event parsed from logs."""

    extension_id: str
    activation_event: str = ""
    duration_ms: int | None = None
    timestamp: str = ""
    success: bool = True
    source: str = ""  # "log", "ui", "output"


@dataclass
class RunningExtension:
    """An extension entry scraped from Running Extensions UI."""

    extension_id: str
    name: str = ""
    activation_time_ms: int | None = None
    status: str = "active"


@dataclass
class NetworkEvent:
    """A single observed network event from tshark."""

    timestamp: str = ""
    rel_time_s: float | None = None
    protocol: str = ""
    event_type: str = ""
    source_ip: str = ""
    destination_ip: str = ""
    destination_port: int | None = None
    host: str = ""
    path: str = ""
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    noise_reason: str = ""
    summary: str = ""


@dataclass
class FileEvent:
    """A single observed file-system event."""

    timestamp: str = ""
    rel_time_s: float | None = None
    operation: str = ""
    path: str = ""
    secondary_path: str = ""
    source: str = ""  # "extension", "automation", "system"
    observer: str = ""  # "strace", "inotify"
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


@dataclass
class ScenarioTrace:
    """Lifecycle timing for an executed automation scenario."""

    name: str
    started_at: float
    ended_at: float = 0.0
    status: str = "running"


@dataclass
class StimulusPassTrace:
    """Lifecycle timing for a layered stimulus pass."""

    pass_id: str
    label: str
    order: int
    started_at: float
    ended_at: float = 0.0
    status: str = "running"
    trigger_method: str = ""


@dataclass
class PrerequisiteResult:
    """Materialization state for a prerequisite used by one or more attempts."""

    prerequisite_id: str
    key: str
    label: str
    status: str = "planned"
    materializer: str = ""
    pass_name: str = ""
    attempt_ids: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class EventAttemptRecord:
    """Per-event execution ledger entry."""

    attempt_id: str
    declared_event: str
    activation_event: str
    event_family: str
    event_value: str = ""
    track: str = "official"
    selected_by: str = ""
    selection_reasons: list[str] = field(default_factory=list)
    pass_name: str = ""
    backfill_pass_name: str = ""
    prerequisite_keys: list[str] = field(default_factory=list)
    verification_contract: list[str] = field(default_factory=list)
    trigger_method: str = ""
    fallback_trigger_method: str = ""
    executor_action: str = ""
    backfill_executor_action: str = ""
    legacy_scenarios: list[str] = field(default_factory=list)
    capability_tags: list[str] = field(default_factory=list)
    status: str = "planned"
    trigger_method_used: str = ""
    attempted_passes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    verification_status: str = "not_attempted"
    failure_reason_code: str = ""
    blocked_reason_code: str = ""
    result_details: str = ""
    official: bool = True
    heuristic: bool = False
    ui_path: str = ""
    harness_fallback: str = ""


@dataclass
class EvidenceEvent:
    """Canonical evidence event shared across telemetry sources."""

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
    raw_context: dict[str, str | int | float | bool | None] = field(
        default_factory=dict
    )


@dataclass
class EvidenceLink:
    """Explicit relationship between two evidence events."""

    from_event_id: str
    to_event_id: str
    link_type: str
    confidence: float
    reason: str


@dataclass
class LogStreamEntry:
    """Normalized log line for split-stream report rendering."""

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


@dataclass
class RiskSignal:
    """Normalized risk signal derived from report evidence."""

    signal_id: str
    category: str
    severity: str
    confidence: float
    evidence_event_ids: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class ActivationReport:
    """Aggregated monitoring results."""

    report_version: int = 2
    activated: list[ActivationEntry] = field(default_factory=list)
    running_extensions: list[RunningExtension] = field(default_factory=list)
    network_events: list[NetworkEvent] = field(default_factory=list)
    file_events: list[FileEvent] = field(default_factory=list)
    scenario_traces: list[ScenarioTrace] = field(default_factory=list)
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
    verdict: dict[str, Any] = field(default_factory=dict)
    trigger_plan_requested: bool = False
    trigger_plan_loaded: bool = False
    trigger_plan_applied: bool = False
    trigger_plan_path: str = ""
    requested_scenarios: list[str] = field(default_factory=list)
    failed_scenarios: list[str] = field(default_factory=list)
    extra_trigger_failures: list[str] = field(default_factory=list)
    network_capture_error: str = ""
    file_capture_error: str = ""
    extension_host_output: str = ""
    log_file_path: str = ""
    log_offsets_snapshot: dict[str, int] = field(default_factory=dict, repr=False)
    target_extension_id: str = ""
    monitoring_start: float = 0.0
    monitoring_end: float = 0.0
    scenarios_run: list[str] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return self.monitoring_end - self.monitoring_start

    @property
    def activated_ids(self) -> set[str]:
        return {e.extension_id for e in self.activated}

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
        )

    @property
    def verification_gap(self) -> int:
        attempted = len(set(self.official_attempted_capabilities))
        verified = len(set(self.official_verified_capabilities))
        return max(attempted - verified, 0)

    @property
    def official_attempted_capabilities(self) -> list[str]:
        return sorted(set(self.attempted_capabilities))

    @property
    def official_verified_capabilities(self) -> list[str]:
        return sorted(set(self.verified_capabilities))

    @property
    def heuristic_verification_gap(self) -> int:
        attempted = len(set(self.heuristic_attempted_capabilities))
        verified = len(set(self.heuristic_verified_capabilities))
        return max(attempted - verified, 0)

    @property
    def attribution_summary(self) -> dict[str, Any]:
        return build_attribution_summary(
            self,
            count_target_activations=count_target_activations,
            is_background_activation=is_background_activation,
        )

    @property
    def _log_capture_health(self) -> dict[str, Any]:
        log_paths = find_exthost_logs()
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
        return build_risk_signals(self, RiskSignal)

    @property
    def risk_summary(self) -> dict[str, Any]:
        return build_risk_summary(self.risk_signals)

    @property
    def summary(self) -> dict:
        return build_summary(
            self,
            run_quality=self.run_quality,
            automation_health=self.automation_health,
            log_health=self.log_health,
            attribution_summary=self.attribution_summary,
            risk_summary=self.risk_summary,
        )

    @property
    def network_summary(self) -> dict:
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
    def file_summary(self) -> dict:
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
        events, _ = _build_evidence_bundle(self)
        return events

    @property
    def canonical_evidence_links(self) -> list[EvidenceLink]:
        _, links = _build_evidence_bundle(self)
        return links

    @property
    def log_streams(self) -> dict[str, list[LogStreamEntry]]:
        grouped: dict[str, list[LogStreamEntry]] = {
            "target_extension_host": [],
            "other_extension_host": [],
            "automation": [],
            "ui_blockers": [],
        }
        for entry in sorted(
            self.log_entries,
            key=lambda item: (
                item.rel_time_s is None,
                item.rel_time_s if item.rel_time_s is not None else 0.0,
                item.timestamp,
                item.message,
            ),
        ):
            grouped.setdefault(entry.stream, []).append(entry)
        return grouped

    def save(self, path: str | Path, announce: bool = True) -> Path:
        """Save full report as JSON."""
        evidence_events, evidence_links = _build_evidence_bundle(self)
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


# ---------------------------------------------------------------------------
# Strategy 1: VS Code log file parsing
# ---------------------------------------------------------------------------

# Patterns found in VS Code Extension Host logs (--log trace)
# These cover multiple VS Code versions.
_ACTIVATION_PATTERNS = [
    # "ExtensionService#_doActivateExtension <id>, ..."
    re.compile(
        r"ExtensionService#_doActivateExtension\s+(?P<id>[\w.\-]+)"
        r"(?:.*?activationEvent:\s*'(?P<event>[^']*)')?"
    ),
    # "extension activated <id> in <N>ms"
    re.compile(
        r"extension activated\s+(?P<id>[\w.\-]+)" r"(?:.*?in\s+(?P<ms>\d+)\s*ms)?"
    ),
    # "activating extension '<id>' because of '<event>'"
    re.compile(
        r"activating extension\s+'(?P<id>[^']+)'"
        r"(?:.*?because of\s+'(?P<event>[^']*)')?"
    ),
    # "eager activation <id>"
    re.compile(r"eager\s+activation\s+(?P<id>[\w.\-]+)"),
    # "[info] <id>: extension activated successfully"
    re.compile(r"(?P<id>[\w.\-]+):\s+extension activated" r"(?:.*?(?P<ms>\d+)\s*ms)?"),
    # "ExtHostExtensionService#_doActivateExtension ..."
    re.compile(
        r"ExtHostExtensionService#.*activat\w*\s+(?P<id>[\w.\-]+)"
        r"(?:.*?'(?P<event>[^']*)')?"
    ),
]

# Timestamp pattern at start of VS Code log lines
_TIMESTAMP_RE = re.compile(r"^\[?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\]?")


def find_exthost_logs() -> list[Path]:
    """Find all Extension Host log files under the VS Code logs directory.

    Returns paths sorted newest-first.
    """
    if not VSCODE_LOGS_DIR.exists():
        _log(f"Log directory not found: {VSCODE_LOGS_DIR}")
        return []

    # Extension Host logs can be at various sub-paths depending on VS Code version:
    #   logs/<session>/exthost/exthost.log
    #   logs/<session>/exthost1/exthost.log
    #   logs/<session>/window1/exthost/exthost.log
    patterns = ["**/exthost*/exthost.log", "**/exthost*.log"]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(VSCODE_LOGS_DIR.glob(pattern))

    # Deduplicate and sort by modification time (newest first)
    seen: set[str] = set()
    unique: list[Path] = []
    for p in sorted(found, key=lambda x: x.stat().st_mtime, reverse=True):
        canon = str(p.resolve())
        if canon not in seen:
            seen.add(canon)
            unique.append(p)

    _log(f"Found {len(unique)} Extension Host log file(s)")
    return unique


def parse_activations_from_log(
    log_path: Path,
    start_offset: int = 0,
) -> list[ActivationEntry]:
    """Parse a single Extension Host log file for activation events."""
    if not log_path.exists():
        return []

    raw = log_path.read_bytes()
    if start_offset < 0:
        start_offset = 0
    if start_offset > len(raw):
        start_offset = len(raw)

    content = raw[start_offset:].decode("utf-8", errors="replace")
    entries: list[ActivationEntry] = []
    seen: set[tuple[str, str, str, int | None]] = set()

    for line in content.splitlines():
        # Skip empty or irrelevant lines early
        if "activ" not in line.lower():
            continue

        # Try each pattern
        for pattern in _ACTIVATION_PATTERNS:
            m = pattern.search(line)
            if m:
                ext_id = m.group("id")
                event = m.groupdict().get("event", "") or ""
                ms_str = m.groupdict().get("ms")
                duration_ms = int(ms_str) if ms_str else None

                # Extract timestamp
                ts_match = _TIMESTAMP_RE.match(line)
                timestamp = ts_match.group(1) if ts_match else ""
                dedup_key = (ext_id, event, timestamp, duration_ms)
                if dedup_key in seen:
                    break
                seen.add(dedup_key)

                entries.append(
                    ActivationEntry(
                        extension_id=ext_id,
                        activation_event=event,
                        duration_ms=duration_ms,
                        timestamp=timestamp,
                        source="log",
                    )
                )
                break

    _log(f"Parsed {len(entries)} activation(s) from {log_path.name}")
    return entries


def parse_all_exthost_logs(
    start_offsets: Mapping[str, int] | None = None,
) -> list[ActivationEntry]:
    """Find and parse all Extension Host log files.

    Args:
        start_offsets: Optional map of ``resolved_log_path -> byte_offset``.
            If provided, only content appended after the given offset is parsed.
    """
    all_entries: list[ActivationEntry] = []
    seen_entries: set[tuple[str, str, str, int | None, str]] = set()
    offsets = start_offsets or {}

    for log_path in find_exthost_logs():
        start_offset = offsets.get(str(log_path.resolve()), 0)
        for entry in parse_activations_from_log(log_path, start_offset=start_offset):
            dedup_key = (
                entry.extension_id,
                entry.activation_event,
                entry.timestamp,
                entry.duration_ms,
                entry.source,
            )
            if dedup_key in seen_entries:
                continue
            seen_entries.add(dedup_key)
            all_entries.append(entry)

    return all_entries


# ---------------------------------------------------------------------------
# Strategy 2: Running Extensions UI via Playwright
# ---------------------------------------------------------------------------


def get_running_extensions(page: Page) -> list[RunningExtension]:
    """Open 'Developer: Show Running Extensions' and scrape extension list.

    This command opens a special editor tab showing all active extensions
    with their activation time.
    """
    extensions: list[RunningExtension] = []
    try:
        _log("Opening Running Extensions view...")
        commands.run_command(page, "Developer: Show Running Extensions")
        page.wait_for_timeout(3000)  # wait for extensions list to populate

        # The Running Extensions editor uses VS Code's list/tree widget.
        rows = page.query_selector_all(".runtime-extensions-editor .monaco-list-row")

        if rows:
            for row in rows:
                text = row.inner_text()
                # aria-label contains the extension short name (e.g. "typescript-language-features")
                aria = row.get_attribute("aria-label") or ""
                ext = _parse_running_extension_row(text, aria)
                if ext:
                    extensions.append(ext)
            _log(f"Found {len(extensions)} running extension(s) via UI")
        else:
            _log("List rows not found in Running Extensions view")

    except PlaywrightError as exc:
        _log(f"Running Extensions scraping failed: {exc}")
    finally:
        # Close the Running Extensions tab if it was opened.
        try:
            page.keyboard.press(keyboard.CLOSE_EDITOR)
            page.wait_for_timeout(300)
        except PlaywrightError as exc:
            _log(f"Failed to close Running Extensions tab: {exc}")

    return extensions


def _parse_running_extension_row(
    text: str, aria_label: str = ""
) -> RunningExtension | None:
    """Parse a single row from Running Extensions list.

    VS Code renders each row as::

        Display Name
        version
        [Startup] Activation: Xms

    The ``aria-label`` attribute contains the extension short name
    (e.g. "typescript-language-features") which we prefix with "vscode."
    for built-in extensions.
    """
    if not text or not text.strip():
        return None

    lines = [
        line_text.strip()
        for line_text in text.strip().splitlines()
        if line_text.strip()
    ]
    if not lines:
        return None

    name = lines[0]
    timing = None

    # Extract activation time from "Activation: 153ms" or "Startup Activation: 39ms"
    for line in lines:
        time_match = re.search(r"(\d+)\s*ms", line)
        if time_match:
            timing = int(time_match.group(1))
            break

    # Build extension ID from aria-label
    # For built-in extensions, aria-label is the short name (e.g. "git", "emmet")
    # For marketplace extensions, it's typically "publisher.name"
    ext_id = aria_label
    if ext_id and "." not in ext_id:
        # Built-in extension: prefix with "vscode."
        ext_id = f"vscode.{ext_id}"

    if not ext_id:
        ext_id = name  # fallback to display name

    return RunningExtension(
        extension_id=ext_id,
        name=name,
        activation_time_ms=timing,
    )


# ---------------------------------------------------------------------------
# Strategy 3: Extension Host Output channel
# ---------------------------------------------------------------------------


def read_extension_host_output(page: Page | None = None) -> str:
    """Read Extension Host output from the log file directly.

    This is more reliable than trying to scrape the Output panel via
    Playwright, since the Output channel picker can behave unpredictably.

    Falls back to reading the exthost.log file which contains the same data.
    """
    _ = page
    _log("Reading Extension Host output from log file...")

    # Read directly from the Extension Host log file (most reliable)
    logs = find_exthost_logs()
    if logs:
        try:
            content = logs[0].read_text(errors="replace")
            _log(f"Read {len(content)} chars from {logs[0].name}")
            return content
        except OSError as exc:
            _log(f"Failed to read log file: {exc}")

    # Fallback: try all per-extension log files
    if VSCODE_LOGS_DIR.exists():
        parts: list[str] = []
        for log_file in sorted(VSCODE_LOGS_DIR.rglob("*.log")):
            if "exthost" in str(log_file):
                try:
                    parts.append(
                        f"--- {log_file.name} ---\n{log_file.read_text(errors='replace')}"
                    )
                except OSError:
                    continue
        if parts:
            content = "\n".join(parts)
            _log(f"Read {len(content)} chars from {len(parts)} exthost log file(s)")
            return content

    _log("No Extension Host log files found")
    return ""


# ---------------------------------------------------------------------------
# Strategy 4: Network monitoring (real-time via tshark)
# ---------------------------------------------------------------------------

_NETWORK_CAPTURE_FILTER = (
    "dns or http.request or tls.handshake.type == 1 or "
    "(tcp.flags.syn == 1 and tcp.flags.ack == 0)"
)


def parse_tshark_event_line(
    line: str,
    monitoring_start: float = 0.0,
) -> NetworkEvent | None:
    """Parse a single tshark TSV line into a structured network event."""
    if not line.strip():
        return None

    parts = line.rstrip("\n").split("\t")
    if len(parts) < 13:
        parts.extend([""] * (13 - len(parts)))

    timestamp_raw = parts[0].strip()
    try:
        timestamp_epoch = float(timestamp_raw)
    except ValueError:
        return None

    source_ip = _first_non_empty(parts[1], parts[2])
    destination_ip = _first_non_empty(parts[3], parts[4])
    destination_port_raw = _first_non_empty(parts[5], parts[6])
    dns_query = parts[7].strip()
    http_host = parts[8].strip()
    http_uri = parts[9].strip()
    tls_sni = parts[10].strip()
    protocol = parts[11].strip().lower()
    info = parts[12].strip()

    destination_port = None
    if destination_port_raw:
        try:
            destination_port = int(destination_port_raw)
        except ValueError:
            destination_port = None

    host = _first_non_empty(http_host, tls_sni, dns_query)
    if http_host and http_uri:
        event_type = "http_request"
    elif dns_query:
        event_type = "dns_query"
    elif tls_sni:
        event_type = "tls_client_hello"
    else:
        event_type = "tcp_connect"

    timestamp = datetime.fromtimestamp(timestamp_epoch).isoformat(
        timespec="milliseconds"
    )
    rel_time_s = None
    if monitoring_start > 0:
        rel_time_s = round(max(timestamp_epoch - monitoring_start, 0.0), 3)

    summary = info or " ".join(
        part for part in [event_type, host or destination_ip, http_uri] if part
    )

    if not any([source_ip, destination_ip, host, summary]):
        return None

    return NetworkEvent(
        timestamp=timestamp,
        rel_time_s=rel_time_s,
        protocol=protocol or event_type.replace("_", ""),
        event_type=event_type,
        source_ip=source_ip,
        destination_ip=destination_ip,
        destination_port=destination_port,
        host=host,
        path=http_uri,
        summary=summary,
    )


class NetworkCapture:
    """Capture network events from inside the executor container using tshark."""

    def __init__(
        self,
        monitoring_start: float,
        on_event: Callable[[NetworkEvent], None] | None = None,
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events: list[NetworkEvent] = []
        self.start_error = ""
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None

    def start(self) -> None:
        """Start background tshark capture."""
        cmd = [
            "tshark",
            "-l",
            "-n",
            "-Q",
            "-i",
            "any",
            "-T",
            "fields",
            "-E",
            "separator=\t",
            "-E",
            "occurrence=f",
            "-e",
            "frame.time_epoch",
            "-e",
            "ip.src",
            "-e",
            "ipv6.src",
            "-e",
            "ip.dst",
            "-e",
            "ipv6.dst",
            "-e",
            "tcp.dstport",
            "-e",
            "udp.dstport",
            "-e",
            "dns.qry.name",
            "-e",
            "http.host",
            "-e",
            "http.request.uri",
            "-e",
            "tls.handshake.extensions_server_name",
            "-e",
            "_ws.col.Protocol",
            "-e",
            "_ws.col.Info",
            "-Y",
            _NETWORK_CAPTURE_FILTER,
        ]
        try:
            self._proc = subprocess.Popen(  # nosec B603,B607
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self.start_error = "tshark binary not available in executor container."
            _log(self.start_error)
            return
        except OSError as exc:
            self.start_error = f"tshark start failed: {exc}"
            _log(self.start_error)
            return

        self._reader = threading.Thread(target=self._consume_stdout, daemon=True)
        self._reader.start()
        _log("Network capture started")

    def stop(self) -> list[NetworkEvent]:
        """Stop capture and return all collected events."""
        if self._proc is None:
            return list(self.events)

        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=3)

        if self._reader is not None:
            self._reader.join(timeout=3)

        _log(f"Network capture stopped with {len(self.events)} event(s)")
        return list(self.events)

    def _consume_stdout(self) -> None:
        if self._proc is None or self._proc.stdout is None:
            return

        for line in self._proc.stdout:
            event = parse_tshark_event_line(line, self.monitoring_start)
            if event is None:
                continue
            self.events.append(event)
            if self.on_event is not None:
                self.on_event(event)


# ---------------------------------------------------------------------------
# Strategy 5: File I/O monitoring
# ---------------------------------------------------------------------------

_STRACE_CALL_RE = re.compile(
    r"^(?:\[pid\s+(?P<pid>\d+)\]\s+)?(?P<ts>\d+\.\d+)\s+"
    r"(?P<call>\w+)\((?P<args>.*)\)\s+=\s+(?P<result>.+)$"
)


def parse_strace_file_event_line(
    line: str,
    monitoring_start: float = 0.0,
) -> FileEvent | None:
    """Parse a single strace line from the Extension Host process."""
    match = _STRACE_CALL_RE.match(line.strip())
    if match is None:
        return None

    try:
        timestamp_epoch = float(match.group("ts"))
    except ValueError:
        return None

    call = match.group("call")
    args = match.group("args")
    quoted_paths = re.findall(r'"([^"]+)"', args)
    if not quoted_paths:
        return None

    primary_path = quoted_paths[0]
    secondary_path = quoted_paths[1] if len(quoted_paths) > 1 else ""
    if not _is_relevant_file_path(primary_path):
        return None

    operation = _normalize_strace_operation(call, args)
    if not operation:
        return None

    rel_time_s = None
    if monitoring_start > 0:
        rel_time_s = round(max(timestamp_epoch - monitoring_start, 0.0), 3)

    timestamp = datetime.fromtimestamp(timestamp_epoch).isoformat(
        timespec="milliseconds"
    )
    summary = operation
    if secondary_path:
        summary = f"{operation}: {primary_path} -> {secondary_path}"
    else:
        summary = f"{operation}: {primary_path}"

    return FileEvent(
        timestamp=timestamp,
        rel_time_s=rel_time_s,
        operation=operation,
        path=primary_path,
        secondary_path=secondary_path,
        source="extension",
        observer="strace",
        flags=args,
        sensitive=_is_sensitive_path(primary_path),
        summary=summary,
    )


def parse_inotify_file_event_line(
    line: str,
    monitoring_start: float = 0.0,
    event_time: float | None = None,
) -> FileEvent | None:
    """Parse a single inotifywait output line."""
    stripped = line.strip()
    if not stripped:
        return None

    parts = stripped.split("\t")
    if len(parts) < 2:
        return None

    path = parts[0].strip()
    raw_events = parts[1].strip()
    if not _is_relevant_file_path(path):
        return None

    operation = _normalize_inotify_operation(raw_events)
    if not operation:
        return None

    observed_at = event_time if event_time is not None else time.time()
    rel_time_s = None
    if monitoring_start > 0:
        rel_time_s = round(max(observed_at - monitoring_start, 0.0), 3)

    timestamp = datetime.fromtimestamp(observed_at).isoformat(timespec="milliseconds")
    return FileEvent(
        timestamp=timestamp,
        rel_time_s=rel_time_s,
        operation=operation,
        path=path,
        source="automation",
        observer="inotify",
        sensitive=_is_sensitive_path(path),
        summary=f"{operation}: {path}",
    )


class FileSystemCapture:
    """Watch selected filesystem roots via inotifywait."""

    def __init__(
        self,
        monitoring_start: float,
        on_event: Callable[[FileEvent], None] | None = None,
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events: list[FileEvent] = []
        self.start_error = ""
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None

    def start(self) -> None:
        watch_paths = [str(path) for path in _FILE_WATCH_PATHS if path.exists()]
        if not watch_paths:
            self.start_error = (
                "No filesystem watch paths available in executor container."
            )
            _log(self.start_error)
            return

        cmd = [
            "inotifywait",
            "-m",
            "-r",
            "--format",
            "%w%f\t%e",
            "-e",
            "create",
            "-e",
            "modify",
            "-e",
            "delete",
            "-e",
            "move",
            "-e",
            "attrib",
            "-e",
            "open",
            "-e",
            "close_write",
            *watch_paths,
        ]
        try:
            self._proc = subprocess.Popen(  # nosec B603,B607
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self.start_error = "inotifywait binary not available in executor container."
            _log(self.start_error)
            return
        except OSError as exc:
            self.start_error = f"inotifywait start failed: {exc}"
            _log(self.start_error)
            return

        self._reader = threading.Thread(target=self._consume_stdout, daemon=True)
        self._reader.start()
        _log("Filesystem capture started")

    def stop(self) -> list[FileEvent]:
        if self._proc is None:
            return list(self.events)

        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=3)

        if self._reader is not None:
            self._reader.join(timeout=3)

        _log(f"Filesystem capture stopped with {len(self.events)} event(s)")
        return list(self.events)

    def _consume_stdout(self) -> None:
        if self._proc is None or self._proc.stdout is None:
            return

        for line in self._proc.stdout:
            event = parse_inotify_file_event_line(
                line,
                monitoring_start=self.monitoring_start,
                event_time=time.time(),
            )
            if event is None:
                continue
            self.events.append(event)
            if self.on_event is not None:
                self.on_event(event)


class ExtensionHostFileCapture:
    """Attach strace to the current Extension Host process."""

    def __init__(
        self,
        monitoring_start: float,
        on_event: Callable[[FileEvent], None] | None = None,
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events: list[FileEvent] = []
        self.start_error = ""
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._pid: int | None = None

    def start(self) -> None:
        pid = _find_extension_host_pid()
        if pid is None:
            self.start_error = (
                "Extension Host PID not found; file attribution unavailable."
            )
            _log(self.start_error)
            return

        self._pid = pid
        cmd = [
            "strace",
            "-f",
            "-ttt",
            "-s",
            "256",
            "-e",
            (
                "trace=open,openat,creat,unlink,unlinkat,rename,renameat,"
                "renameat2,mkdir,rmdir,newfstatat,readlink"
            ),
            "-p",
            str(pid),
        ]
        try:
            self._proc = subprocess.Popen(  # nosec B603,B607
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self.start_error = "strace binary not available in executor container."
            _log(self.start_error)
            return
        except OSError as exc:
            self.start_error = f"strace start failed: {exc}"
            _log(self.start_error)
            return

        self._reader = threading.Thread(target=self._consume_stderr, daemon=True)
        self._reader.start()
        _log(f"Extension Host file capture attached to pid {pid}")

    def stop(self) -> list[FileEvent]:
        if self._proc is None:
            return list(self.events)

        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=3)

        if self._reader is not None:
            self._reader.join(timeout=3)

        _log(f"Extension Host file capture stopped with {len(self.events)} event(s)")
        return list(self.events)

    def _consume_stderr(self) -> None:
        if self._proc is None or self._proc.stderr is None:
            return

        for line in self._proc.stderr:
            event = parse_strace_file_event_line(
                line,
                monitoring_start=self.monitoring_start,
            )
            if event is None:
                continue
            self.events.append(event)
            if self.on_event is not None:
                self.on_event(event)


# ---------------------------------------------------------------------------
# Strategy 6: Log file watching (real-time via inotifywait)
# ---------------------------------------------------------------------------


def watch_exthost_log(
    callback: Callable[[ActivationEntry], None],
    timeout_s: int = 60,
) -> None:
    """Watch the Extension Host log file for new activation events.

    Uses inotifywait for efficient file monitoring. Calls ``callback(entry)``
    for each new ActivationEntry detected.

    Args:
        callback: Function called with each new ActivationEntry.
        timeout_s: Max time to watch in seconds.
    """
    logs = find_exthost_logs()
    if not logs:
        _log("No Extension Host log found to watch")
        return

    log_path = logs[0]
    _log(f"Watching {log_path} for {timeout_s}s...")

    # Read initial content to track what's new
    initial_size = log_path.stat().st_size

    proc: subprocess.Popen[str] | None = None

    try:
        proc = subprocess.Popen(  # nosec B603,B607
            ["inotifywait", "-m", "-e", "modify", str(log_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        start = time.time()
        seen_ids: set[str] = set()

        while time.time() - start < timeout_s:
            # Read new content appended to the log
            current_size = log_path.stat().st_size
            if current_size > initial_size:
                with open(log_path, encoding="utf-8", errors="replace") as f:
                    f.seek(initial_size)
                    new_content = f.read()
                initial_size = current_size

                for line in new_content.splitlines():
                    if "activ" not in line.lower():
                        continue
                    for pattern in _ACTIVATION_PATTERNS:
                        m = pattern.search(line)
                        if m and m.group("id") not in seen_ids:
                            seen_ids.add(m.group("id"))
                            entry = ActivationEntry(
                                extension_id=m.group("id"),
                                activation_event=m.groupdict().get("event", "") or "",
                                source="watch",
                            )
                            callback(entry)
                            break

            time.sleep(0.5)

    except FileNotFoundError:
        _log("inotifywait not available, falling back to polling")
        _poll_exthost_log(log_path, initial_size, callback, timeout_s)
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()


def _poll_exthost_log(
    log_path: Path,
    initial_size: int,
    callback: Callable[[ActivationEntry], None],
    timeout_s: int,
) -> None:
    """Fallback polling-based log watcher when inotifywait is unavailable."""
    start = time.time()
    seen_ids: set[str] = set()

    while time.time() - start < timeout_s:
        current_size = log_path.stat().st_size
        if current_size > initial_size:
            with open(log_path, encoding="utf-8", errors="replace") as f:
                f.seek(initial_size)
                new_content = f.read()
            initial_size = current_size

            for line in new_content.splitlines():
                if "activ" not in line.lower():
                    continue
                for pattern in _ACTIVATION_PATTERNS:
                    m = pattern.search(line)
                    if m and m.group("id") not in seen_ids:
                        seen_ids.add(m.group("id"))
                        entry = ActivationEntry(
                            extension_id=m.group("id"),
                            activation_event=m.groupdict().get("event", "") or "",
                            source="poll",
                        )
                        callback(entry)
                        break

        time.sleep(1)


# ---------------------------------------------------------------------------
# Unified monitor
# ---------------------------------------------------------------------------


class ExtensionMonitor:
    """Context manager that captures extension activations around scenario execution.

    Usage::

        mon = ExtensionMonitor(page)
        mon.start()
        # ... run automation scenarios ...
        report = mon.stop()
        report.print_summary()
        report.save("/results/report.json")

    Or as a context manager::

        with ExtensionMonitor(page) as mon:
            automation.run_all_scenarios(page)
        mon.report.print_summary()
    """

    def __init__(
        self,
        page: Page,
        report_path: str | Path | None = None,
        target_extension_id: str = "",
    ) -> None:
        self.page = page
        self.report_path = Path(report_path) if report_path is not None else None
        self.report = ActivationReport(target_extension_id=target_extension_id)
        self._started = False
        self._log_offsets: dict[str, int] = {}
        self._network_capture: NetworkCapture | None = None
        self._file_capture: FileSystemCapture | None = None
        self._extension_file_capture: ExtensionHostFileCapture | None = None
        self._active_scenarios: dict[str, ScenarioTrace] = {}
        self._last_persist_at = 0.0

    def apply_trigger_payload(self, payload: Any) -> None:
        """Attach trigger-selection metadata to the in-progress report."""
        self.report.trigger_plan_requested = True
        self.report.trigger_plan_loaded = True
        self.report.coverage_tracks = dict(getattr(payload, "coverage_tracks", {}))
        self.report.coverage_summary = dict(getattr(payload, "coverage_summary", {}))
        self.report.coverage_matrix = list(getattr(payload, "coverage_matrix", []))
        self.report.official_event_coverage = dict(
            getattr(payload, "official_event_coverage", {})
        )
        self.report.heuristic_workflow_coverage = dict(
            getattr(payload, "heuristic_workflow_coverage", {})
        )
        self.report.attempted_capabilities = _extract_official_attempted_capabilities(
            payload
        )
        self.report.heuristic_attempted_capabilities = (
            _extract_heuristic_attempted_capabilities(payload)
        )
        self.report.stimulus_passes = [
            StimulusPassTrace(
                pass_id=str(item.get("pass_id", "")),
                label=str(item.get("label", "")),
                order=int(item.get("order", 0) or 0),
                started_at=0.0,
                status=str(item.get("status", "planned")),
                trigger_method=str(item.get("trigger_method", "")),
            )
            for item in getattr(payload, "stimulus_passes", []) or []
            if isinstance(item, Mapping)
        ]
        self.report.prerequisite_results = [
            PrerequisiteResult(
                prerequisite_id=str(item.get("prerequisite_id", "")),
                key=str(item.get("key", "")),
                label=str(item.get("label", "")),
                status=str(item.get("status", "planned")),
                materializer=str(item.get("materializer", "")),
                pass_name=str(item.get("pass_name", "")),
                attempt_ids=[
                    str(attempt_id)
                    for attempt_id in item.get("attempt_ids", [])
                    if str(attempt_id).strip()
                ],
                detail=str(item.get("detail", "")),
            )
            for item in getattr(payload, "prerequisite_results", []) or []
            if isinstance(item, Mapping)
        ]
        self.report.event_attempts = [
            EventAttemptRecord(
                attempt_id=str(item.get("attempt_id", "")),
                declared_event=str(item.get("declared_event", "")),
                activation_event=str(item.get("activation_event", "")),
                event_family=str(item.get("event_family", "")),
                event_value=str(item.get("event_value", "")),
                track=str(item.get("track", "official")),
                selected_by=str(item.get("selected_by", "")),
                selection_reasons=[
                    str(reason)
                    for reason in item.get("selection_reasons", [])
                    if str(reason).strip()
                ],
                pass_name=str(item.get("pass_name", "")),
                backfill_pass_name=str(item.get("backfill_pass_name", "")),
                prerequisite_keys=[
                    str(key)
                    for key in item.get("prerequisite_keys", [])
                    if str(key).strip()
                ],
                verification_contract=[
                    str(contract)
                    for contract in item.get("verification_contract", [])
                    if str(contract).strip()
                ],
                trigger_method=str(item.get("trigger_method", "")),
                fallback_trigger_method=str(item.get("fallback_trigger_method", "")),
                executor_action=str(item.get("executor_action", "")),
                backfill_executor_action=str(item.get("backfill_executor_action", "")),
                legacy_scenarios=[
                    str(name)
                    for name in item.get("legacy_scenarios", [])
                    if str(name).strip()
                ],
                capability_tags=[
                    str(tag)
                    for tag in item.get("capability_tags", [])
                    if str(tag).strip()
                ],
                status=str(item.get("status", "planned")),
                trigger_method_used=str(item.get("trigger_method_used", "")),
                attempted_passes=[
                    str(pass_name)
                    for pass_name in item.get("attempted_passes", [])
                    if str(pass_name).strip()
                ],
                evidence=[
                    str(evidence)
                    for evidence in item.get("evidence", [])
                    if str(evidence).strip()
                ],
                verification_status=str(
                    item.get("verification_status", "not_attempted")
                ),
                failure_reason_code=str(item.get("failure_reason_code", "")),
                blocked_reason_code=str(item.get("blocked_reason_code", "")),
                result_details=str(item.get("result_details", "")),
                official=bool(item.get("official", True)),
                heuristic=bool(item.get("heuristic", False)),
                ui_path=str(item.get("ui_path", "")),
                harness_fallback=str(item.get("harness_fallback", "")),
            )
            for item in getattr(payload, "event_attempts", []) or []
            if isinstance(item, Mapping)
        ]
        self.report.requested_scenarios = list(
            getattr(payload, "selected_scenarios", []) or []
        )
        payload_target = getattr(payload, "target_extension_id", None)
        if payload_target and not self.report.target_extension_id:
            self.report.target_extension_id = payload_target
        self._persist_report(force=True)

    def start(self) -> None:
        """Record the monitoring start time."""
        self.report.monitoring_start = time.time()
        self._log_offsets = _snapshot_log_offsets()
        self.report.log_offsets_snapshot = dict(self._log_offsets)
        self._network_capture = NetworkCapture(
            monitoring_start=self.report.monitoring_start,
            on_event=self._handle_network_event,
        )
        self._network_capture.start()
        if self._network_capture.start_error:
            self.report.network_capture_error = self._network_capture.start_error
        self._file_capture = FileSystemCapture(
            monitoring_start=self.report.monitoring_start,
            on_event=self._handle_file_event,
        )
        self._file_capture.start()
        if self._file_capture.start_error:
            self.report.file_capture_error = self._file_capture.start_error
        self._started = True
        self._persist_report(force=True)
        _log("Monitoring started")

    def attach_runtime_tracers(self) -> None:
        """Attach runtime tracers that depend on a stable Extension Host PID."""
        if self._extension_file_capture is not None:
            return

        self._extension_file_capture = ExtensionHostFileCapture(
            monitoring_start=self.report.monitoring_start,
            on_event=self._handle_file_event,
        )
        self._extension_file_capture.start()
        if (
            self._extension_file_capture.start_error
            and not self.report.file_capture_error
        ):
            self.report.file_capture_error = self._extension_file_capture.start_error
        self._persist_report(force=True)

    def stop(self) -> ActivationReport:
        """Collect all monitoring data and build the report.

        Executes all three strategies: log parsing, UI snapshot, output reading.
        Each strategy is wrapped in error handling so a failure in one
        doesn't prevent the others from running.
        """
        if not self._started:
            _log("Warning: stop() called without start()")
            self.report.monitoring_start = time.time()

        if self._network_capture is not None:
            self.report.network_events = self._network_capture.stop()
            if self._network_capture.start_error:
                self.report.network_capture_error = self._network_capture.start_error
        if self._file_capture is not None:
            self.report.file_events = self._file_capture.stop()
            if self._file_capture.start_error and not self.report.file_capture_error:
                self.report.file_capture_error = self._file_capture.start_error
        if self._extension_file_capture is not None:
            extension_events = self._extension_file_capture.stop()
            if (
                self._extension_file_capture.start_error
                and not self.report.file_capture_error
            ):
                self.report.file_capture_error = (
                    self._extension_file_capture.start_error
                )
            self.report.file_events.extend(extension_events)

        self.report.monitoring_end = time.time()
        self._finalize_running_scenarios()
        _log(f"Monitoring stopped ({self.report.duration_s:.1f}s elapsed)")
        self._persist_report(force=True)

        # Strategy 1: Parse Extension Host log files
        try:
            _log("Strategy 1: Parsing Extension Host logs...")
            self.report.activated = parse_all_exthost_logs(
                start_offsets=self._log_offsets
            )
            if self.report.activated:
                log_files = find_exthost_logs()
                self.report.log_file_path = str(log_files[0]) if log_files else ""
        except (OSError, ValueError) as exc:
            _log(f"Strategy 1 failed: {exc}")
        self._persist_report(force=True)

        # Strategy 2: Running Extensions UI snapshot
        try:
            _log("Strategy 2: Scraping Running Extensions UI...")
            self.report.running_extensions = get_running_extensions(self.page)
        except (PlaywrightError, OSError, ValueError) as exc:
            _log(f"Strategy 2 failed: {exc}")
            # Dismiss any stuck dialogs (may also fail if VS Code crashed)
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
            except PlaywrightError as esc_exc:
                _log(f"Strategy 2 recovery failed: {esc_exc}")
        self._persist_report(force=True)

        # Strategy 3: Extension Host output from log files
        try:
            _log("Strategy 3: Reading Extension Host output...")
            self.report.extension_host_output = read_extension_host_output()
        except OSError as exc:
            _log(f"Strategy 3 failed: {exc}")
        self._append_activation_log_entries()
        self.report.network_events = _annotate_network_events(
            self.report.network_events,
            self.report.activated,
            self.report.scenario_traces,
            self.report.target_extension_id,
        )
        self.report.file_events = _annotate_file_events(
            self.report.file_events,
            self.report.activated,
            self.report.scenario_traces,
            self.report.target_extension_id,
        )
        derived_verified = set(derive_verified_capabilities(self.report))
        self.report.verified_capabilities = sorted(
            set(self.report.verified_capabilities)
            | (derived_verified & set(self.report.official_attempted_capabilities))
        )
        self.report.heuristic_verified_capabilities = sorted(
            set(self.report.heuristic_verified_capabilities)
            | (derived_verified & set(self.report.heuristic_attempted_capabilities))
        )
        self.report.event_attempts = reconcile_event_attempts(self.report)
        self.report.official_event_coverage = summarize_event_attempts_for_report(
            self.report,
            track="official",
        )
        self.report.heuristic_workflow_coverage = summarize_event_attempts_for_report(
            self.report,
            track="heuristic",
        )
        (
            self.report.coverage_summary,
            self.report.coverage_matrix,
            self.report.coverage_tracks,
        ) = reconcile_coverage_verification(self.report)
        self.report.verdict = build_verdict(
            self.report,
            automation_health=self.report.automation_health,
            run_quality=build_run_quality(
                self.report,
                self.report.automation_health,
            ),
        )
        self.report.evidence_links = self.report.canonical_evidence_links
        self._persist_report(force=True)

        return self.report

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
        self.report.network_events.append(event)
        self._persist_report(force=False)

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
        self._persist_report(force=False)

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
        self.record_automation_event(
            "prerequisite",
            f"Prerequisite {existing.label or existing.key} {status}",
            status=status,
        )

    def record_event_attempt_start(
        self, attempt_id: str, *, pass_name: str = ""
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
            "attempted_only"
            if status in {"attempted_only", "verified"}
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

    def _handle_file_event(self, event: FileEvent) -> None:
        self.report.file_events.append(event)
        self._persist_report(force=False)

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
            finished_trace: ScenarioTrace | None = (
                self._active_scenarios.pop(name)
                if name in self._active_scenarios
                else None
            )
            if finished_trace is None:
                finished_trace = ScenarioTrace(name=name, started_at=now)
                self.report.scenario_traces.append(finished_trace)
            finished_trace.ended_at = now
            finished_trace.status = status or "completed"
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
        self._persist_report(force=False)

    def capture_runtime_snapshot(self) -> dict[str, int | bool]:
        target_activations = _count_target_activations(
            parse_all_exthost_logs(start_offsets=self._log_offsets),
            self.report.target_extension_id,
        )
        target_running = any(
            entry.extension_id == self.report.target_extension_id
            for entry in get_running_extensions(self.page)
        )
        return {
            "target_activations": target_activations,
            "target_running": target_running,
            "target_file_events": len(self.report.target_file_events),
            "target_network_events": len(self.report.target_network_events),
            "ui_blockers": len(self.report.ui_blocker_entries),
        }

    def verify_target_reaction(
        self,
        baseline: dict[str, int | bool],
        *,
        capability: str,
        trigger_label: str,
        activation_event: str = "",
        success_signal: bool = False,
    ) -> bool:
        current_target_activations = _count_target_activations(
            parse_all_exthost_logs(start_offsets=self._log_offsets),
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

    def _persist_report(self, force: bool) -> None:
        if self.report_path is None:
            return

        now = time.time()
        file_count = len(self.report.file_events)
        scenario_count = len(self.report.scenario_traces)
        if (
            not force
            and (len(self.report.network_events) % 5 != 0)
            and (file_count % 5 != 0)
            and (scenario_count % 2 != 0)
            and (now - self._last_persist_at < 1.0)
        ):
            return

        try:
            self.report.save(self.report_path, announce=False)
            self._last_persist_at = now
        except OSError as exc:
            _log(f"Live report persistence failed: {exc}")


# ---------------------------------------------------------------------------
# Convenience: quick activation check
# ---------------------------------------------------------------------------


def check_extension_activated(extension_id: str, page: Page | None = None) -> bool:
    """Quick check: is a specific extension activated?

    Checks log files first (fast), then UI if page is provided.
    """
    # Check logs
    for entry in parse_all_exthost_logs():
        if entry.extension_id == extension_id:
            return True

    # Check UI if page available
    if page is not None:
        for ext in get_running_extensions(page):
            if ext.extension_id == extension_id:
                return True

    return False


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _log(msg: str) -> None:
    print(f"[monitor] {msg}")


def _first_non_empty(*values: str) -> str:
    for value in values:
        item = value.strip()
        if item:
            return item
    return ""


def _is_sensitive_path(path: str) -> bool:
    normalized = path.strip()
    return any(normalized.startswith(prefix) for prefix in _SENSITIVE_PATH_PREFIXES)


def _is_relevant_file_path(path: str) -> bool:
    normalized = path.strip()
    if not normalized or normalized in {".", ".."}:
        return False
    if any(normalized.startswith(prefix) for prefix in _NOISY_PATH_PREFIXES):
        return False
    return normalized.startswith("/workspace") or normalized.startswith(
        "/home/executor"
    )


def _normalize_inotify_operation(raw_events: str) -> str:
    events = raw_events.upper()
    if "CREATE" in events:
        return "create"
    if "CLOSE_WRITE" in events or "MODIFY" in events:
        return "write"
    if "DELETE" in events:
        return "delete"
    if "MOVE" in events:
        return "move"
    if "ATTRIB" in events:
        return "metadata"
    if "OPEN" in events:
        return "read"
    return ""


def _normalize_strace_operation(call: str, args: str) -> str:
    if call in {"unlink", "unlinkat", "rmdir"}:
        return "delete"
    if call in {"rename", "renameat", "renameat2"}:
        return "move"
    if call == "mkdir":
        return "create"
    if call in {"readlink", "newfstatat"}:
        return "metadata"
    if call in {"creat", "open", "openat"}:
        if any(flag in args for flag in ["O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC"]):
            return "write"
        return "read"
    return ""


def _find_extension_host_pid() -> int | None:
    try:
        result = subprocess.run(  # nosec B603
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        _log(f"Failed to inspect process table: {exc}")
        return None

    candidates: list[int] = []
    for line in result.stdout.splitlines():
        if "extensionHost" not in line:
            continue
        parts = line.strip().split(maxsplit=1)
        if not parts:
            continue
        try:
            candidates.append(int(parts[0]))
        except ValueError:
            continue

    return max(candidates) if candidates else None


def _parse_iso_timestamp(timestamp: str) -> float | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp).timestamp()
    except ValueError:
        pass
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").timestamp()
    except ValueError:
        return None


def _format_epoch_timestamp(epoch: float | None) -> str:
    if epoch is None or epoch <= 0:
        return ""
    return datetime.fromtimestamp(epoch).isoformat(timespec="milliseconds")


def _relative_time(
    event_epoch: float | None,
    monitoring_start: float,
) -> float | None:
    if event_epoch is None or monitoring_start <= 0:
        return None
    return round(max(event_epoch - monitoring_start, 0.0), 3)


def _resolve_event_epoch(
    timestamp: str, rel_time_s: float | None, base_time: float
) -> float | None:
    event_epoch = _parse_iso_timestamp(timestamp)
    if event_epoch is not None:
        return event_epoch
    if rel_time_s is not None and base_time > 0:
        return base_time + rel_time_s
    return None


def _actor_from_file_source(source: str) -> str:
    if source in {"extension", "automation", "system"}:
        return source
    return "unknown"


def _actor_from_network_event(event: NetworkEvent) -> str:
    if event.is_target_extension_event:
        return "extension"
    if event.attribution_status == "near_target_activation":
        return "unknown"
    return "unknown"


def _build_scenario_log_message(
    action: str,
    name: str,
    status: str,
    metadata: dict[str, Any] | None,
) -> str:
    label = name.replace("_", " ")
    intent = ""
    if metadata is not None:
        intent = str(metadata.get("intent", "")).strip()
    if action == "start":
        return f"Started scenario {label}" + (f": {intent}" if intent else "")
    if action == "end":
        verb = "Completed" if status != "failed" else "Failed"
        return f"{verb} scenario {label}" + (f": {intent}" if intent else "")
    return f"Scenario {label}"


def _build_stimulus_pass_log_message(
    action: str,
    label: str,
    status: str,
) -> str:
    verb = "Started" if action == "start" else "Finished"
    return f"{verb} {label} ({status})"


def _build_event_attempt_log_message(attempt: EventAttemptRecord) -> str:
    outcome = attempt.status or attempt.verification_status or "unknown"
    return (
        f"Event attempt {attempt.activation_event or attempt.event_family} "
        f"finished as {outcome}"
    )


def _build_activation_log_message(entry: ActivationEntry) -> str:
    parts = [f"Activated {entry.extension_id}"]
    if entry.activation_event:
        parts.append(f"via {entry.activation_event}")
    if entry.duration_ms is not None:
        parts.append(f"in {entry.duration_ms}ms")
    return " ".join(parts)


def _scenario_name_for_timestamp(
    timestamp: str,
    rel_time_s: float | None,
    scenario_traces: list[ScenarioTrace],
    monitoring_start: float,
) -> str:
    event_epoch = _resolve_event_epoch(timestamp, rel_time_s, monitoring_start)
    if event_epoch is None:
        return ""
    for trace in scenario_traces:
        if trace.started_at <= event_epoch <= (trace.ended_at or event_epoch):
            return trace.name
    return ""


def _find_event_attempt(
    report: ActivationReport,
    attempt_id: str,
) -> EventAttemptRecord | None:
    for attempt in report.event_attempts:
        if attempt.attempt_id == attempt_id:
            return attempt
    return None


def _extract_official_attempted_capabilities(payload: Any) -> list[str]:
    attempted: set[str] = set()
    for entry in getattr(payload, "coverage_matrix", []) or []:
        capability = str(entry.get("capability", "")).strip()
        if capability and (entry.get("is_active") or entry.get("selected")):
            attempted.add(capability)
    for capability in getattr(payload, "official_attempted_capabilities", []) or []:
        cap = str(capability).strip()
        if cap:
            attempted.add(cap)
    return sorted(attempted)


def _extract_heuristic_attempted_capabilities(payload: Any) -> list[str]:
    attempted: set[str] = set()
    coverage_tracks = getattr(payload, "coverage_tracks", {}) or {}
    heuristic_track = coverage_tracks.get("heuristic", {})
    for entry in (
        heuristic_track.get("matrix", []) if isinstance(heuristic_track, dict) else []
    ):
        capability = str(entry.get("capability", "")).strip()
        if capability and (entry.get("is_active") or entry.get("selected")):
            attempted.add(capability)
    for capability in getattr(payload, "heuristic_attempted_capabilities", []) or []:
        cap = str(capability).strip()
        if cap:
            attempted.add(cap)
    return sorted(attempted)


def _artifact_class_for_path(path: str) -> str:
    normalized = path.strip()
    if not normalized.endswith("/package.json"):
        return ""
    if normalized.startswith("/workspace/"):
        return "workspace_runtime"
    return "manifest_ingestion"


def _nearest_activation_matches(
    event_epoch: float | None,
    activations: list[ActivationEntry],
    target_extension_id: str,
) -> tuple[tuple[ActivationEntry, float] | None, tuple[ActivationEntry, float] | None]:
    if event_epoch is None:
        return None, None

    target_match: tuple[ActivationEntry, float] | None = None
    competitor_match: tuple[ActivationEntry, float] | None = None
    for activation in activations:
        activation_epoch = _parse_iso_timestamp(activation.timestamp)
        if activation_epoch is None:
            continue
        delta = abs(event_epoch - activation_epoch)
        if delta > 5.0:
            continue
        candidate = (activation, delta)
        if activation.extension_id == target_extension_id:
            if target_match is None or delta < target_match[1]:
                target_match = candidate
            continue
        if competitor_match is None or delta < competitor_match[1]:
            competitor_match = candidate
    return target_match, competitor_match


def _classify_event_attribution(
    event_epoch: float | None,
    activations: list[ActivationEntry],
    target_extension_id: str,
    *,
    observer: str,
) -> tuple[str, str, float, str, str, bool, str]:
    if observer == "inotify":
        return (
            "automation_noise",
            "inotify captures workspace automation and system activity, not extension-host ownership",
            0.0,
            "",
            "",
            False,
            "ownership is intentionally suppressed for inotify telemetry",
        )

    if not target_extension_id or event_epoch is None:
        return (
            "unattributed",
            "target extension context was unavailable for ownership analysis",
            0.0,
            "",
            "",
            False,
            "",
        )

    target_match, competitor_match = _nearest_activation_matches(
        event_epoch,
        activations,
        target_extension_id,
    )
    if target_match is None:
        if competitor_match is not None and competitor_match[1] <= 1.25:
            competitor_id = competitor_match[0].extension_id
            return (
                "competing_candidate",
                f"nearest activation belonged to competing extension {competitor_id}",
                0.35,
                target_extension_id,
                "",
                False,
                "a different extension activated closer to this event",
            )
        return (
            "unattributed",
            "no target activation was close enough to support ownership",
            0.0,
            "",
            "",
            False,
            "",
        )

    target_activation, target_delta = target_match
    competitor_delta = competitor_match[1] if competitor_match is not None else None
    if (
        competitor_match is not None
        and competitor_delta is not None
        and competitor_delta <= min(1.25, target_delta + 0.35)
    ):
        return (
            "competing_candidate",
            "target activation overlapped with another extension activation in the same window",
            0.45,
            target_extension_id,
            target_activation.activation_event,
            False,
            f"competing activation {competitor_match[0].extension_id} was too close",
        )

    if observer == "strace":
        if target_delta <= 1.25:
            confidence = (
                0.93 if target_delta <= 0.35 else 0.84 if target_delta <= 0.75 else 0.72
            )
            return (
                "target_attributed",
                "strace event aligned tightly with the target extension activation window",
                confidence,
                target_extension_id,
                target_activation.activation_event,
                True,
                "",
            )
        return (
            "unattributed",
            "strace observed extension-host I/O but the target activation was not close enough",
            0.0,
            "",
            "",
            False,
            "",
        )

    if target_delta <= 0.75:
        confidence = 0.78 if target_delta <= 0.35 else 0.66
        return (
            "target_attributed",
            "network event happened immediately after a target activation without a competing activation",
            confidence,
            target_extension_id,
            target_activation.activation_event,
            True,
            "",
        )
    if target_delta <= 5.0:
        confidence = max(0.28, round(0.58 - min(target_delta, 5.0) * 0.06, 2))
        return (
            "near_target_activation",
            "network event was only temporally close to the target activation",
            confidence,
            target_extension_id,
            target_activation.activation_event,
            False,
            "temporal proximity alone is not treated as ownership",
        )
    return (
        "unattributed",
        "no attribution rule matched this event",
        0.0,
        "",
        "",
        False,
        "",
    )


def _upgrade_inotify_correlations(file_events: list[FileEvent]) -> list[FileEvent]:
    strace_events = [event for event in file_events if event.observer == "strace"]
    for event in file_events:
        if (
            event.observer != "inotify"
            or event.attribution_status != "automation_noise"
        ):
            continue
        event_epoch = _parse_iso_timestamp(event.timestamp)
        if event_epoch is None:
            continue
        for strace_event in strace_events:
            strace_epoch = _parse_iso_timestamp(strace_event.timestamp)
            if strace_epoch is None:
                continue
            if (
                event.path != strace_event.path
                or event.operation != strace_event.operation
            ):
                continue
            if abs(event_epoch - strace_epoch) > 1.0:
                continue
            event.attribution_status = "corroboration"
            event.attribution_basis = "inotify duplicated a matching extension-host file event and is retained as corroboration only"
            event.attribution_confidence = 0.25
            event.noise_reason = (
                "duplicate workspace observation; ownership remains anchored to strace"
            )
            break
    return file_events


def _annotate_network_events(
    network_events: list[NetworkEvent],
    activations: list[ActivationEntry],
    scenario_traces: list[ScenarioTrace],
    target_extension_id: str,
) -> list[NetworkEvent]:
    annotated: list[NetworkEvent] = []
    for network_event in network_events:
        event_epoch = _resolve_event_epoch(
            network_event.timestamp,
            network_event.rel_time_s,
            0.0,
        )
        scenario_name = _scenario_name_for_timestamp(
            network_event.timestamp,
            network_event.rel_time_s,
            scenario_traces,
            0.0,
        )
        (
            attribution_status,
            attribution_basis,
            attribution_confidence,
            related_extension_id,
            related_activation_event,
            is_target_extension_event,
            noise_reason,
        ) = _classify_event_attribution(
            event_epoch,
            activations,
            target_extension_id,
            observer="network",
        )
        summary = network_event.summary
        if scenario_name:
            summary = f"{summary} [{scenario_name}]"
        annotated.append(
            NetworkEvent(
                timestamp=network_event.timestamp,
                rel_time_s=network_event.rel_time_s,
                protocol=network_event.protocol,
                event_type=network_event.event_type,
                source_ip=network_event.source_ip,
                destination_ip=network_event.destination_ip,
                destination_port=network_event.destination_port,
                host=network_event.host,
                path=network_event.path,
                related_extension_id=related_extension_id,
                related_activation_event=related_activation_event,
                attribution_status=attribution_status,
                attribution_basis=attribution_basis,
                attribution_confidence=attribution_confidence,
                is_target_extension_event=is_target_extension_event,
                noise_reason=noise_reason,
                summary=summary,
            )
        )
    return annotated


def _annotate_file_events(
    file_events: list[FileEvent],
    activations: list[ActivationEntry],
    scenario_traces: list[ScenarioTrace],
    target_extension_id: str,
) -> list[FileEvent]:
    annotated: list[FileEvent] = []
    for file_event in sorted(
        file_events,
        key=lambda entry: (
            entry.rel_time_s is None,
            entry.rel_time_s if entry.rel_time_s is not None else 0.0,
            entry.path,
        ),
    ):
        scenario_name = file_event.scenario_name
        event_epoch = _parse_iso_timestamp(file_event.timestamp)

        if event_epoch is not None and not scenario_name:
            for trace in scenario_traces:
                if (
                    trace.started_at
                    <= event_epoch
                    <= (trace.ended_at or trace.started_at)
                ):
                    scenario_name = trace.name
                    break

        source = file_event.source
        if file_event.observer == "strace":
            source = "extension"
        elif file_event.observer == "inotify" and scenario_name:
            source = "automation"
        elif file_event.observer == "inotify":
            source = "system"

        summary = file_event.summary
        if scenario_name:
            summary = f"{summary} [{scenario_name}]"
        (
            attribution_status,
            attribution_basis,
            attribution_confidence,
            related_extension_id,
            related_activation_event,
            is_target_extension_event,
            noise_reason,
        ) = _classify_event_attribution(
            event_epoch,
            activations,
            target_extension_id,
            observer=file_event.observer,
        )

        annotated.append(
            FileEvent(
                timestamp=file_event.timestamp,
                rel_time_s=file_event.rel_time_s,
                operation=file_event.operation,
                path=file_event.path,
                secondary_path=file_event.secondary_path,
                source=source,
                observer=file_event.observer,
                scenario_name=scenario_name,
                related_extension_id=related_extension_id,
                related_activation_event=related_activation_event,
                attribution_status=attribution_status,
                attribution_basis=attribution_basis,
                attribution_confidence=attribution_confidence,
                is_target_extension_event=is_target_extension_event,
                noise_reason=noise_reason,
                artifact_class=_artifact_class_for_path(file_event.path),
                flags=file_event.flags,
                sensitive=file_event.sensitive,
                summary=summary,
            )
        )

    return _upgrade_inotify_correlations(annotated)


def _build_evidence_bundle(
    report: ActivationReport,
) -> tuple[list[EvidenceEvent], list[EvidenceLink]]:
    events: list[EvidenceEvent] = []
    links: list[EvidenceLink] = list(report.evidence_links)
    monitoring_start = report.monitoring_start

    scenario_entries: list[tuple[str, ScenarioTrace]] = []
    activation_entries: list[tuple[str, ActivationEntry, float | None]] = []
    network_entries: list[tuple[str, NetworkEvent, float | None]] = []
    file_entries: list[tuple[str, FileEvent, float | None]] = []
    blocker_entries: list[tuple[str, LogStreamEntry, float | None]] = []

    for index, trace in enumerate(
        sorted(report.scenario_traces, key=lambda item: item.started_at),
        start=1,
    ):
        event_id = f"scenario-{index:04d}"
        scenario_entries.append((event_id, trace))
        rel_time_s = None
        if monitoring_start > 0 and trace.started_at > 0:
            rel_time_s = round(max(trace.started_at - monitoring_start, 0.0), 3)
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="scenario",
                timestamp=_format_epoch_timestamp(trace.started_at),
                rel_time_s=rel_time_s,
                collector="automation",
                actor="automation",
                scenario_name=trace.name,
                summary=f"Scenario {trace.name} {trace.status}",
                raw_context={
                    "status": trace.status,
                    "started_at": trace.started_at,
                    "ended_at": trace.ended_at,
                },
            )
        )

    for index, activation in enumerate(report.activated, start=1):
        event_id = f"activation-{index:04d}"
        event_epoch = _resolve_event_epoch(
            activation.timestamp,
            None,
            monitoring_start,
        )
        activation_entries.append((event_id, activation, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="activation",
                timestamp=activation.timestamp
                if activation.timestamp
                else _format_epoch_timestamp(event_epoch),
                rel_time_s=round(max(event_epoch - monitoring_start, 0.0), 3)
                if event_epoch is not None and monitoring_start > 0
                else None,
                collector=activation.source or "log",
                actor="extension",
                extension_id=activation.extension_id,
                activation_event=activation.activation_event,
                summary=(
                    f"Activation {activation.extension_id}"
                    + (
                        f" via {activation.activation_event}"
                        if activation.activation_event
                        else ""
                    )
                ),
                raw_context={
                    "success": activation.success,
                    "duration_ms": activation.duration_ms,
                    "source": activation.source,
                },
            )
        )

    ui_blockers = [
        entry for entry in report.log_entries if entry.stream == "ui_blockers"
    ]
    for index, blocker in enumerate(ui_blockers, start=1):
        event_id = f"ui-blocker-{index:04d}"
        event_epoch = _resolve_event_epoch(
            blocker.timestamp,
            blocker.rel_time_s,
            monitoring_start,
        )
        blocker_entries.append((event_id, blocker, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="ui_blocker",
                timestamp=blocker.timestamp
                if blocker.timestamp
                else _format_epoch_timestamp(event_epoch),
                rel_time_s=blocker.rel_time_s,
                collector=blocker.stream,
                actor="automation",
                scenario_name=blocker.scenario_name,
                activation_event=blocker.activation_event,
                summary=blocker.message,
                raw_context={
                    "status": blocker.status,
                    "stream": blocker.stream,
                },
            )
        )

    for index, network_event in enumerate(report.network_events, start=1):
        event_id = f"network-{index:04d}"
        event_epoch = _resolve_event_epoch(
            network_event.timestamp,
            network_event.rel_time_s,
            monitoring_start,
        )
        network_entries.append((event_id, network_event, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="network",
                timestamp=network_event.timestamp
                if network_event.timestamp
                else _format_epoch_timestamp(event_epoch),
                rel_time_s=network_event.rel_time_s,
                collector="tshark",
                actor=_actor_from_network_event(network_event),
                scenario_name=_scenario_name_for_timestamp(
                    network_event.timestamp,
                    network_event.rel_time_s,
                    report.scenario_traces,
                    monitoring_start,
                ),
                extension_id=network_event.related_extension_id,
                activation_event=network_event.related_activation_event,
                protocol=network_event.protocol,
                host=network_event.host,
                destination_ip=network_event.destination_ip,
                destination_port=network_event.destination_port,
                attribution_status=network_event.attribution_status,
                attribution_basis=network_event.attribution_basis,
                attribution_confidence=network_event.attribution_confidence,
                is_target_extension_event=network_event.is_target_extension_event,
                noise_reason=network_event.noise_reason,
                summary=network_event.summary,
                raw_context={
                    "event_type": network_event.event_type,
                    "source_ip": network_event.source_ip,
                    "path": network_event.path,
                },
            )
        )

    for index, file_event in enumerate(report.file_events, start=1):
        event_id = f"file-{index:04d}"
        event_epoch = _resolve_event_epoch(
            file_event.timestamp,
            file_event.rel_time_s,
            monitoring_start,
        )
        file_entries.append((event_id, file_event, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="file",
                timestamp=file_event.timestamp
                if file_event.timestamp
                else _format_epoch_timestamp(event_epoch),
                rel_time_s=file_event.rel_time_s,
                collector=file_event.observer or "unknown",
                actor=_actor_from_file_source(file_event.source),
                scenario_name=file_event.scenario_name,
                extension_id=file_event.related_extension_id,
                activation_event=file_event.related_activation_event,
                operation=file_event.operation,
                path=file_event.path,
                attribution_status=file_event.attribution_status,
                attribution_basis=file_event.attribution_basis,
                attribution_confidence=file_event.attribution_confidence,
                is_target_extension_event=file_event.is_target_extension_event,
                noise_reason=file_event.noise_reason,
                artifact_class=file_event.artifact_class,
                sensitive=file_event.sensitive,
                summary=file_event.summary,
                raw_context={
                    "secondary_path": file_event.secondary_path,
                    "flags": file_event.flags,
                    "observer": file_event.observer,
                    "source": file_event.source,
                },
            )
        )

    links.extend(
        _build_scenario_links(
            scenario_entries,
            activation_entries,
            network_entries,
            file_entries,
            blocker_entries,
        )
    )
    links.extend(
        _build_temporal_links(activation_entries, network_entries, file_entries)
    )
    links.extend(_build_duplicate_file_links(file_entries))
    links.extend(_build_noise_links(scenario_entries, file_entries, blocker_entries))
    return events, _dedupe_evidence_links(links)


def _build_scenario_links(
    scenario_entries: list[tuple[str, ScenarioTrace]],
    activation_entries: list[tuple[str, ActivationEntry, float | None]],
    network_entries: list[tuple[str, NetworkEvent, float | None]],
    file_entries: list[tuple[str, FileEvent, float | None]],
    blocker_entries: list[tuple[str, LogStreamEntry, float | None]],
) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for scenario_event_id, trace in scenario_entries:
        window_end = trace.ended_at or trace.started_at
        if trace.started_at <= 0 or window_end <= 0:
            continue
        for event_id, _, event_epoch in [
            *activation_entries,
            *network_entries,
            *file_entries,
            *blocker_entries,
        ]:
            if event_epoch is None:
                continue
            if trace.started_at <= event_epoch <= window_end:
                links.append(
                    EvidenceLink(
                        from_event_id=event_id,
                        to_event_id=scenario_event_id,
                        link_type="occurred_in_scenario",
                        confidence=1.0,
                        reason=f"Event happened during scenario window {trace.name}.",
                    )
                )
    return links


def _build_temporal_links(
    activation_entries: list[tuple[str, ActivationEntry, float | None]],
    network_entries: list[tuple[str, NetworkEvent, float | None]],
    file_entries: list[tuple[str, FileEvent, float | None]],
) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for event_id, file_event, event_epoch in file_entries:
        if event_epoch is None:
            continue
        activation_match = _nearest_activation(activation_entries, event_epoch)
        if activation_match is None:
            continue
        activation_event_id, _activation_entry, delta = activation_match
        if file_event.is_target_extension_event:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="caused_by_target_extension",
                    confidence=file_event.attribution_confidence
                    or _temporal_confidence(delta),
                    reason=(
                        "File activity is attributed to the target extension because the "
                        "extension-host event aligned with its activation window."
                    ),
                )
            )
        elif file_event.attribution_status in {"competing_candidate", "unattributed"}:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="near_target_activation",
                    confidence=_temporal_confidence(delta),
                    reason=(
                        "File activity happened near the target activation but ownership "
                        f"remains unconfirmed ({delta:.3f}s delta)."
                    ),
                )
            )

    for event_id, network_event, event_epoch in network_entries:
        if event_epoch is None:
            continue
        activation_match = _nearest_activation(activation_entries, event_epoch)
        if activation_match is None:
            continue
        activation_event_id, _activation_entry, delta = activation_match
        if network_event.is_target_extension_event:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="caused_by_target_extension",
                    confidence=network_event.attribution_confidence
                    or _temporal_confidence(delta),
                    reason=(
                        "Network activity is attributed to the target extension because it "
                        "followed a target activation without a competing activation."
                    ),
                )
            )
        elif network_event.attribution_status in {
            "near_target_activation",
            "competing_candidate",
        }:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="near_target_activation",
                    confidence=_temporal_confidence(delta),
                    reason=(
                        "Network activity happened near the target activation but remains "
                        f"correlative only ({delta:.3f}s delta)."
                    ),
                )
            )
    return links


def _build_duplicate_file_links(
    file_entries: list[tuple[str, FileEvent, float | None]],
) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for index, (left_id, left_event, left_epoch) in enumerate(file_entries):
        for right_id, right_event, right_epoch in file_entries[index + 1 :]:
            if left_event.path != right_event.path:
                continue
            if left_event.operation != right_event.operation:
                continue
            if left_event.observer == right_event.observer:
                continue
            if {left_event.observer, right_event.observer} != {"strace", "inotify"}:
                continue

            if (
                left_epoch is not None
                and right_epoch is not None
                and abs(left_epoch - right_epoch) > 1.0
            ):
                continue

            links.append(
                EvidenceLink(
                    from_event_id=left_id,
                    to_event_id=right_id,
                    link_type="duplicate_signal",
                    confidence=0.9,
                    reason=(
                        "Both strace and inotify observed the same file artifact "
                        "operation within the same investigation window."
                    ),
                )
            )
    return links


def _build_noise_links(
    scenario_entries: list[tuple[str, ScenarioTrace]],
    file_entries: list[tuple[str, FileEvent, float | None]],
    blocker_entries: list[tuple[str, LogStreamEntry, float | None]],
) -> list[EvidenceLink]:
    scenario_ids = {trace.name: event_id for event_id, trace in scenario_entries}
    links: list[EvidenceLink] = []
    for event_id, file_event, _ in file_entries:
        scenario_event_id = scenario_ids.get(file_event.scenario_name)
        if scenario_event_id is None:
            continue
        if file_event.attribution_status == "automation_noise":
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=scenario_event_id,
                    link_type="automation_noise",
                    confidence=1.0,
                    reason=(
                        "This inotify file event belongs to the automation scenario rather "
                        "than extension-host ownership."
                    ),
                )
            )
    for event_id, blocker_entry, _ in blocker_entries:
        scenario_event_id = scenario_ids.get(blocker_entry.scenario_name)
        if scenario_event_id is None:
            continue
        links.append(
            EvidenceLink(
                from_event_id=event_id,
                to_event_id=scenario_event_id,
                link_type="blocked_by_ui",
                confidence=1.0,
                reason="A VS Code popup or modal interfered with the active automation flow.",
            )
        )
    return links


def _nearest_activation(
    activation_entries: list[tuple[str, ActivationEntry, float | None]],
    event_epoch: float,
) -> tuple[str, ActivationEntry, float] | None:
    nearest: tuple[str, ActivationEntry, float] | None = None
    for activation_event_id, activation_entry, activation_epoch in activation_entries:
        if activation_epoch is None:
            continue
        delta = abs(event_epoch - activation_epoch)
        if delta > 5.0:
            continue
        if nearest is None or delta < nearest[2]:
            nearest = (activation_event_id, activation_entry, delta)
    return nearest


def _temporal_confidence(delta: float) -> float:
    return max(0.2, round(0.7 - min(delta, 5.0) * 0.1, 2))


def _dedupe_evidence_links(links: list[EvidenceLink]) -> list[EvidenceLink]:
    deduped: list[EvidenceLink] = []
    seen: set[tuple[str, str, str, str]] = set()
    for link in links:
        key = (
            link.from_event_id,
            link.to_event_id,
            link.link_type,
            link.reason,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(link)
    return deduped


def _derive_verified_capabilities(report: ActivationReport) -> list[str]:
    return derive_verified_capabilities(report)


def _count_target_activations(
    activations: list[ActivationEntry],
    target_extension_id: str,
) -> int:
    return count_target_activations(activations, target_extension_id)


def _reconcile_coverage_verification(
    report: ActivationReport,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    return reconcile_coverage_verification(report)


def _build_run_quality(report: ActivationReport) -> tuple[str, list[str]]:
    return build_run_quality(report, report.automation_health)


def _is_background_activation(activation_event: str) -> bool:
    return is_background_activation(activation_event)


def _indexed_target_activations(
    report: ActivationReport,
) -> list[tuple[str, ActivationEntry]]:
    if not report.target_extension_id:
        return []
    return [
        (f"activation-{index:04d}", entry)
        for index, entry in enumerate(report.activated, start=1)
        if entry.extension_id == report.target_extension_id
    ]


def _indexed_target_file_events(
    report: ActivationReport,
) -> list[tuple[str, FileEvent]]:
    return [
        (f"file-{index:04d}", entry)
        for index, entry in enumerate(report.file_events, start=1)
        if entry.is_target_extension_event
    ]


def _indexed_target_network_events(
    report: ActivationReport,
) -> list[tuple[str, NetworkEvent]]:
    return [
        (f"network-{index:04d}", entry)
        for index, entry in enumerate(report.network_events, start=1)
        if entry.is_target_extension_event
    ]


def _indexed_ui_blockers(report: ActivationReport) -> list[tuple[str, LogStreamEntry]]:
    return [
        (f"ui-blocker-{index:04d}", entry)
        for index, entry in enumerate(report.ui_blocker_entries, start=1)
    ]


def _build_risk_signals(report: ActivationReport) -> list[RiskSignal]:
    return build_risk_signals(report, RiskSignal)


def _build_risk_summary(signals: list[RiskSignal]) -> dict[str, Any]:
    return build_risk_summary(signals)


def _build_verdict(report: ActivationReport) -> dict[str, Any]:
    return build_verdict(
        report,
        automation_health=report.automation_health,
        run_quality=build_run_quality(report, report.automation_health),
    )


def _matches_extension_signature(
    file_event: FileEvent,
    extension_signatures: list[tuple[str, str, float | None]],
) -> bool:
    for path, operation, rel_time in extension_signatures:
        if path != file_event.path or operation != file_event.operation:
            continue
        if rel_time is None or file_event.rel_time_s is None:
            return True
        if abs(rel_time - file_event.rel_time_s) <= 1.0:
            return True
    return False


def _snapshot_log_offsets() -> dict[str, int]:
    """Capture current end offsets for all known Extension Host logs."""
    offsets: dict[str, int] = {}
    for log_path in find_exthost_logs():
        try:
            offsets[str(log_path.resolve())] = log_path.stat().st_size
        except OSError as exc:
            _log(f"Failed to snapshot {log_path}: {exc}")
    return offsets
