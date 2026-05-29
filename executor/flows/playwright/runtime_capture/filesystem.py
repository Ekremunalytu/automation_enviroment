"""Filesystem capture via inotifywait."""

from __future__ import annotations

import re
import subprocess
import threading
import time
from collections.abc import Callable
from datetime import datetime

from executor.binary_paths import INOTIFYWAIT_PATH

from ._shared import (
    _FILE_WATCH_PATHS,
    _is_relevant_file_path,
    _is_sensitive_path,
    _log,
)
from .events import FileEvent

_STRACE_CALL_RE = re.compile(
    r"^(?:\[pid\s+(?P<pid>\d+)\]\s+)?(?P<ts>\d+\.\d+)\s+"
    r"(?P<call>\w+)\((?P<args>.*)\)\s+=\s+(?P<result>.+)$"
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


def parse_strace_file_event_line(
    line: str,
    monitoring_start: float = 0.0,
    *,
    root_pid: int = 0,
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

    pid_group = match.group("pid")
    pid = int(pid_group) if pid_group else (root_pid or None)

    return FileEvent(
        timestamp=timestamp,
        rel_time_s=rel_time_s,
        operation=operation,
        path=primary_path,
        secondary_path=secondary_path,
        source="extension",
        observer="strace",
        pid=pid,
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
            INOTIFYWAIT_PATH,
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
