"""
scanner/executor.py
===================

Docker Exec Wrapper for Executor Container
-------------------------------------------

Provides functions to install VS Code extensions and run Playwright
automation inside the executor container via ``docker exec``.

No database access. Pure subprocess operations.
"""

from __future__ import annotations

import subprocess

from core.config import settings


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
    """
    Run a command inside the executor container via ``docker exec``.

    Args:
        cmd: Command and arguments to execute inside the container.
        timeout: Seconds before the subprocess is killed.

    Returns:
        CompletedProcess with captured stdout/stderr.

    Raises:
        ExecutorError: On non-zero exit code or timeout.
    """
    container = settings.executor.CONTAINER_NAME
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT

    full_cmd = [
        "docker",
        "exec",
        "-e",
        "PYTHONUNBUFFERED=1",
        container,
        *cmd,
    ]

    try:
        result = subprocess.run(  # noqa: S603
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
    """Run a command inside the executor container, tolerating non-zero exit codes.

    Used for automation runs where some scenarios may fail but the report
    is still generated successfully.

    Raises:
        ExecutorError: Only on timeout (not on non-zero exit).
    """
    container = settings.executor.CONTAINER_NAME
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT

    full_cmd = [
        "docker",
        "exec",
        "-e",
        "PYTHONUNBUFFERED=1",
        container,
        *cmd,
    ]

    try:
        result = subprocess.run(  # noqa: S603
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

    return result


def install_extension_in_executor(publisher: str, name: str, version: str) -> str:
    """
    Install a .vsix extension in the executor container's VS Code instance.

    Args:
        publisher: Extension publisher.
        name: Extension name.
        version: Extension version.

    Returns:
        stdout from the install command.

    Raises:
        ExecutorError: If the install command fails.
    """
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


_RELOAD_SCRIPT_PATH = "/home/executor/playwright/reload_vscode.py"
"""Path to the container-side reload script."""

_RELOAD_TIMEOUT = 60
"""Seconds to allow for the VS Code window reload."""


def reload_vscode_window() -> str:
    """
    Reload the VS Code window inside the executor container.

    Must be called **after** ``install_extension_in_executor`` so that
    VS Code picks up the newly installed extension.  Without a reload,
    the extension never activates.

    Returns:
        stdout from the reload script.

    Raises:
        ExecutorError: If the reload command fails or times out.
    """
    result = _docker_exec(
        ["python3", _RELOAD_SCRIPT_PATH],
        timeout=_RELOAD_TIMEOUT,
    )
    return result.stdout


_DEFAULT_SCENARIO = "coding_session"


def run_playwright_automation(
    report_path: str,
    scenario: str | None = None,
    trigger_container_path: str | None = None,
) -> str:
    """
    Run the Playwright automation entrypoint inside the executor container.

    Args:
        report_path: Path (inside container) where the report will be written.
        scenario: Optional scenario name to pass to entrypoint.
            Defaults to ``coding_session`` for fast analysis (~15s).
            Pass ``"all"`` to run every scenario (~3-5 min).
        trigger_container_path: Optional path to trigger payload JSON inside
            the container. When provided, the entrypoint uses smart scenario
            selection based on the extension's activation events.

    Returns:
        stdout from the automation run.

    Raises:
        ExecutorError: If the automation command times out.
    """
    cmd = [
        "python3",
        settings.executor.ENTRYPOINT_PATH,
        "--monitor",
        "--report-path",
        report_path,
    ]

    # When triggers are provided, let the entrypoint handle scenario selection
    if trigger_container_path:
        cmd.extend(["--triggers", trigger_container_path])
    else:
        effective_scenario = scenario or _DEFAULT_SCENARIO
        # "all" means run every scenario (no --scenario flag)
        if effective_scenario != "all":
            cmd.extend(["--scenario", effective_scenario])

    # Use partial mode: some scenarios may fail (exit code 1) but the
    # activation report is still written to disk.  Only a timeout is fatal.
    result = _docker_exec_allow_partial(cmd)
    return result.stdout
