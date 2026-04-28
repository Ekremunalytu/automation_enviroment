"""Docker exec wrapper for the executor container."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from executor.config import settings
from packages.marketplace_identity import safe_marketplace_slug


class ExecutorError(Exception):
    """Raised when a docker exec command fails inside the executor container."""

    def __init__(self, message: str, returncode: int | None = None, output: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.output = output


_DOCKER_RETRYABLE_ERROR_MARKERS = (
    "failed to connect to the docker api",
    "cannot connect to the docker daemon",
    "docker daemon is not running",
    "tls handshake timeout",
    "transport is closing",
    "dial unix /var/run/docker.sock",
    "docker.sock",
)
_DOCKER_MAX_RETRIES = 3


def _is_retryable_docker_transport_error(output: str) -> bool:
    normalized = output.lower()
    if any(marker in normalized for marker in _DOCKER_RETRYABLE_ERROR_MARKERS):
        return True
    return "error during connect" in normalized and (
        "docker daemon" in normalized or "docker.sock" in normalized
    )


def _docker_exec_target_path(container_path: str) -> Path:
    return Path(settings.project.OUTPUT_DIR) / Path(container_path).name


def _run_docker_exec(
    cmd: list[str],
    timeout: int,
    *,
    allow_partial: bool,
) -> subprocess.CompletedProcess[str]:
    container = settings.executor.CONTAINER_NAME
    full_cmd = ["docker", "exec", "-e", "PYTHONUNBUFFERED=1", container, *cmd]

    for attempt in range(_DOCKER_MAX_RETRIES):
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

        output = result.stderr or result.stdout or ""
        if (
            result.returncode != 0
            and _is_retryable_docker_transport_error(output)
            and attempt < (_DOCKER_MAX_RETRIES - 1)
        ):
            time.sleep(2**attempt)
            continue

        if result.returncode != 0 and not allow_partial:
            raise ExecutorError(
                f"Command failed (rc={result.returncode}): {' '.join(cmd)}",
                returncode=result.returncode,
                output=output,
            )

        if result.returncode != 0 and _is_retryable_docker_transport_error(output):
            raise ExecutorError(
                f"Command failed (rc={result.returncode}): {' '.join(cmd)}",
                returncode=result.returncode,
                output=output,
            )

        return result

    raise ExecutorError(
        f"Command failed after {_DOCKER_MAX_RETRIES} attempts: {' '.join(cmd)}",
        returncode=None,
        output="",
    )


def _docker_exec(
    cmd: list[str],
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT
    return _run_docker_exec(cmd, timeout, allow_partial=False)


def _docker_exec_allow_partial(
    cmd: list[str],
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT
    return _run_docker_exec(cmd, timeout, allow_partial=True)


_INSTALL_EXTENSION_RETRYABLE_MARKERS = (
    "connection refused",
    "econnrefused",
    "could not connect",
    "ipc handle",
    "ipc hook",
    "singleton",
    "already running",
    "extension host",
    "lock file",
    "exited unexpectedly",
    "timed out",
    "timeout",
    "renderer process gone",
    "target crashed",
)


def _is_retryable_install_error(output: str) -> bool:
    normalized = output.lower()
    return any(marker in normalized for marker in _INSTALL_EXTENSION_RETRYABLE_MARKERS)


def install_extension_in_executor(publisher: str, name: str, version: str) -> str:
    """Install a VSIX inside the executor with one reload-backed retry.

    VS Code's ``--install-extension`` CLI talks to any running instance over
    IPC; if that instance is mid-reload or has a stale singleton lock, the
    command fails with ``rc=1`` even though the sandbox is otherwise healthy.
    We surface the CLI's own stderr in :class:`ExecutorError.output` so the
    caller can emit it to the job log, and on recognizable transient failures
    we issue a fresh ``reload_vscode_window()`` + brief settle delay and try
    once more. Non-retryable failures (bad VSIX, permission, etc.) propagate
    on the first attempt.
    """
    slug = safe_marketplace_slug(publisher, name, version)
    vsix_container_path = f"{settings.executor.EXTENSIONS_CONTAINER_PATH}/{slug}.vsix"
    cmd = [
        "code",
        "--install-extension",
        vsix_container_path,
        "--no-sandbox",
        "--force",
    ]
    try:
        result = _docker_exec(cmd)
    except ExecutorError as first_exc:
        if not _is_retryable_install_error(first_exc.output):
            raise
        try:
            reload_vscode_window()
        except ExecutorError:
            raise first_exc from None
        time.sleep(2)
        try:
            result = _docker_exec(cmd)
        except ExecutorError as retry_exc:
            raise ExecutorError(
                f"{retry_exc}; first attempt output: "
                f"{first_exc.output[-200:].strip()}",
                returncode=retry_exc.returncode,
                output=retry_exc.output,
            ) from retry_exc
    return result.stdout


_RELOAD_TIMEOUT = 90
_RESET_TIMEOUT = 90
_AUTOMATION_TIMEOUT = 600
_DEFAULT_SCENARIO = "coding_session"
_RELOAD_CLEANUP_TIMEOUT = 5


def _cleanup_stale_reload_processes() -> None:
    try:
        _docker_exec_allow_partial(
            ["pkill", "-f", settings.executor.RELOAD_SCRIPT_PATH],
            timeout=_RELOAD_CLEANUP_TIMEOUT,
        )
    except ExecutorError:
        return


def _cleanup_stale_entrypoint_processes() -> None:
    try:
        _docker_exec_allow_partial(
            ["pkill", "-f", settings.executor.ENTRYPOINT_PATH],
            timeout=_RELOAD_CLEANUP_TIMEOUT,
        )
    except ExecutorError:
        return


def _last_reload_output_line(output: str) -> str | None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    return lines[-1]


def _reload_error_message(exc: ExecutorError) -> str:
    detail = _last_reload_output_line(exc.output)
    if detail:
        return f"{exc}; last reload output: {detail}"
    return str(exc)


def reload_vscode_window() -> str:
    _cleanup_stale_reload_processes()
    try:
        result = _docker_exec(
            ["python3", settings.executor.RELOAD_SCRIPT_PATH],
            timeout=_RELOAD_TIMEOUT,
        )
    except ExecutorError as exc:
        _cleanup_stale_reload_processes()
        raise ExecutorError(
            _reload_error_message(exc),
            returncode=exc.returncode,
            output=exc.output,
        ) from exc
    return result.stdout


def reset_executor_sandbox_state(reload_window: bool = True) -> str:
    _cleanup_stale_entrypoint_processes()
    reset_result = _docker_exec(
        ["python3", settings.executor.RESET_SCRIPT_PATH],
        timeout=_RESET_TIMEOUT,
    )
    outputs = [reset_result.stdout.strip()]
    if reload_window:
        try:
            outputs.append(reload_vscode_window().strip())
        except ExecutorError:
            time.sleep(2)
            outputs.append(reload_vscode_window().strip())
    return "\n".join(output for output in outputs if output)


def cleanup_trigger_file(trigger_container_path: str | None) -> None:
    if not trigger_container_path:
        return

    _docker_exec_target_path(trigger_container_path).unlink(missing_ok=True)
    _docker_exec_allow_partial(
        ["rm", "-f", trigger_container_path],
        timeout=_RELOAD_CLEANUP_TIMEOUT,
    )


def run_playwright_automation(
    report_path: str,
    scenario: str | None = None,
    trigger_container_path: str | None = None,
    skip_automation: bool = False,
    reload_before_run: bool = False,
    target_extension_id: str | None = None,
) -> str:
    effective_scenario = None
    if not skip_automation:
        effective_scenario = scenario or (
            None if trigger_container_path else _DEFAULT_SCENARIO
        )
    cmd = [
        "python3",
        settings.executor.ENTRYPOINT_PATH,
        "--monitor",
        "--report-path",
        report_path,
    ]
    if skip_automation:
        cmd.append("--skip-automation")
    if reload_before_run:
        cmd.append("--reload-before-run")
    if target_extension_id:
        cmd.extend(["--target-extension-id", target_extension_id])
    if trigger_container_path:
        cmd.extend(["--triggers", trigger_container_path])
        if effective_scenario and effective_scenario != "all":
            cmd.extend(["--scenario", effective_scenario])
    else:
        if effective_scenario and effective_scenario != "all":
            cmd.extend(["--scenario", effective_scenario])

    try:
        try:
            result = _docker_exec_allow_partial(cmd, timeout=_AUTOMATION_TIMEOUT)
        except ExecutorError as exc:
            if exc.returncode is None:
                _cleanup_stale_entrypoint_processes()
            raise
        report_host_path = _docker_exec_target_path(report_path)
        if result.returncode != 0 and not report_host_path.exists():
            output = result.stderr or result.stdout or ""
            raise ExecutorError(
                "Automation exited before writing the requested report: "
                f"{report_host_path.name}",
                returncode=result.returncode,
                output=output,
            )
        return result.stdout
    finally:
        cleanup_trigger_file(trigger_container_path)


__all__ = [
    "ExecutorError",
    "_docker_exec",
    "_docker_exec_allow_partial",
    "cleanup_trigger_file",
    "install_extension_in_executor",
    "reload_vscode_window",
    "reset_executor_sandbox_state",
    "run_playwright_automation",
]
