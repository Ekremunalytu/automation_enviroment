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

import json
import re
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from types import TracebackType

import commands
import keyboard
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

VSCODE_USER_DATA = Path("/home/executor/.vscode")
VSCODE_LOGS_DIR = VSCODE_USER_DATA / "logs"
RESULTS_DIR = Path("/results")

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
    summary: str = ""


@dataclass
class ActivationReport:
    """Aggregated monitoring results."""

    activated: list[ActivationEntry] = field(default_factory=list)
    running_extensions: list[RunningExtension] = field(default_factory=list)
    network_events: list[NetworkEvent] = field(default_factory=list)
    network_capture_error: str = ""
    extension_host_output: str = ""
    log_file_path: str = ""
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
    def summary(self) -> dict:
        unique_ids = self.activated_ids | self.runtime_ids
        return {
            "total_activated": len(self.activated),
            "unique_extensions": len(unique_ids),
            "unique_event_extensions": len(self.activated_ids),
            "running_extensions": len(self.running_extensions),
            "monitoring_duration_s": round(self.duration_s, 1),
            "monitoring_started_at": self.monitoring_start,
            "monitoring_ended_at": self.monitoring_end,
            "extension_ids": sorted(unique_ids),
            "scenarios_run": self.scenarios_run,
            "network_events": len(self.network_events),
            "network_hosts": len(self.network_hosts),
        }

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

    def save(self, path: str | Path, announce: bool = True) -> Path:
        """Save full report as JSON."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        # Truncate extension host output to last 500 lines to avoid huge files
        eh_lines = self.extension_host_output.splitlines()
        if len(eh_lines) > 500:
            eh_text = "\n".join(eh_lines[-500:])
        else:
            eh_text = self.extension_host_output
        data = {
            "summary": self.summary,
            "activated": [asdict(e) for e in self.activated],
            "running_extensions": [asdict(e) for e in self.running_extensions],
            "network_events": [asdict(e) for e in self.network_events],
            "network_summary": self.network_summary,
            "extension_host_output_lines": self.extension_host_output.count("\n"),
            "extension_host_output": eh_text,
            "log_file": self.log_file_path,
        }
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        temp_out = out.parent / f".{out.name}.tmp"
        temp_out.write_text(serialized, encoding="utf-8")
        temp_out.replace(out)
        if announce:
            _log(f"Report saved to {out}")
        return out

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
# Strategy 5: Log file watching (real-time via inotifywait)
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

    def __init__(self, page: Page, report_path: str | Path | None = None) -> None:
        self.page = page
        self.report_path = Path(report_path) if report_path is not None else None
        self.report = ActivationReport()
        self._started = False
        self._log_offsets: dict[str, int] = {}
        self._network_capture: NetworkCapture | None = None
        self._last_persist_at = 0.0

    def start(self) -> None:
        """Record the monitoring start time."""
        self.report.monitoring_start = time.time()
        self._log_offsets = _snapshot_log_offsets()
        self._network_capture = NetworkCapture(
            monitoring_start=self.report.monitoring_start,
            on_event=self._handle_network_event,
        )
        self._network_capture.start()
        if self._network_capture.start_error:
            self.report.network_capture_error = self._network_capture.start_error
        self._started = True
        self._persist_report(force=True)
        _log("Monitoring started")

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

        self.report.monitoring_end = time.time()
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

    def _persist_report(self, force: bool) -> None:
        if self.report_path is None:
            return

        now = time.time()
        if (
            not force
            and (len(self.report.network_events) % 5 != 0)
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


def _snapshot_log_offsets() -> dict[str, int]:
    """Capture current end offsets for all known Extension Host logs."""
    offsets: dict[str, int] = {}
    for log_path in find_exthost_logs():
        try:
            offsets[str(log_path.resolve())] = log_path.stat().st_size
        except OSError as exc:
            _log(f"Failed to snapshot {log_path}: {exc}")
    return offsets
