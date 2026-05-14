"""Extension Host strace capture orchestrator + log watching (W12-5 split from extension_host.py)."""

from __future__ import annotations

import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from executor.binary_paths import INOTIFYWAIT_PATH, STRACE_PATH

from ._shared import _log
from .events import ActivationEntry, FileEvent, ProcessEvent
from .extension_host_log_parse import _ACTIVATION_PATTERNS, find_exthost_logs
from .extension_host_strace_parse import parse_strace_process_event_line
from .filesystem import parse_strace_file_event_line


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
            STRACE_PATH,
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
        proc = subprocess.Popen(  # nosec B603,B607
            [INOTIFYWAIT_PATH, "-m", "-e", "modify", str(log_path)],
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
