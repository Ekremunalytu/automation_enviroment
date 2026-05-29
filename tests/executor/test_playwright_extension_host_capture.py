"""Integration tests for ``ExtensionHostFileCapture`` (W12-5 split target).

The class is the strace orchestrator that ``runtime_capture/extension_host.py``
re-exports through its facade. The W11 precursor suite at
``tests/executor/test_playwright_extension_host.py`` only asserts the
``__init__`` shape and the ``stop()`` no-op path; this file fills the
``start() -> consume_stderr -> stop()`` integration gap.

All cases drive the capture through fake ``subprocess.Popen`` stderr streams
and a fake ``_wait_for_extension_host_pid`` so they stay deterministic
without strace or a live Extension Host process.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from executor.flows.playwright.runtime_capture import extension_host
from executor.flows.playwright.runtime_capture import (
    extension_host_capture as capture_module,
)
from executor.flows.playwright.runtime_capture.events import FileEvent, ProcessEvent


# ---------------------------------------------------------------------------
# Fake subprocess.Popen — minimal surface used by ExtensionHostFileCapture
# ---------------------------------------------------------------------------


class _FakeStderrStream:
    """Iterator over canned strace stderr lines that signals EOF when drained."""

    def __init__(self, lines: list[str]) -> None:
        self._iter: Iterator[str] = iter(lines)

    def __iter__(self) -> _FakeStderrStream:
        return self

    def __next__(self) -> str:
        return next(self._iter)


class _FakePopen:
    def __init__(
        self,
        cmd: list[str],
        *,
        stdout: Any = None,
        stderr: Any = None,
        text: bool = True,
        bufsize: int = 1,
        stderr_lines: list[str] | None = None,
    ) -> None:
        self.cmd = cmd
        self.stderr = _FakeStderrStream(stderr_lines or [])
        self.terminated = False
        self.killed = False
        self._returncode: int | None = None

    def poll(self) -> int | None:
        return self._returncode

    def terminate(self) -> None:
        self.terminated = True
        self._returncode = 0

    def kill(self) -> None:
        self.killed = True
        self._returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        return self._returncode or 0


def _make_fake_popen_factory(
    stderr_lines: list[str],
) -> type[_FakePopen]:
    """Bind canned stderr lines into a Popen subclass with the right signature."""

    class _BoundFakePopen(_FakePopen):
        def __init__(self, cmd: list[str], **kwargs: Any) -> None:
            super().__init__(cmd, stderr_lines=stderr_lines, **kwargs)

    return _BoundFakePopen


def _patch_pid_resolver(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pid: int | None,
    diagnostics: dict[str, Any] | None = None,
) -> None:
    """Replace the lazy-imported PID resolver inside the monitor facade."""
    if diagnostics is None:
        diagnostics = {
            "attempts": 1,
            "selected_pid": pid,
            "status": "planned",
            "poll_timeout_s": 10.0,
            "poll_interval_s": 0.5,
            "failure_reason": "",
        }

    def _fake_resolver() -> tuple[int | None, dict[str, Any]]:
        return pid, dict(diagnostics)

    # ``ExtensionHostFileCapture.start`` does ``from ..monitor import
    # _wait_for_extension_host_pid`` lazily, so patching the attribute on the
    # already-imported monitor module is the canonical interception point.
    from executor.flows.playwright import monitor as monitor_module

    monkeypatch.setattr(monitor_module, "_wait_for_extension_host_pid", _fake_resolver)


def _wait_for_thread_drain(capture: Any, deadline_s: float = 1.0) -> None:
    """Spin briefly until the daemon stderr-reader thread has drained the iterator."""
    start = time.monotonic()
    while time.monotonic() - start < deadline_s:
        reader = capture._reader
        if reader is None or not reader.is_alive():
            return
        time.sleep(0.01)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_extension_host_file_capture_attaches_strace_with_pid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path: PID resolved, Popen succeeds, status flips to ``attached``."""
    _patch_pid_resolver(monkeypatch, pid=4242)
    monkeypatch.setattr(
        capture_module.subprocess, "Popen", _make_fake_popen_factory([])
    )

    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    cap.start()
    _wait_for_thread_drain(cap)

    assert cap.pid == 4242
    assert cap.attach_attempts >= 1
    assert cap.start_error == ""
    assert cap.diagnostics["status"] == "attached"
    assert cap.diagnostics["selected_pid"] == 4242
    cap.stop()


