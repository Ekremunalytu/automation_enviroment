"""Extension Host log discovery, activation parsing, and strace capture."""

from __future__ import annotations

import re
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from ._shared import VSCODE_LOGS_DIR, _log, _parse_iso_timestamp
from .events import ActivationEntry, FileEvent, ProcessEvent
from .filesystem import parse_strace_file_event_line

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

# Lifecycle marker patterns enrich event_attempts correlation in
# health_reconciliation (PR345 PR3). Each entry is (compiled_pattern,
# marker_type) where marker_type ends up on ActivationEntry.marker_type.
# Kept sibling to _ACTIVATION_PATTERNS so the existing dedup contract
# (entry per (id, event, timestamp, duration_ms)) stays intact for the
# default activation path; lifecycle entries dedup on the same tuple
# extended with marker_type.
_LIFECYCLE_MARKER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # "activate(<id>) entered"
    (
        re.compile(r"activate(?:Function)?\s*\((?P<id>[\w.\-]+)\)\s*entered"),
        "activate_fn_entry",
    ),
    # "activateFunction entered for <id>" / "activate entered <id>"
    (
        re.compile(r"activate(?:Function)?\s*entered.*?(?P<id>[\w.\-]+)"),
        "activate_fn_entry",
    ),
    # "activate(<id>) returned in 42ms" / "activate(<id>) completed"
    (
        re.compile(
            r"activate(?:Function)?\s*\((?P<id>[\w.\-]+)\)\s*"
            r"(?:returned|completed)"
            r"(?:.*?in\s+(?P<ms>\d+)\s*ms)?"
        ),
        "activate_fn_exit",
    ),
    # "activate returned for <id> in <N>ms" / "activate completed <id>"
    (
        re.compile(
            r"activate(?:Function)?\s*"
            r"(?:returned|completed).*?(?P<id>[\w.\-]+)"
            r"(?:.*?in\s+(?P<ms>\d+)\s*ms)?"
        ),
        "activate_fn_exit",
    ),
    # "registered command 'extrace.example.run' for <id>"
    (
        re.compile(
            r"register(?:ed|ing)?\s+command\s+'(?P<event>[^']+)'"
            r"(?:.*?(?:for|by|from)\s+(?P<id>[\w.\-]+))?"
        ),
        "command_register",
    ),
    # "registered FooProvider for <id>"
    (
        re.compile(
            r"register(?:ed|ing)?\s+(?P<event>\w+Provider)"
            r"(?:.*?(?:for|by|from)\s+(?P<id>[\w.\-]+))?"
        ),
        "provider_register",
    ),
]

# Timestamp pattern at start of VS Code log lines
_TIMESTAMP_RE = re.compile(r"^\[?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\]?")
_PROCESS_EVENT_RE = re.compile(
    r"^(?:\[pid\s+(?P<pid>\d+)\]\s+)?(?P<ts>\d+\.\d+)\s+"
    r"(?P<call>execve|execveat|clone|clone3|fork|vfork|chdir)\((?P<args>.*)\)\s+=\s+(?P<result>.+)$"
)
_PROCESS_ARGUMENT_PREVIEW = 256


def _parse_activation_lines(lines: list[str], *, source: str) -> list[ActivationEntry]:
    entries: list[ActivationEntry] = []
    seen: set[tuple[str, str, str, int | None, str]] = set()

    for line in lines:
        lowered = line.lower()
        if "activ" not in lowered and "register" not in lowered:
            continue

        ts_match = _TIMESTAMP_RE.match(line)
        timestamp = ts_match.group(1) if ts_match else ""

        matched = False
        for pattern in _ACTIVATION_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue

            ext_id = match.group("id")
            event = match.groupdict().get("event", "") or ""
            ms_str = match.groupdict().get("ms")
            duration_ms = int(ms_str) if ms_str else None
            dedup_key = (ext_id, event, timestamp, duration_ms, "")

            if dedup_key in seen:
                matched = True
                break

            seen.add(dedup_key)
            entries.append(
                ActivationEntry(
                    extension_id=ext_id,
                    activation_event=event,
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                    source=source,
                )
            )
            matched = True
            break

        if matched:
            continue

        for pattern, marker_type in _LIFECYCLE_MARKER_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue

            ext_id = match.groupdict().get("id") or ""
            if not ext_id:
                continue

            event = match.groupdict().get("event", "") or ""
            ms_str = match.groupdict().get("ms")
            duration_ms = int(ms_str) if ms_str else None
            dedup_key = (ext_id, event, timestamp, duration_ms, marker_type)

            if dedup_key in seen:
                break

            seen.add(dedup_key)
            entries.append(
                ActivationEntry(
                    extension_id=ext_id,
                    activation_event=event,
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                    source=source,
                    marker_type=marker_type,
                )
            )
            break

    return entries


