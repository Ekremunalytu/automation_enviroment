"""Unit tests for executor/host.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import executor.config as executor_config
from executor.host import (
    ExecutorError,
    _cleanup_stale_reload_processes,
    _docker_exec,
    _docker_exec_allow_partial,
    cleanup_trigger_file,
    install_extension_in_executor,
    reload_vscode_window,
    reset_executor_sandbox_state,
    run_playwright_automation,
)

# ---------------------------------------------------------------------------
# _docker_exec
# ---------------------------------------------------------------------------


@patch("executor.host.subprocess.run")
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


@patch("executor.host.subprocess.run")
def test_docker_exec_nonzero_exit(mock_run: MagicMock) -> None:
    """Non-zero exit code raises ExecutorError."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="command not found"
    )

    with pytest.raises(ExecutorError) as exc_info:
        _docker_exec(["bad-command"])

    assert exc_info.value.returncode == 1
    assert "command not found" in exc_info.value.output


@patch("executor.host.subprocess.run")
def test_docker_exec_timeout(mock_run: MagicMock) -> None:
    """Timeout raises ExecutorError."""
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)

    with pytest.raises(ExecutorError) as exc_info:
        _docker_exec(["long-running"], timeout=10)

    assert "timed out" in str(exc_info.value).lower()
    assert exc_info.value.returncode is None


@patch("executor.host.time.sleep")
@patch("executor.host.subprocess.run")
def test_docker_exec_retries_docker_transport_errors(
    mock_run: MagicMock,
    mock_sleep: MagicMock,
) -> None:
    """Transient docker transport failures retry before succeeding."""
    mock_run.side_effect = [
        subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Cannot connect to the Docker daemon",
        ),
        subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok\n",
            stderr="",
        ),
    ]

    result = _docker_exec(["echo", "hello"])

    assert result.stdout == "ok\n"
    assert mock_run.call_count == 2
    mock_sleep.assert_called_once_with(1)


