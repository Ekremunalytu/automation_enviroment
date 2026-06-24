from __future__ import annotations

import signal
import subprocess
from pathlib import Path

import pytest

from executor.flows.playwright import reset_state


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
    monkeypatch.setattr(reset_state, "_process_tree", lambda roots, table=None: roots)
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
    monkeypatch.setattr(reset_state, "_process_tree", lambda roots, table=None: roots)
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


def test_reset_executor_state_recovers_from_held_singleton_locks_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """W13-10 — stale singleton-lock recovery integration test.

    Existing unit cases at lines 137-176 cover ``cleanup_singleton_locks()``
    in isolation; the orchestration case at lines 223-270 stubs
    ``cleanup_singleton_locks`` and only asserts call ordering.

    Neither exercises the *integration*: a previous VS Code session
    crashed leaving all three Chromium singleton sentinels in place,
    ``reset_executor_state()`` runs end-to-end, and the lock files
    actually disappear from the filesystem while the rest of the
    reset pipeline still completes normally.

    Without this gate, a future regression that stubs out
    ``cleanup_singleton_locks`` inside ``reset_executor_state`` (or
    accidentally skips the call) would leave a stuck VS Code that
    refuses to relaunch. Failure mode is silent at unit-test level
    because the orchestration test only checks call ordering against
    stubs.
    """
    extensions_dir = tmp_path / "extensions"
    logs_dir = tmp_path / "logs"
    workspace_dir = tmp_path / "workspace"
    config_dir = tmp_path / "Code"
    extensions_dir.mkdir()
    logs_dir.mkdir()
    workspace_dir.mkdir()
    config_dir.mkdir()

    (extensions_dir / "leftover-extension").mkdir()
    (logs_dir / "stale-session").mkdir()

    (config_dir / "SingletonLock").write_text("")
    (config_dir / "SingletonCookie").write_text("")
    (config_dir / "SingletonSocket").write_text("")
    (config_dir / "Preferences").write_text("keep me")

    monkeypatch.setattr(reset_state, "EXTENSIONS_DIR", extensions_dir)
    monkeypatch.setattr(reset_state, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(reset_state, "CHROMIUM_CONFIG_DIR", config_dir)
    monkeypatch.setattr(reset_state.workspace, "WORKSPACE_DIR", workspace_dir)
    monkeypatch.setattr(reset_state.workspace, "clean_workspace", lambda: None)
    monkeypatch.setattr(reset_state.workspace, "setup_dev_environment", lambda: None)
    monkeypatch.setattr(reset_state, "terminate_vscode", lambda: [])
    monkeypatch.setattr(reset_state, "launch_vscode", lambda: 9999)

    summary = reset_state.reset_executor_state()

    assert summary["removed_singleton_locks"] == 3
    assert summary["removed_extensions"] == 1
    assert summary["removed_logs"] == 1
    assert summary["relaunched_vscode_pid"] == 9999

    remaining = sorted(p.name for p in config_dir.iterdir())
    assert remaining == ["Preferences"], (
        f"Expected only ['Preferences'] to survive cleanup, found {remaining}. "
        "All three Chromium singleton sentinels must be removed by "
        "reset_executor_state() so the next launch_vscode() does not bail "
        "out with a stuck-lock error."
    )


def test_reset_executor_state_recovery_handles_partial_singleton_lock_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """W13-10 — recovery is robust when only some singleton files exist.

    A crash may leave only one or two of the three sentinels behind
    (Chromium writes them in a specific order). Recovery must still
    succeed end-to-end: the present sentinels are removed, the absent
    ones do not cause an error, and the reset pipeline completes
    normally with the partial removed-count reflected in the summary.
    """
    extensions_dir = tmp_path / "extensions"
    logs_dir = tmp_path / "logs"
    workspace_dir = tmp_path / "workspace"
    config_dir = tmp_path / "Code"
    extensions_dir.mkdir()
    logs_dir.mkdir()
    workspace_dir.mkdir()
    config_dir.mkdir()

    (config_dir / "SingletonLock").write_text("")
    (config_dir / "SingletonSocket").write_text("")

    monkeypatch.setattr(reset_state, "EXTENSIONS_DIR", extensions_dir)
    monkeypatch.setattr(reset_state, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(reset_state, "CHROMIUM_CONFIG_DIR", config_dir)
    monkeypatch.setattr(reset_state.workspace, "WORKSPACE_DIR", workspace_dir)
    monkeypatch.setattr(reset_state.workspace, "clean_workspace", lambda: None)
    monkeypatch.setattr(reset_state.workspace, "setup_dev_environment", lambda: None)
    monkeypatch.setattr(reset_state, "terminate_vscode", lambda: [])
    monkeypatch.setattr(reset_state, "launch_vscode", lambda: 1234)

    summary = reset_state.reset_executor_state()

    assert summary["removed_singleton_locks"] == 2
    assert summary["relaunched_vscode_pid"] == 1234
    assert sorted(p.name for p in config_dir.iterdir()) == []


# ---------------------------------------------------------------------------
# B2 / reliability-multi-analyze: same-container reset must actually reap the
# previous VS Code process tree. Regressions guarded below:
#   1. the pgrep call passes `--` so the `--`-prefixed needle is a pattern,
#      not an unknown option (the root cause: terminate silently no-op'd);
#   2. the needle is CDP-independent (works in the CDP-off Podman deploy);
#   3. terminate walks the PPID tree so the orphan-prone integrated-terminal
#      shells are reaped, not left to accumulate across analyses.
# ---------------------------------------------------------------------------


def test_find_vscode_pids_passes_separator_so_needle_is_a_pattern(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: ``pgrep -f`` must receive ``--`` before the needle.

    Without it, ``pgrep -f --extensionDevelopmentPath`` parses the pattern as
    an unknown option (exit 2) and ``_find_vscode_pids`` returns ``[]``, so
    ``terminate_vscode`` silently no-ops in EVERY config — the proven root
    cause of the 2nd-analyze sandbox-reset failure.
    """
    captured: dict[str, list[str]] = {}

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="101\n", stderr="")

    monkeypatch.setattr(reset_state.subprocess, "run", fake_run)

    assert reset_state._find_vscode_pids() == [101]

    cmd = captured["cmd"]
    assert "--" in cmd, f"pgrep call must include the `--` separator: {cmd}"
    assert cmd.index("--") < cmd.index(reset_state._VSCODE_PROCESS_NEEDLE), (
        "the needle must come AFTER `--` so pgrep treats it as a pattern"
    )


def test_vscode_needle_is_cdp_independent() -> None:
    """The needle must not depend on the opt-in CDP flag, which is absent in
    the CDP-off Podman/air-gapped deploy (``-e EXECUTOR_CDP_PORT=``)."""
    assert "remote-debugging-port" not in reset_state._VSCODE_PROCESS_NEEDLE
    assert reset_state._VSCODE_PROCESS_NEEDLE == "--extensionDevelopmentPath"


def test_process_tree_reaps_main_and_descendant_terminals() -> None:
    """The PPID walk must reach the integrated-terminal shells.

    Modelled on a live executor snapshot: main(101) -> node-utility(2104) ->
    two bash terminals (2127, 2257). The terminals ``setsid`` into their own
    sessions, so a process-group kill of 101 would miss them; the tree walk
    catches them. Unrelated PID 999 must NOT be included.
    """
    table = [
        (101, 1),  # main VS Code
        (103, 101),  # zygote child
        (2104, 101),  # node utility child
        (2127, 2104),  # bash terminal (own session in reality)
        (2257, 2104),  # bash terminal
        (999, 1),  # unrelated process
    ]

    tree = reset_state._process_tree([101], table=table)

    assert tree[0] == 101, "root must come first"
    assert set(tree) == {101, 103, 2104, 2127, 2257}
    assert 999 not in tree


def test_read_proc_table_parses_ppid_after_complex_comm(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``/proc/<pid>/stat`` ``comm`` can contain spaces and parentheses, so the
    ppid must be parsed from the fields AFTER the final ')'."""
    proc = tmp_path / "proc"
    proc.mkdir()
    (proc / "101").mkdir()
    (proc / "101" / "stat").write_text("101 (code) S 1 101 101 0 -1 4194560 0\n")
    (proc / "2127").mkdir()
    # comm itself contains spaces and an extra ')'
    (proc / "2127" / "stat").write_text("2127 (bash (login) x) S 2104 2127 2127 0\n")
    (proc / "self").mkdir()  # non-numeric entry must be ignored
    (proc / "self" / "stat").write_text("garbage line without parens\n")

    monkeypatch.setattr(reset_state, "_PROC_ROOT", proc)

    table = dict(reset_state._read_proc_table())

    assert table[101] == 1
    assert table[2127] == 2104  # ppid correct despite parens/spaces in comm
    assert len(table) == 2  # "self" skipped by the isdigit() filter


def test_terminate_vscode_signals_entire_process_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """terminate_vscode must SIGTERM the main process AND its descendants
    (the orphan-prone terminals), not just the pgrep-matched root."""
    signalled: list[int] = []

    monkeypatch.setattr(reset_state, "_find_vscode_pids", lambda: [101])
    monkeypatch.setattr(
        reset_state,
        "_read_proc_table",
        lambda: [(101, 1), (2104, 101), (2127, 2104), (2257, 2104), (999, 1)],
    )
    monkeypatch.setattr(
        reset_state, "_send_signal", lambda pid, sig: signalled.append(pid)
    )
    monkeypatch.setattr(reset_state, "_process_alive", lambda _pid: False)
    monkeypatch.setattr(reset_state.time, "sleep", lambda _seconds: None)

    result = reset_state.terminate_vscode(grace_seconds=0.01, poll_interval=0.001)

    assert set(result) == {101, 2104, 2127, 2257}
    assert set(signalled) == {101, 2104, 2127, 2257}
    assert 999 not in signalled  # unrelated process is never touched
