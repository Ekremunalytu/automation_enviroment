"""
Tests for scanner/executor.py
==============================

Unit tests for Docker exec wrapper functions.
All subprocess calls are mocked — no Docker daemon required.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scanner.executor import (
    ExecutorError,
    _docker_exec,
    _docker_exec_allow_partial,
    install_extension_in_executor,
    reload_vscode_window,
    reset_executor_sandbox_state,
    run_playwright_automation,
)

# ---------------------------------------------------------------------------
# _docker_exec
# ---------------------------------------------------------------------------


@patch("scanner.executor.subprocess.run")
def test_docker_exec_success(mock_run: MagicMock) -> None:
    """Successful command returns CompletedProcess."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="ok\n", stderr=""
    )

    result = _docker_exec(["echo", "hello"])

    assert result.stdout == "ok\n"
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0:2] == ["docker", "exec"]
    # PYTHONUNBUFFERED=1 should be passed as env flag
    assert "-e" in call_args
    assert "PYTHONUNBUFFERED=1" in call_args
    assert "echo" in call_args
    assert "hello" in call_args


@patch("scanner.executor.subprocess.run")
def test_docker_exec_nonzero_exit(mock_run: MagicMock) -> None:
    """Non-zero exit code raises ExecutorError."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="command not found"
    )

    with pytest.raises(ExecutorError) as exc_info:
        _docker_exec(["bad-command"])

    assert exc_info.value.returncode == 1
    assert "command not found" in exc_info.value.output


@patch("scanner.executor.subprocess.run")
def test_docker_exec_timeout(mock_run: MagicMock) -> None:
    """Timeout raises ExecutorError."""
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)

    with pytest.raises(ExecutorError) as exc_info:
        _docker_exec(["long-running"], timeout=10)

    assert "timed out" in str(exc_info.value).lower()
    assert exc_info.value.returncode is None


# ---------------------------------------------------------------------------
# install_extension_in_executor
# ---------------------------------------------------------------------------


@patch("scanner.executor._docker_exec")
def test_install_extension_success(mock_exec: MagicMock) -> None:
    """Successful install returns stdout."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Extension 'test.ext' was successfully installed.",
        stderr="",
    )

    output = install_extension_in_executor("pub", "ext", "1.0.0")

    assert "successfully installed" in output
    call_cmd = mock_exec.call_args[0][0]
    assert "code" in call_cmd
    assert "--install-extension" in call_cmd
    assert any("pub.ext-1.0.0.vsix" in arg for arg in call_cmd)


@patch("scanner.executor._docker_exec")
def test_install_extension_failure(mock_exec: MagicMock) -> None:
    """ExecutorError propagates from _docker_exec."""
    mock_exec.side_effect = ExecutorError("Install failed", returncode=1, output="err")

    with pytest.raises(ExecutorError):
        install_extension_in_executor("pub", "ext", "1.0.0")


# ---------------------------------------------------------------------------
# run_playwright_automation
# ---------------------------------------------------------------------------


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_success(mock_exec: MagicMock) -> None:
    """Successful automation returns stdout; default scenario is coding_session."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Report written.", stderr=""
    )

    output = run_playwright_automation("/results/report.json")

    assert "Report written" in output
    call_cmd = mock_exec.call_args[0][0]
    assert "python3" in call_cmd
    assert "--monitor" in call_cmd
    assert "--report-path" in call_cmd
    assert "/results/report.json" in call_cmd
    # Default scenario should be coding_session
    assert "--scenario" in call_cmd
    assert "coding_session" in call_cmd


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_with_scenario(mock_exec: MagicMock) -> None:
    """Explicit scenario argument is passed to entrypoint."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation("/results/r.json", scenario="basic")

    call_cmd = mock_exec.call_args[0][0]
    assert "--scenario" in call_cmd
    assert "basic" in call_cmd


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_all_scenarios(mock_exec: MagicMock) -> None:
    """Passing scenario='all' runs every scenario (no --scenario flag)."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation("/results/r.json", scenario="all")

    call_cmd = mock_exec.call_args[0][0]
    assert "--scenario" not in call_cmd


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_with_reload_before_run(mock_exec: MagicMock) -> None:
    """Reload flag is forwarded to the executor entrypoint."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation("/results/r.json", reload_before_run=True)

    call_cmd = mock_exec.call_args[0][0]
    assert "--reload-before-run" in call_cmd


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_with_trigger_payload(mock_exec: MagicMock) -> None:
    """Trigger payload uses --triggers and skips explicit scenario selection."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation(
        "/results/r.json",
        scenario="ignored",
        trigger_container_path="/results/triggers.json",
    )

    call_cmd = mock_exec.call_args[0][0]
    assert "--triggers" in call_cmd
    assert "/results/triggers.json" in call_cmd
    assert "--scenario" not in call_cmd


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_partial_failure(mock_exec: MagicMock) -> None:
    """Non-zero exit code is tolerated (report may still be written)."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="Report written.\nSome scenarios failed.",
        stderr="",
    )

    output = run_playwright_automation("/results/r.json")
    assert "Report written" in output