def _activation_within_monitoring_window(
    entry: ActivationEntry,
    monitoring_start: float,
) -> bool:
    if monitoring_start <= 0:
        return True

    event_epoch = _parse_iso_timestamp(entry.timestamp)
    if event_epoch is None:
        return True

    return event_epoch >= monitoring_start


_LAST_EXTHOST_LOG_COUNT: int = -1


def find_exthost_logs() -> list[Path]:
    """Find all Extension Host log files under the VS Code logs directory.

    Returns paths sorted newest-first.
    """
    global _LAST_EXTHOST_LOG_COUNT
    if not VSCODE_LOGS_DIR.exists():
        if _LAST_EXTHOST_LOG_COUNT != -2:
            _log(f"Log directory not found: {VSCODE_LOGS_DIR}")
            _LAST_EXTHOST_LOG_COUNT = -2
        return []

    patterns = ["**/exthost*/exthost.log", "**/exthost*.log"]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(VSCODE_LOGS_DIR.glob(pattern))

    seen: set[str] = set()
    unique: list[Path] = []
    for p in sorted(found, key=lambda x: x.stat().st_mtime, reverse=True):
        canon = str(p.resolve())
        if canon not in seen:
            seen.add(canon)
            unique.append(p)

    if len(unique) != _LAST_EXTHOST_LOG_COUNT:
        _log(f"Found {len(unique)} Extension Host log file(s)")
        _LAST_EXTHOST_LOG_COUNT = len(unique)
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
    entries = _parse_activation_lines(content.splitlines(), source="log")

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
    seen_entries: set[tuple[str, str, str, int | None, str, str]] = set()
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
                entry.marker_type,
            )
            if dedup_key in seen_entries:
                continue
            seen_entries.add(dedup_key)
            all_entries.append(entry)

    return all_entries


def read_extension_host_output(page: Any = None) -> str:
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


def parse_activations_from_output(
    output: str,
    *,
    monitoring_start: float = 0.0,
) -> list[ActivationEntry]:
    """Parse activation entries from final Extension Host output."""
    entries = _parse_activation_lines(output.splitlines(), source="output")
    return [
        entry
        for entry in entries
        if _activation_within_monitoring_window(entry, monitoring_start)
    ]


def parse_strace_process_event_line(
    line: str,
    *,
    monitoring_start: float = 0.0,
    root_pid: int,
    ppid_by_pid: dict[int, int | None],
    cwd_by_pid: dict[int, str],
) -> ProcessEvent | None:
    match = _PROCESS_EVENT_RE.match(line.strip())
    if match is None:
        return None

    try:
        timestamp_epoch = float(match.group("ts"))
    except ValueError:
        return None

    call = match.group("call")
    args = match.group("args")
    result = match.group("result").strip()
    current_pid = int(match.group("pid") or root_pid)
    current_ppid = ppid_by_pid.get(current_pid)
    current_cwd = cwd_by_pid.get(current_pid, "")
    rel_time_s = None
    if monitoring_start > 0:
        rel_time_s = round(max(timestamp_epoch - monitoring_start, 0.0), 3)
    timestamp = datetime.fromtimestamp(timestamp_epoch).isoformat(
        timespec="milliseconds"
    )

    if call in {"clone", "clone3", "fork", "vfork"}:
        try:
            child_pid = int(result.split()[0])
        except ValueError:
            return None
        ppid_by_pid[child_pid] = current_pid
        return ProcessEvent(
            timestamp=timestamp,
            rel_time_s=rel_time_s,
            pid=child_pid,
            ppid=current_pid,
            operation="spawn",
            command=call,
            arguments_preview=_bounded_arguments_preview(args),
            cwd=current_cwd,
            summary=f"Spawned child process {child_pid} from pid {current_pid}.",
        )

    quoted_items = re.findall(r'"([^"]*)"', args)
    if call in {"execve", "execveat"}:
        if not quoted_items:
            return None
        command = quoted_items[0]
        arguments_preview = _bounded_arguments_preview(" ".join(quoted_items[1:]))
        return ProcessEvent(
            timestamp=timestamp,
            rel_time_s=rel_time_s,
            pid=current_pid,
            ppid=current_ppid,
            operation="exec",
            command=command,
            arguments_preview=arguments_preview,
            cwd=current_cwd,
            summary=f"Executed {command} in pid {current_pid}.",
        )

    if call == "chdir":
        if not quoted_items:
            return None
        cwd_by_pid[current_pid] = quoted_items[0]
        return ProcessEvent(
            timestamp=timestamp,
            rel_time_s=rel_time_s,
            pid=current_pid,
            ppid=current_ppid,
            operation="chdir",
            command="chdir",
            arguments_preview="",
            cwd=quoted_items[0],
            summary=f"Changed working directory to {quoted_items[0]}.",
        )

    return None