def test_extension_host_file_capture_invokes_event_callback_on_strace_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fake strace stderr lines are routed through the parser and into callbacks."""
    _patch_pid_resolver(monkeypatch, pid=100)
    stderr_lines = [
        # process-event: clone, child pid 4242 spawned from root pid 100
        "[pid 100] 1700000001.000 clone(child_stack=NULL) = 4242\n",
        # file-event: openat on the child pid (parsed by parse_strace_file_event_line)
        '[pid 4242] 1700000002.000 openat(AT_FDCWD, "/tmp/probe.txt", O_RDONLY) = 7\n',
    ]
    monkeypatch.setattr(
        capture_module.subprocess, "Popen", _make_fake_popen_factory(stderr_lines)
    )

    seen_files: list[FileEvent] = []
    seen_procs: list[ProcessEvent] = []
    cap = extension_host.ExtensionHostFileCapture(
        monitoring_start=0.0,
        on_event=seen_files.append,
        on_process_event=seen_procs.append,
    )
    cap.start()
    _wait_for_thread_drain(cap)

    # Process events captured: at least the spawn line.
    spawn_events = [e for e in cap.process_events if e.operation == "spawn"]
    assert spawn_events, "expected the clone() line to produce a spawn ProcessEvent"
    assert spawn_events[0].pid == 4242
    assert spawn_events[0].ppid == 100
    # Callback fires symmetrically with the buffered list.
    assert len(seen_procs) == len(cap.process_events)

    # File events are parsed by ``parse_strace_file_event_line`` (filesystem.py).
    # We do not assert the exact count to avoid coupling to that parser, but if
    # it fired, the callback must have seen identical objects.
    assert len(seen_files) == len(cap.events)
    cap.stop()


def test_strace_file_event_carries_owning_pid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """File events carry the strace ``[pid N]`` owner; bare lines fall back to root.

    This is the plumbing pid-lineage attribution relies on: each strace file
    event must know which PID performed the syscall so a child-process read can
    later be attributed to the extension that spawned it.
    """
    _patch_pid_resolver(monkeypatch, pid=840)
    stderr_lines = [
        # child pid 4242 reads a workspace file -> pid must be 4242
        '[pid 4242] 1700000002.000 openat(AT_FDCWD, "/workspace/probe.txt", O_RDONLY) = 7\n',
        # a line with no [pid] prefix -> falls back to the attach root pid (840)
        '1700000003.000 openat(AT_FDCWD, "/workspace/root.txt", O_RDONLY) = 8\n',
    ]
    monkeypatch.setattr(
        capture_module.subprocess, "Popen", _make_fake_popen_factory(stderr_lines)
    )

    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    cap.start()
    _wait_for_thread_drain(cap)

    by_path = {event.path: event for event in cap.events}
    assert by_path["/workspace/probe.txt"].pid == 4242
    assert by_path["/workspace/root.txt"].pid == 840
    cap.stop()


def test_strace_cmd_has_volume_flags_without_widening_trace_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Volume control (-qq, signal=none) is applied; the syscall set is not
    widened (brief §8) and no status filter drops failed (recon) syscalls."""
    _patch_pid_resolver(monkeypatch, pid=4242)
    monkeypatch.setattr(
        capture_module.subprocess, "Popen", _make_fake_popen_factory([])
    )

    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    cap.start()
    _wait_for_thread_drain(cap)

    cmd = cap._proc.cmd
    assert "-qq" in cmd
    assert "signal=none" in cmd
    # The trace= syscall set must stay byte-identical (no widening).
    trace_arg = next(arg for arg in cmd if arg.startswith("trace="))
    assert trace_arg == (
        "trace=open,openat,creat,unlink,unlinkat,rename,renameat,"
        "renameat2,mkdir,rmdir,newfstatat,readlink,execve,execveat,"
        "clone,clone3,fork,vfork,chdir"
    )
    # Failed syscalls (e.g. a probe of ~/.ssh/id_rsa) must NOT be dropped.
    assert not any("status=" in arg for arg in cmd)
    assert "-p" in cmd and str(4242) in cmd
    cap.stop()


def test_extension_host_file_capture_stop_joins_thread_and_returns_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``stop()`` returns the buffered FileEvent list and leaves the thread joined."""
    _patch_pid_resolver(monkeypatch, pid=100)
    monkeypatch.setattr(
        capture_module.subprocess, "Popen", _make_fake_popen_factory([])
    )

    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    cap.start()
    _wait_for_thread_drain(cap)
    returned = cap.stop()

    assert returned == cap.events
    assert isinstance(returned, list)
    # After stop(), the reader thread must have exited.
    assert cap._reader is None or not cap._reader.is_alive()


def test_extension_host_file_capture_handles_missing_strace_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``FileNotFoundError`` from Popen marks the capture as failed cleanly."""
    _patch_pid_resolver(monkeypatch, pid=100)

    def _raise_missing(*_args: Any, **_kwargs: Any) -> None:
        raise FileNotFoundError("strace not found")

    monkeypatch.setattr(capture_module.subprocess, "Popen", _raise_missing)

    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    cap.start()

    assert cap.start_error == "strace binary not available in executor container."
    assert cap.diagnostics["status"] == "failed"
    assert cap.diagnostics["failure_reason"] == cap.start_error
    # No reader thread ever started, so stop() must still be a no-op.
    assert cap.stop() == []


def test_extension_host_file_capture_marks_failed_when_pid_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the monitor cannot resolve the Extension Host PID, start() bails cleanly."""
    failure_diagnostics = {
        "attempts": 5,
        "selected_pid": None,
        "status": "planned",
        "poll_timeout_s": 10.0,
        "poll_interval_s": 0.5,
        "failure_reason": "",
    }
    _patch_pid_resolver(monkeypatch, pid=None, diagnostics=failure_diagnostics)

    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    cap.start()

    assert cap.pid is None
    assert "Extension Host PID not found" in cap.start_error
    assert cap.diagnostics["status"] == "failed"
    assert cap.diagnostics["failure_reason"] == cap.start_error
    assert cap.attach_attempts == 5