@patch("scanner.executor._docker_exec_allow_partial")
def test_run_automation_timeout(mock_exec: MagicMock) -> None:
    """Timeout still raises ExecutorError."""
    mock_exec.side_effect = ExecutorError("Timed out", returncode=None, output="")

    with pytest.raises(ExecutorError):
        run_playwright_automation("/results/r.json")


# ---------------------------------------------------------------------------
# _docker_exec_allow_partial
# ---------------------------------------------------------------------------


@patch("scanner.executor.subprocess.run")
def test_docker_exec_allow_partial_nonzero(mock_run: MagicMock) -> None:
    """Non-zero exit code does NOT raise ExecutorError."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="partial", stderr=""
    )

    result = _docker_exec_allow_partial(["some-cmd"])
    assert result.returncode == 1
    assert result.stdout == "partial"


@patch("scanner.executor.subprocess.run")
def test_docker_exec_allow_partial_timeout(mock_run: MagicMock) -> None:
    """Timeout raises ExecutorError even in partial mode."""
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)

    with pytest.raises(ExecutorError):
        _docker_exec_allow_partial(["slow-cmd"], timeout=10)


# ---------------------------------------------------------------------------
# reload_vscode_window
# ---------------------------------------------------------------------------


@patch("scanner.executor._docker_exec")
def test_reload_vscode_window_success(mock_exec: MagicMock) -> None:
    """Successful reload returns stdout."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="[reload] Done\n", stderr=""
    )

    output = reload_vscode_window()

    assert "Done" in output
    call_cmd = mock_exec.call_args[0][0]
    assert "python3" in call_cmd
    assert "reload_vscode.py" in call_cmd[-1]


@patch("scanner.executor._docker_exec")
def test_reload_vscode_window_timeout(mock_exec: MagicMock) -> None:
    """Timeout during reload raises ExecutorError."""
    mock_exec.side_effect = ExecutorError(
        "Command timed out after 60s", returncode=None, output=""
    )

    with pytest.raises(ExecutorError):
        reload_vscode_window()


# ---------------------------------------------------------------------------
# reset_executor_sandbox_state
# ---------------------------------------------------------------------------


@patch("scanner.executor.reload_vscode_window")
@patch("scanner.executor._docker_exec")
def test_reset_executor_sandbox_state_with_reload(
    mock_exec: MagicMock,
    mock_reload: MagicMock,
) -> None:
    """Reset clears sandbox state and reloads VS Code by default."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="[reset] sandbox ready",
        stderr="",
    )
    mock_reload.return_value = "[reload] Done"

    output = reset_executor_sandbox_state()

    assert "[reset] sandbox ready" in output
    assert "[reload] Done" in output
    call_cmd = mock_exec.call_args[0][0]
    assert call_cmd[0] == "python3"
    assert "reset_state.py" in call_cmd[-1]
    mock_reload.assert_called_once_with()


@patch("scanner.executor.reload_vscode_window")
@patch("scanner.executor._docker_exec")
def test_reset_executor_sandbox_state_without_reload(
    mock_exec: MagicMock,
    mock_reload: MagicMock,
) -> None:
    """Reset can skip the VS Code reload when requested."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="[reset] sandbox ready",
        stderr="",
    )

    output = reset_executor_sandbox_state(reload_window=False)

    assert output == "[reset] sandbox ready"
    mock_reload.assert_not_called()