def _bounded_arguments_preview(raw: str) -> str:
    preview = " ".join(raw.split())
    if len(preview) <= _PROCESS_ARGUMENT_PREVIEW:
        return preview
    return preview[: _PROCESS_ARGUMENT_PREVIEW - 3] + "..."


class ExtensionHostFileCapture:
    """Attach strace to the current Extension Host process."""

    def __init__(
        self,
        monitoring_start: float,
        on_event: Callable[[FileEvent], None] | None = None,
        on_process_event: Callable[[ProcessEvent], None] | None = None,
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.on_process_event = on_process_event
        self.events: list[FileEvent] = []
        self.process_events: list[ProcessEvent] = []
        self.start_error = ""
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._pid: int | None = None
        self._ppid_by_pid: dict[int, int | None] = {}
        self._cwd_by_pid: dict[int, str] = {}
        self.attach_attempts = 0
        self.diagnostics: dict[str, Any] = {
            "attempts": 0,
            "selected_pid": None,
            "status": "planned",
            "poll_timeout_s": 10.0,
            "poll_interval_s": 0.5,
            "failure_reason": "",
        }

    @property
    def pid(self) -> int | None:
        return self._pid

    def start(self) -> None:
        # Imported lazily to avoid a circular import with ``monitor`` which
        # owns the process-table inspection helpers.
        from ..monitor import _wait_for_extension_host_pid

        pid, diagnostics = _wait_for_extension_host_pid()
        self.attach_attempts = int(diagnostics.get("attempts", 0) or 0)
        self.diagnostics = diagnostics
        if pid is None:
            self.start_error = (
                "Extension Host PID not found; file attribution unavailable."
            )
            self.diagnostics["status"] = "failed"
            self.diagnostics["failure_reason"] = self.start_error
            _log(self.start_error)
            return

        self._pid = pid
        self._ppid_by_pid[pid] = None
        self.diagnostics["selected_pid"] = pid
        cmd = [
            "strace",
            "-f",
            "-ttt",
            "-s",
            "256",
            "-e",
            (
                "trace=open,openat,creat,unlink,unlinkat,rename,renameat,"
                "renameat2,mkdir,rmdir,newfstatat,readlink,execve,execveat,"
                "clone,clone3,fork,vfork,chdir"
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
            self.diagnostics["status"] = "failed"
            self.diagnostics["failure_reason"] = self.start_error
            _log(self.start_error)
            return
        except OSError as exc:
            self.start_error = f"strace start failed: {exc}"
            self.diagnostics["status"] = "failed"
            self.diagnostics["failure_reason"] = self.start_error
            _log(self.start_error)
            return

        self._reader = threading.Thread(target=self._consume_stderr, daemon=True)
        self._reader.start()
        self.diagnostics["status"] = "attached"
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
            process_event = parse_strace_process_event_line(
                line,
                monitoring_start=self.monitoring_start,
                root_pid=self._pid or 0,
                ppid_by_pid=self._ppid_by_pid,
                cwd_by_pid=self._cwd_by_pid,
            )
            if process_event is not None:
                self.process_events.append(process_event)
                if self.on_process_event is not None:
                    self.on_process_event(process_event)
            event = parse_strace_file_event_line(
                line,
                monitoring_start=self.monitoring_start,
            )
            if event is None:
                continue
            self.events.append(event)
            if self.on_event is not None:
                self.on_event(event)


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
        # arch-allow: bare-binary-path  # W8-4-followup: see POST_POC_BACKLOG.md
        proc = subprocess.Popen(  # nosec B603,B607
            ["inotifywait", "-m", "-e", "modify", str(log_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        start = time.monotonic()
        seen_ids: set[str] = set()

        while time.monotonic() - start < timeout_s:
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
    start = time.monotonic()
    seen_ids: set[str] = set()

    while time.monotonic() - start < timeout_s:
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
