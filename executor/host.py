"""Docker exec wrapper for the executor container."""

from __future__ import annotations

import subprocess

from appcore.api.config import settings


class ExecutorError(Exception):
    """Raised when a docker exec command fails inside the executor container."""

    def __init__(self, message: str, returncode: int | None = None, output: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.output = output


def _docker_exec(
    cmd: list[str],
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    container = settings.executor.CONTAINER_NAME
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT
    full_cmd = ["docker", "exec", "-e", "PYTHONUNBUFFERED=1", container, *cmd]

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExecutorError(
            f"Command timed out after {timeout}s: {' '.join(cmd)}",
            returncode=None,
            output=str(exc.stdout or ""),
        ) from exc

    if result.returncode != 0:
        raise ExecutorError(
            f"Command failed (rc={result.returncode}): {' '.join(cmd)}",
            returncode=result.returncode,
            output=result.stderr or result.stdout,
        )

    return result


def _docker_exec_allow_partial(
    cmd: list[str],
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    container = settings.executor.CONTAINER_NAME
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT
    full_cmd = ["docker", "exec", "-e", "PYTHONUNBUFFERED=1", container, *cmd]

    try:
        return subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExecutorError(
            f"Command timed out after {timeout}s: {' '.join(cmd)}",
            returncode=None,
            output=str(exc.stdout or ""),
        ) from exc


def install_extension_in_executor(publisher: str, name: str, version: str) -> str:
    vsix_container_path = (
        f"{settings.executor.EXTENSIONS_CONTAINER_PATH}"
        f"/{publisher}.{name}-{version}.vsix"
    )
    result = _docker_exec(
        [
            "code",
            "--install-extension",
            vsix_container_path,
            "--no-sandbox",
            "--force",
        ]
    )
    return result.stdout


_RELOAD_TIMEOUT = 60
_RESET_TIMEOUT = 90
_AUTOMATION_TIMEOUT = 600
_DEFAULT_SCENARIO = "coding_session"


def reload_vscode_window() -> str:
    result = _docker_exec(
        ["python3", settings.executor.RELOAD_SCRIPT_PATH],
        timeout=_RELOAD_TIMEOUT,
    )
    return result.stdout


def reset_executor_sandbox_state(reload_window: bool = True) -> str:
    reset_result = _docker_exec(
        ["python3", settings.executor.RESET_SCRIPT_PATH],
        timeout=_RESET_TIMEOUT,
    )
    outputs = [reset_result.stdout.strip()]
    if reload_window:
        outputs.append(reload_vscode_window().strip())
    return "\n".join(output for output in outputs if output)


def run_playwright_automation(
    report_path: str,
    scenario: str | None = None,
    trigger_container_path: str | None = None,
    reload_before_run: bool = False,
    target_extension_id: str | None = None,
) -> str:
    cmd = [
        "python3",
        settings.executor.ENTRYPOINT_PATH,
        "--monitor",
        "--report-path",
        report_path,
    ]
    if reload_before_run:
        cmd.append("--reload-before-run")
    if target_extension_id:
        cmd.extend(["--target-extension-id", target_extension_id])
    if trigger_container_path:
        cmd.extend(["--triggers", trigger_container_path])
    else:
        effective_scenario = scenario or _DEFAULT_SCENARIO
        if effective_scenario != "all":
            cmd.extend(["--scenario", effective_scenario])

    result = _docker_exec_allow_partial(cmd, timeout=_AUTOMATION_TIMEOUT)
    return result.stdout


__all__ = [
    "ExecutorError",
    "_docker_exec",
    "_docker_exec_allow_partial",
    "install_extension_in_executor",
    "reload_vscode_window",
    "reset_executor_sandbox_state",
    "run_playwright_automation",
]
