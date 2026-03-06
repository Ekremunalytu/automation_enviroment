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
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
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
class ActivationReport:
    """Aggregated monitoring results."""

    activated: list[ActivationEntry] = field(default_factory=list)
    running_extensions: list[RunningExtension] = field(default_factory=list)
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
    def summary(self) -> dict:
        return {
            "total_activated": len(self.activated),
            "unique_extensions": len(self.activated_ids),
            "running_extensions": len(self.running_extensions),
            "monitoring_duration_s": round(self.duration_s, 1),
            "extension_ids": sorted(self.activated_ids),
            "scenarios_run": self.scenarios_run,
        }

    def save(self, path: str | Path) -> Path:
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
            "extension_host_output_lines": self.extension_host_output.count("\n"),
            "extension_host_output": eh_text,
            "log_file": self.log_file_path,
        }
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        temp_out = out.parent / f".{out.name}.tmp"
        temp_out.write_text(serialized, encoding="utf-8")
        temp_out.replace(out)
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
        if self.activated:
            print("\n  Activated extensions:")
            for entry in self.activated:
                event = f" [{entry.activation_event}]" if entry.activation_event else ""
                timing = f" ({entry.duration_ms}ms)" if entry.duration_ms else ""
                src = f" via {entry.source}" if entry.source else ""
                print(f"    - {entry.extension_id}{event}{timing}{src}")
        if self.running_extensions:
            print("\n  Running extensions (from UI):")
            for ext in self.running_extensions:
                name = f" ({ext.name})" if ext.name else ""
                timing = (
                    f" {ext.activation_time_ms}ms" if ext.activation_time_ms else ""
                )
                print(f"    - {ext.extension_id}{name}{timing}")
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
    seen: set[str] = set()

    for line in content.splitlines():
        # Skip empty or irrelevant lines early
        if "activ" not in line.lower():
            continue

        # Try each pattern
        for pattern in _ACTIVATION_PATTERNS:
            m = pattern.search(line)
            if m:
                ext_id = m.group("id")
                # Deduplicate by extension ID (keep first occurrence)
                dedup_key = ext_id
                if dedup_key in seen:
                    break
                seen.add(dedup_key)

                event = m.groupdict().get("event", "") or ""
                ms_str = m.groupdict().get("ms")
                duration_ms = int(ms_str) if ms_str else None

                # Extract timestamp
                ts_match = _TIMESTAMP_RE.match(line)
                timestamp = ts_match.group(1) if ts_match else ""

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
    seen_ids: set[str] = set()
    offsets = start_offsets or {}

    for log_path in find_exthost_logs():
        start_offset = offsets.get(str(log_path.resolve()), 0)
        for entry in parse_activations_from_log(log_path, start_offset=start_offset):
            if entry.extension_id not in seen_ids:
                seen_ids.add(entry.extension_id)
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
# Strategy 4: Log file watching (real-time via inotifywait)
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

    def __init__(self, page: Page) -> None:
        self.page = page
        self.report = ActivationReport()
        self._started = False
        self._log_offsets: dict[str, int] = {}

    def start(self) -> None:
        """Record the monitoring start time."""
        self.report.monitoring_start = time.time()
        self._log_offsets = _snapshot_log_offsets()
        self._started = True
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

        self.report.monitoring_end = time.time()
        _log(f"Monitoring stopped ({self.report.duration_s:.1f}s elapsed)")

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

        # Strategy 2: Running Extensions UI snapshot
        try:
            _log("Strategy 2: Scraping Running Extensions UI...")
            self.report.running_extensions = get_running_extensions(self.page)
        except Exception as exc:
            _log(f"Strategy 2 failed: {exc}")
            # Dismiss any stuck dialogs (may also fail if VS Code crashed)
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
            except Exception as esc_exc:
                _log(f"Strategy 2 recovery failed: {esc_exc}")

        # Strategy 3: Extension Host output from log files
        try:
            _log("Strategy 3: Reading Extension Host output...")
            self.report.extension_host_output = read_extension_host_output()
        except OSError as exc:
            _log(f"Strategy 3 failed: {exc}")

        # Merge UI results into activated list if they have new IDs
        log_ids = {e.extension_id for e in self.report.activated}
        for ext in self.report.running_extensions:
            if ext.extension_id not in log_ids:
                self.report.activated.append(
                    ActivationEntry(
                        extension_id=ext.extension_id,
                        duration_ms=ext.activation_time_ms,
                        source="ui",
                    )
                )

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


def _snapshot_log_offsets() -> dict[str, int]:
    """Capture current end offsets for all known Extension Host logs."""
    offsets: dict[str, int] = {}
    for log_path in find_exthost_logs():
        try:
            offsets[str(log_path.resolve())] = log_path.stat().st_size
        except OSError as exc:
            _log(f"Failed to snapshot {log_path}: {exc}")
    return offsets