@patch("executor.host.subprocess.run")
def test_docker_exec_does_not_retry_generic_connection_refused(
    mock_run: MagicMock,
) -> None:
    """Generic app-level connection errors should not be treated as docker transport failures."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr="connection refused",
    )

    with pytest.raises(ExecutorError):
        _docker_exec(["echo", "hello"])

    assert mock_run.call_count == 1


def test_build_settings_reads_dotenv_values_when_env_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Executor config should keep honoring repo-local .env overrides."""
    monkeypatch.delenv("PROJECT_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("EXECUTOR_CONTAINER_NAME", raising=False)
    monkeypatch.setattr(
        executor_config,
        "_dotenv_values",
        lambda: {
            "PROJECT_OUTPUT_DIR": "tmp/output-from-dotenv",
            "EXECUTOR_CONTAINER_NAME": "executor-from-dotenv",
        },
    )

    settings = executor_config.build_settings()

    assert settings.project.OUTPUT_DIR == "tmp/output-from-dotenv"
    assert settings.executor.CONTAINER_NAME == "executor-from-dotenv"


# ---------------------------------------------------------------------------
# install_extension_in_executor
# ---------------------------------------------------------------------------


@patch("executor.host._docker_exec")
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


@patch("executor.host._docker_exec")
def test_install_extension_failure(mock_exec: MagicMock) -> None:
    """ExecutorError propagates from _docker_exec."""
    mock_exec.side_effect = ExecutorError("Install failed", returncode=1, output="err")

    with pytest.raises(ExecutorError):
        install_extension_in_executor("pub", "ext", "1.0.0")


# ---------------------------------------------------------------------------
# reload_vscode_window
# ---------------------------------------------------------------------------


@patch("executor.host._cleanup_stale_reload_processes")
@patch("executor.host._docker_exec")
def test_reload_vscode_window_uses_reload_timeout(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Reload wrapper should allow enough time for VS Code teardown/reconnect."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="reloaded",
        stderr="",
    )

    output = reload_vscode_window()

    assert output == "reloaded"
    assert mock_exec.call_args.kwargs["timeout"] == 90
    mock_cleanup.assert_called_once_with()


# ---------------------------------------------------------------------------
# run_playwright_automation
# ---------------------------------------------------------------------------


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_success(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
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
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_with_scenario(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Explicit scenario argument is passed to entrypoint."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation("/results/r.json", scenario="basic")

    call_cmd = mock_exec.call_args[0][0]
    assert "--scenario" in call_cmd
    assert "basic" in call_cmd
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_all_scenarios(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Passing scenario='all' runs every scenario (no --scenario flag)."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation("/results/r.json", scenario="all")

    call_cmd = mock_exec.call_args[0][0]
    assert "--scenario" not in call_cmd
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_with_reload_before_run(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Reload flag is forwarded to the executor entrypoint."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation("/results/r.json", reload_before_run=True)

    call_cmd = mock_exec.call_args[0][0]
    assert "--reload-before-run" in call_cmd
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_with_trigger_payload(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Trigger payload + explicit scenario preserves scenario selection."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation(
        "/results/r.json",
        scenario="coding_session",
        trigger_container_path="/results/triggers.json",
    )

    call_cmd = mock_exec.call_args[0][0]
    assert "--triggers" in call_cmd
    assert "/results/triggers.json" in call_cmd
    assert "--scenario" in call_cmd
    assert "coding_session" in call_cmd
    mock_cleanup.assert_called_once_with("/results/triggers.json")


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_with_trigger_payload_omits_default_scenario(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Layered trigger payloads should not receive an implicit scenario flag."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation(
        "/results/r.json",
        trigger_container_path="/results/triggers.json",
    )

    call_cmd = mock_exec.call_args[0][0]
    assert "--triggers" in call_cmd
    assert "/results/triggers.json" in call_cmd
    assert "--scenario" not in call_cmd
    mock_cleanup.assert_called_once_with("/results/triggers.json")


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_skip_automation_omits_scenarios(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Scenario-zero mode should forward --skip-automation without scenario flags."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done", stderr=""
    )

    run_playwright_automation(
        "/results/r.json",
        skip_automation=True,
        scenario="coding_session",
    )

    call_cmd = mock_exec.call_args[0][0]
    assert "--skip-automation" in call_cmd
    assert "--scenario" not in call_cmd
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_partial_failure_with_report(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
    tmp_path: Path,
) -> None:
    """Non-zero exit code is tolerated (report may still be written)."""
    report_path = tmp_path / "activation_report.json"
    report_path.write_text("{}", encoding="utf-8")
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="Report written.\nSome scenarios failed.",
        stderr="",
    )

    with patch("executor.host._docker_exec_target_path", return_value=report_path):
        output = run_playwright_automation("/results/r.json")

    assert "Report written" in output
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_nonzero_without_report_raises_executor_error(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
    tmp_path: Path,
) -> None:
    """Non-zero exit without a report should fail closed."""
    report_path = tmp_path / "missing_report.json"
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="Traceback: import failed",
        stderr="",
    )

    with (
        patch("executor.host._docker_exec_target_path", return_value=report_path),
        pytest.raises(ExecutorError) as exc_info,
    ):
        run_playwright_automation("/results/r.json")

    assert exc_info.value.returncode == 1
    assert "missing_report.json" in str(exc_info.value)
    assert "import failed" in exc_info.value.output
    mock_cleanup.assert_called_once_with(None)


@patch("executor.host.cleanup_trigger_file")
@patch("executor.host._docker_exec_allow_partial")
def test_run_automation_timeout(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Timeout still raises ExecutorError."""
    mock_exec.side_effect = ExecutorError("Timed out", returncode=None, output="")

    with pytest.raises(ExecutorError):
        run_playwright_automation("/results/r.json")
    mock_cleanup.assert_called_once_with(None)


# ---------------------------------------------------------------------------
# _docker_exec_allow_partial
# ---------------------------------------------------------------------------


@patch("executor.host.subprocess.run")
def test_docker_exec_allow_partial_nonzero(mock_run: MagicMock) -> None:
    """Non-zero exit code does NOT raise ExecutorError."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="partial", stderr=""
    )

    result = _docker_exec_allow_partial(["some-cmd"])
    assert result.returncode == 1
    assert result.stdout == "partial"


@patch("executor.host.subprocess.run")
def test_docker_exec_allow_partial_timeout(mock_run: MagicMock) -> None:
    """Timeout raises ExecutorError even in partial mode."""
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)

    with pytest.raises(ExecutorError):
        _docker_exec_allow_partial(["slow-cmd"], timeout=10)


# ---------------------------------------------------------------------------
# reload_vscode_window
# ---------------------------------------------------------------------------


@patch("executor.host._cleanup_stale_reload_processes")
@patch("executor.host._docker_exec")
def test_reload_vscode_window_success(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Successful reload returns stdout."""
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="[reload] Done\n", stderr=""
    )

    output = reload_vscode_window()

    assert "Done" in output
    call_cmd = mock_exec.call_args[0][0]
    assert "python3" in call_cmd
    assert "reload_vscode.py" in call_cmd[-1]
    mock_cleanup.assert_called_once_with()


@patch("executor.host._cleanup_stale_reload_processes")
@patch("executor.host._docker_exec")
def test_reload_vscode_window_timeout(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    """Timeout during reload raises ExecutorError with phase context."""
    mock_exec.side_effect = ExecutorError(
        "Command timed out after 60s",
        returncode=None,
        output="[reload] reconnect: Reconnecting to a ready VS Code workbench...\n",
    )

    with pytest.raises(
        ExecutorError,
        match="last reload output: \\[reload\\] reconnect: Reconnecting to a ready VS Code workbench",
    ):
        reload_vscode_window()
    assert mock_cleanup.call_count == 2


@patch("executor.host._cleanup_stale_reload_processes")
@patch("executor.host._docker_exec")
def test_reload_vscode_window_nonzero_exit_surfaces_script_error(
    mock_exec: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    mock_exec.side_effect = ExecutorError(
        "Command failed (rc=1): python3 /home/executor/flows/playwright/reload_vscode.py",
        returncode=1,
        output=(
            "[reload] post_settle: Waiting 5000ms for extensions to settle after reload...\n"
            "[reload] ERROR reconnect: Timed out while reconnecting to a VS Code workbench page.\n"
        ),
    )

    with pytest.raises(
        ExecutorError,
        match="last reload output: \\[reload\\] ERROR reconnect: Timed out while reconnecting to a VS Code workbench page\\.",
    ):
        reload_vscode_window()
    assert mock_cleanup.call_count == 2


@patch("executor.host._docker_exec_allow_partial")
def test_cleanup_stale_reload_processes_ignores_missing_processes(
    mock_exec: MagicMock,
) -> None:
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr="",
    )

    _cleanup_stale_reload_processes()

    mock_exec.assert_called_once()
    call_cmd = mock_exec.call_args[0][0]
    assert call_cmd == [
        "pkill",
        "-f",
        "/home/executor/flows/playwright/reload_vscode.py",
    ]
    assert mock_exec.call_args.kwargs["timeout"] == 5


@patch("executor.host._docker_exec_allow_partial")
def test_cleanup_trigger_file_removes_host_and_container_artifacts(
    mock_exec: MagicMock,
    tmp_path: Path,
) -> None:
    host_trigger = tmp_path / "triggers.json"
    host_trigger.write_text("{}", encoding="utf-8")

    with patch("executor.host._docker_exec_target_path", return_value=host_trigger):
        cleanup_trigger_file("/results/triggers.json")

    assert not host_trigger.exists()
    mock_exec.assert_called_once_with(["rm", "-f", "/results/triggers.json"], timeout=5)


# ---------------------------------------------------------------------------
# reset_executor_sandbox_state
# ---------------------------------------------------------------------------


@patch("executor.host.reload_vscode_window")
@patch("executor.host._docker_exec")
@patch("executor.host._docker_exec_allow_partial")
def test_reset_executor_sandbox_state_with_reload(
    mock_exec_allow_partial: MagicMock,
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
    mock_exec_allow_partial.assert_called_once_with(
        ["pkill", "-f", "/home/executor/flows/playwright/entrypoint.py"],
        timeout=5,
    )
    mock_reload.assert_called_once_with()


@patch("executor.host.time.sleep")
@patch("executor.host.reload_vscode_window")
@patch("executor.host._docker_exec")
@patch("executor.host._docker_exec_allow_partial")
def test_reset_executor_sandbox_state_retries_reload_once(
    mock_exec_allow_partial: MagicMock,
    mock_exec: MagicMock,
    mock_reload: MagicMock,
    mock_sleep: MagicMock,
) -> None:
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="[reset] sandbox ready",
        stderr="",
    )
    mock_reload.side_effect = [
        ExecutorError("reload failed", returncode=1, output="boom"),
        "[reload] Done",
    ]

    output = reset_executor_sandbox_state()

    assert "[reset] sandbox ready" in output
    assert "[reload] Done" in output
    mock_exec_allow_partial.assert_called_once_with(
        ["pkill", "-f", "/home/executor/flows/playwright/entrypoint.py"],
        timeout=5,
    )
    mock_sleep.assert_called_once_with(2)
    assert mock_reload.call_count == 2


@patch("executor.host.reload_vscode_window")
@patch("executor.host._docker_exec")
@patch("executor.host._docker_exec_allow_partial")
def test_reset_executor_sandbox_state_without_reload(
    mock_exec_allow_partial: MagicMock,
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
    mock_exec_allow_partial.assert_called_once_with(
        ["pkill", "-f", "/home/executor/flows/playwright/entrypoint.py"],
        timeout=5,
    )
    mock_reload.assert_not_called()
