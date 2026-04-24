from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import reset_state  # noqa: E402


def _stub_vscode_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralise real VS Code process/socket side effects for the FS tests."""
    monkeypatch.setattr(reset_state, "terminate_vscode", lambda: [])
    monkeypatch.setattr(reset_state, "cleanup_singleton_locks", lambda: 0)
    monkeypatch.setattr(reset_state, "launch_vscode", lambda: None)


def test_reset_executor_state_clears_extensions_and_logs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    extensions_dir = tmp_path / "extensions"
    logs_dir = tmp_path / "logs"
    workspace_dir = tmp_path / "workspace"

    extensions_dir.mkdir()
    logs_dir.mkdir()
    workspace_dir.mkdir()

    (extensions_dir / "old-extension").mkdir()
    (extensions_dir / "note.txt").write_text("leftover")
    (logs_dir / "session-1").mkdir()
    (logs_dir / "latest").symlink_to(logs_dir / "session-1", target_is_directory=True)

    call_order: list[str] = []

    def fake_clean_workspace() -> None:
        call_order.append("clean")
        (workspace_dir / "scratch.txt").write_text("temp")

    def fake_setup_dev_environment() -> None:
        call_order.append("setup")
        (workspace_dir / "seed.txt").write_text("restored")

    monkeypatch.setattr(reset_state, "EXTENSIONS_DIR", extensions_dir)
    monkeypatch.setattr(reset_state, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(reset_state.workspace, "WORKSPACE_DIR", workspace_dir)
    monkeypatch.setattr(reset_state.workspace, "clean_workspace", fake_clean_workspace)
    monkeypatch.setattr(
        reset_state.workspace,
        "setup_dev_environment",
        fake_setup_dev_environment,
    )
    _stub_vscode_lifecycle(monkeypatch)

    summary = reset_state.reset_executor_state()

    assert summary["removed_extensions"] == 2
    assert summary["removed_logs"] == 2
    assert summary["terminated_vscode_processes"] == 0
    assert summary["removed_singleton_locks"] == 0
    assert summary["relaunched_vscode_pid"] == 0
    assert call_order == ["clean", "setup"]
    assert sorted(path.name for path in extensions_dir.iterdir()) == []
    assert sorted(path.name for path in logs_dir.iterdir()) == []
    assert (workspace_dir / "seed.txt").read_text() == "restored"


def test_terminate_vscode_returns_empty_when_no_process_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")

    monkeypatch.setattr(reset_state.subprocess, "run", fake_run)
    assert reset_state.terminate_vscode() == []


def test_terminate_vscode_sigterms_live_processes_then_returns_pids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signals_sent: list[tuple[int, int]] = []
    alive_calls: list[int] = []

    def fake_find() -> list[int]:
        return [111, 222]

    def fake_send(pid: int, sig: signal.Signals) -> None:
        signals_sent.append((pid, int(sig)))

    def fake_alive(pid: int) -> bool:
        alive_calls.append(pid)
        return False

    monkeypatch.setattr(reset_state, "_find_vscode_pids", fake_find)
    monkeypatch.setattr(reset_state, "_send_signal", fake_send)
    monkeypatch.setattr(reset_state, "_process_alive", fake_alive)
    monkeypatch.setattr(reset_state.time, "sleep", lambda _seconds: None)

    result = reset_state.terminate_vscode(grace_seconds=0.01, poll_interval=0.001)

    assert result == [111, 222]
    assert signals_sent == [(111, int(signal.SIGTERM)), (222, int(signal.SIGTERM))]
    assert set(alive_calls) == {111, 222}


def test_terminate_vscode_escalates_to_sigkill_when_processes_survive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signals_sent: list[tuple[int, int]] = []
    alive_sequence = [True, True, True, True, True, True]

    def fake_find() -> list[int]:
        return [333]

    def fake_send(pid: int, sig: signal.Signals) -> None:
        signals_sent.append((pid, int(sig)))

    def fake_alive(pid: int) -> bool:
        if alive_sequence:
            return alive_sequence.pop(0)
        return True

    monkeypatch.setattr(reset_state, "_find_vscode_pids", fake_find)
    monkeypatch.setattr(reset_state, "_send_signal", fake_send)
    monkeypatch.setattr(reset_state, "_process_alive", fake_alive)
    monkeypatch.setattr(reset_state.time, "sleep", lambda _seconds: None)

    reset_state.terminate_vscode(grace_seconds=0.01, poll_interval=0.001)

    sigs = [sig for _, sig in signals_sent]
    assert int(signal.SIGTERM) in sigs
    assert int(signal.SIGKILL) in sigs


def test_cleanup_singleton_locks_removes_known_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "Code"
    config_dir.mkdir()
    (config_dir / "SingletonLock").write_text("")
    (config_dir / "SingletonCookie").write_text("")
    (config_dir / "SingletonSocket").write_text("")
    (config_dir / "unrelated.txt").write_text("keep")

    monkeypatch.setattr(reset_state, "CHROMIUM_CONFIG_DIR", config_dir)

    removed = reset_state.cleanup_singleton_locks()

    assert removed == 3
    remaining = sorted(p.name for p in config_dir.iterdir())
    assert remaining == ["unrelated.txt"]


def test_cleanup_singleton_locks_noop_when_dir_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr(reset_state, "CHROMIUM_CONFIG_DIR", missing)
    assert reset_state.cleanup_singleton_locks() == 0


def test_cleanup_singleton_locks_ignores_partial_file_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "Code"
    config_dir.mkdir()
    (config_dir / "SingletonLock").write_text("")

    monkeypatch.setattr(reset_state, "CHROMIUM_CONFIG_DIR", config_dir)

    assert reset_state.cleanup_singleton_locks() == 1


def test_launch_vscode_returns_pid_from_script_stdout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    script_path = tmp_path / "launch_vscode.sh"
    script_path.write_text("#!/bin/bash\necho 4242\n")
    script_path.chmod(0o755)
    monkeypatch.setattr(reset_state, "_VSCODE_LAUNCH_SCRIPT", script_path)

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(
            cmd, returncode=0, stdout="4242\n", stderr=""
        )

    monkeypatch.setattr(reset_state.subprocess, "run", fake_run)

    assert reset_state.launch_vscode() == 4242


def test_launch_vscode_returns_none_when_script_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(reset_state, "_VSCODE_LAUNCH_SCRIPT", tmp_path / "missing.sh")
    assert reset_state.launch_vscode() is None


def test_launch_vscode_returns_none_when_script_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    script_path = tmp_path / "launch_vscode.sh"
    script_path.write_text("#!/bin/bash\nexit 1\n")
    script_path.chmod(0o755)
    monkeypatch.setattr(reset_state, "_VSCODE_LAUNCH_SCRIPT", script_path)

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")

    monkeypatch.setattr(reset_state.subprocess, "run", fake_run)

    assert reset_state.launch_vscode() is None


def test_reset_executor_state_orchestrates_restart_in_correct_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    extensions_dir = tmp_path / "extensions"
    logs_dir = tmp_path / "logs"
    workspace_dir = tmp_path / "workspace"
    extensions_dir.mkdir()
    logs_dir.mkdir()
    workspace_dir.mkdir()
    (extensions_dir / "stale").mkdir()

    events: list[str] = []

    def record(name: str, ret):  # type: ignore[no-untyped-def]
        def fn(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            events.append(name)
            return ret

        return fn

    monkeypatch.setattr(reset_state, "EXTENSIONS_DIR", extensions_dir)
    monkeypatch.setattr(reset_state, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(reset_state.workspace, "WORKSPACE_DIR", workspace_dir)
    monkeypatch.setattr(
        reset_state.workspace, "clean_workspace", record("clean_workspace", None)
    )
    monkeypatch.setattr(
        reset_state.workspace,
        "setup_dev_environment",
        record("setup_dev_environment", None),
    )
    monkeypatch.setattr(
        reset_state, "terminate_vscode", record("terminate_vscode", [123])
    )
    monkeypatch.setattr(
        reset_state, "cleanup_singleton_locks", record("cleanup_singleton_locks", 2)
    )
    monkeypatch.setattr(reset_state, "launch_vscode", record("launch_vscode", 555))

    summary = reset_state.reset_executor_state()

    assert events.index("terminate_vscode") < events.index("cleanup_singleton_locks")
    assert events.index("cleanup_singleton_locks") < events.index("launch_vscode")
    assert events.index("clean_workspace") < events.index("terminate_vscode")
    assert summary["terminated_vscode_processes"] == 1
    assert summary["removed_singleton_locks"] == 2
    assert summary["relaunched_vscode_pid"] == 555
