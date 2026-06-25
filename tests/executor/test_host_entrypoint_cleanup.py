"""Regression: stale-entrypoint cleanup must escalate SIGTERM -> SIGKILL.

A timed-out / wedged analyze entrypoint installs a SIGTERM handler
(``entrypoint/__main__.py``) that turns the first SIGTERM into a SystemExit
graceful unwind. That SystemExit is only raised between bytecode ops, so an
entrypoint stuck in a CPU-bound C call (slow report-build on a large extension
like GitHub.copilot-chat) ignores the first SIGTERM and keeps burning CPU,
holding the single-active sandbox past the automation timeout. The cleanup must
therefore SIGTERM, grant a bounded grace, then SIGKILL the survivor — and must
NOT pay that grace delay when nothing was running.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from executor import host as host_module


def test_cleanup_escalates_to_sigkill_when_entrypoint_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    sleeps: list[float] = []

    def fake_exec(cmd, timeout=None, **_kwargs):  # type: ignore[no-untyped-def]
        calls.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")  # matched

    monkeypatch.setattr(host_module, "_docker_exec_allow_partial", fake_exec)
    monkeypatch.setattr(host_module.time, "sleep", lambda s: sleeps.append(s))

    host_module._cleanup_stale_entrypoint_processes()

    signals = [cmd[1] for cmd in calls]
    assert signals == ["-TERM", "-KILL"], (
        f"a running entrypoint must be SIGTERM'd then SIGKILL'd, got {signals}"
    )
    assert all("-f" in cmd for cmd in calls), "both pkills must full-match the module"
    assert all(host_module.settings.executor.ENTRYPOINT_MODULE in cmd for cmd in calls)
    assert sleeps == [host_module._ENTRYPOINT_TERM_GRACE_SECONDS], (
        "must grant exactly one grace window between SIGTERM and SIGKILL"
    )


def test_cleanup_no_escalation_when_nothing_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    sleeps: list[float] = []

    def fake_exec(cmd, timeout=None, **_kwargs):  # type: ignore[no-untyped-def]
        calls.append(list(cmd))
        return SimpleNamespace(returncode=1, stdout="", stderr="")  # no match

    monkeypatch.setattr(host_module, "_docker_exec_allow_partial", fake_exec)
    monkeypatch.setattr(host_module.time, "sleep", lambda s: sleeps.append(s))

    host_module._cleanup_stale_entrypoint_processes()

    signals = [cmd[1] for cmd in calls]
    assert signals == ["-TERM"], (
        f"no SIGKILL escalation when nothing matched, got {signals}"
    )
    assert sleeps == [], "no grace delay when no entrypoint was running"


def test_cleanup_swallows_executor_error_on_first_pkill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed cleanup pkill must not propagate (best-effort recovery)."""
    sleeps: list[float] = []

    def fake_exec(cmd, timeout=None, **_kwargs):  # type: ignore[no-untyped-def]
        raise host_module.ExecutorError("pkill unavailable", returncode=None)

    monkeypatch.setattr(host_module, "_docker_exec_allow_partial", fake_exec)
    monkeypatch.setattr(host_module.time, "sleep", lambda s: sleeps.append(s))

    # Must not raise.
    host_module._cleanup_stale_entrypoint_processes()
    assert sleeps == []
