"""Docker exec wrapper for the executor container."""

from __future__ import annotations

import contextlib
import re
import stat
import subprocess
import time
from pathlib import Path

from executor.binary_paths import (
    CODE_PATH,
    PKILL_PATH,
    PYTHON3_PATH,
    RM_PATH,
    docker_path,
)
from executor.config import settings
from packages.analysis_contracts.evidence import redact_secrets
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

# W13-11 (Codex F1 close-pass for W13-1 H6): the per-launch HMAC python
# secret is threaded to the entrypoint container as a docker exec env var.
# ``_run_docker_exec`` embeds ``' '.join(cmd)`` into ExecutorError messages
# on non-zero rc and on timeout; the generic ``_REDACTION_PATTERNS``
# (aws/bearer/private_key/api_key/db_url) do not catch the 64-char raw hex
# that ``launch_vscode.sh`` emits, so a targeted masking helper rewrites
# the env value to ``***`` before the message propagates to
# ``str(exc)`` and lands on the persisted ``job.error_detail`` surface.
_HARNESS_SECRET_ENV_NAME = "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE"  # noqa: S105 — env-var name, not a credential
_HARNESS_SECRET_MASK_RE = re.compile(rf"{re.escape(_HARNESS_SECRET_ENV_NAME)}=\S+")


def _mask_harness_secret_in_message(message: str) -> str:
    """W13-11 (E4): replace ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>`` with ``=***`` in error text.

    Operators must still see *which* env was passed (debug-ability) without
    seeing the value. The generic secret redactor cannot help here because
    pure hex matches none of its class patterns.
    """
    return _HARNESS_SECRET_MASK_RE.sub(f"{_HARNESS_SECRET_ENV_NAME}=***", message)


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
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    container = settings.executor.CONTAINER_NAME
    # W13-11: ``extra_env`` is rendered as additional ``-e KEY=VALUE`` args
    # alongside the existing ``-e PYTHONUNBUFFERED=1``. Keeping the env on
    # the docker exec argv (rather than the subprocess.run ``env=`` kwarg)
    # matches the existing convention and lets a single masking helper
    # cover both stdout and exception messages.
    env_args: list[str] = []
    if extra_env:
        for key, value in extra_env.items():
            env_args.extend(["-e", f"{key}={value}"])
    full_cmd = [
        docker_path(),
        "exec",
        "-e",
        "PYTHONUNBUFFERED=1",
        *env_args,
        container,
        *cmd,
    ]

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
                _mask_harness_secret_in_message(
                    f"Command timed out after {timeout}s: {' '.join(full_cmd)}"
                ),
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
                _mask_harness_secret_in_message(
                    f"Command failed (rc={result.returncode}): {' '.join(full_cmd)}"
                ),
                returncode=result.returncode,
                output=output,
            )

        if result.returncode != 0 and _is_retryable_docker_transport_error(output):
            raise ExecutorError(
                _mask_harness_secret_in_message(
                    f"Command failed (rc={result.returncode}): {' '.join(full_cmd)}"
                ),
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
    *,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT
    return _run_docker_exec(cmd, timeout, allow_partial=False, extra_env=extra_env)


def _docker_exec_allow_partial(
    cmd: list[str],
    timeout: int | None = None,
    *,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = timeout or settings.executor.DOCKER_EXEC_TIMEOUT
    return _run_docker_exec(cmd, timeout, allow_partial=True, extra_env=extra_env)


# W13-11 (Codex F1 close-pass for W13-1 H6): host-side eager-consume of
# the per-launch HMAC python secret. ``launch_vscode.sh`` writes
# ``/results/_extrace_harness_python_secret`` at chmod 0600 owned by the
# executor user; the bind-mount ``${EXECUTOR_OUTPUT_HOST_PATH:-./output}``
# makes the file visible to the host process under
# ``Path(settings.project.OUTPUT_DIR) / "_extrace_harness_python_secret"``.
# Reading + unlinking the file on the host BEFORE ``install_extension``
# admits the target VSIX closes the same-UID install -> setup_monitor
# window that re-opened W13-1 H6. The consumed value is then threaded
# through ``run_playwright_automation`` as the
# ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`` env var so the entrypoint
# container's ``load_harness_python_secret`` reads it from os.environ
# (env-priority) instead of from the bind-mounted file.
_HARNESS_PYTHON_SECRET_FILENAME = "_extrace_harness_python_secret"  # noqa: S105 — filename literal, not a credential


def consume_harness_python_secret_eager(
    host_path: Path | None = None,
) -> str | None:
    """W13-11: read + unlink the per-launch HMAC secret on the host before VSIX admit.

    Returns the secret string when the file exists at chmod 0600 with a
    non-empty body; ``None`` otherwise (missing file, wrong mode, read
    error). Always attempts the unlink even on reject so a malformed
    file cannot linger into the next launch cycle (defense-in-depth).

    Ownership guard is intentionally skipped — macOS Docker Desktop
    bind-mount UID mapping makes ``stat.st_uid`` unreliable across host
    platforms. The mode guard plus the producer (``launch_vscode.sh``)
    chmodding 0600 is the contract.
    """
    path = host_path or (
        Path(settings.project.OUTPUT_DIR) / _HARNESS_PYTHON_SECRET_FILENAME
    )
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    if stat.S_IMODE(st.st_mode) != 0o600:
        # Suspicious: launch_vscode.sh writes 0o600. Best-effort unlink
        # so the malformed file cannot persist; do not read its content.
        with contextlib.suppress(FileNotFoundError, OSError):
            path.unlink()
        return None

    try:
        secret = path.read_text(encoding="utf-8").strip()
    except OSError:
        secret = ""
    with contextlib.suppress(FileNotFoundError, OSError):
        path.unlink()
    return secret or None


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
        CODE_PATH,
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
            # Retry-path message embeds raw subprocess output from the first
            # attempt; redact before it lands on the persisted job.error_detail
            # surface (workflows/marketplace/analysis_service.py persists
            # str(exc) verbatim).
            raw_message = (
                f"{retry_exc}; first attempt output: {first_exc.output[-200:].strip()}"
            )
            raise ExecutorError(
                redact_secrets(raw_message),
                returncode=retry_exc.returncode,
                output=retry_exc.output,
            ) from retry_exc
    return result.stdout


_RELOAD_TIMEOUT = 180
_RESET_TIMEOUT = 90
_AUTOMATION_TIMEOUT = 1200
_DEFAULT_SCENARIO = "coding_session"
_RELOAD_CLEANUP_TIMEOUT = 5


def _cleanup_stale_reload_processes() -> None:
    try:
        _docker_exec_allow_partial(
            [PKILL_PATH, "-f", settings.executor.RELOAD_SCRIPT_MODULE],
            timeout=_RELOAD_CLEANUP_TIMEOUT,
        )
    except ExecutorError:
        return


def _cleanup_stale_entrypoint_processes() -> None:
    try:
        _docker_exec_allow_partial(
            [PKILL_PATH, "-f", settings.executor.ENTRYPOINT_MODULE],
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
        # ``detail`` is the last non-empty line of the raw subprocess output
        # and may include extension-controlled secret material (PEM/AWS/Bearer/
        # api_key/db_url). Redact before the message reaches str(exc) → the
        # persisted job.error_detail surface.
        return redact_secrets(f"{exc}; last reload output: {detail}")
    return str(exc)


def reload_vscode_window() -> str:
    _cleanup_stale_reload_processes()
    try:
        result = _docker_exec(
            [PYTHON3_PATH, "-m", settings.executor.RELOAD_SCRIPT_MODULE],
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
        [PYTHON3_PATH, "-m", settings.executor.RESET_SCRIPT_MODULE],
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
        [RM_PATH, "-f", trigger_container_path],
        timeout=_RELOAD_CLEANUP_TIMEOUT,
    )


def run_playwright_automation(
    report_path: str,
    scenario: str | None = None,
    trigger_container_path: str | None = None,
    skip_automation: bool = False,
    reload_before_run: bool = False,
    target_extension_id: str | None = None,
    harness_python_secret: str | None = None,
) -> str:
    effective_scenario = None
    if not skip_automation:
        effective_scenario = scenario or (
            None if trigger_container_path else _DEFAULT_SCENARIO
        )
    cmd = [
        PYTHON3_PATH,
        "-m",
        settings.executor.ENTRYPOINT_MODULE,
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

    # W13-11: thread the eager-consumed harness secret to the entrypoint
    # container via the EXECUTOR_HARNESS_PYTHON_SECRET_VALUE env var so
    # ``load_harness_python_secret`` reads it from os.environ rather than
    # from the (now-unlinked) /results bind-mount path. The env-var name
    # is inlined here (rather than via the module-level
    # ``_HARNESS_SECRET_ENV_NAME`` constant) so the architecture gate's
    # AST check sees the literal as a Constant node in this function's
    # body — keeping the env-var contract pinnable from a single
    # call-site invariant.
    extra_env: dict[str, str] | None = None
    if harness_python_secret:
        extra_env = {"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE": harness_python_secret}

    try:
        try:
            result = _docker_exec_allow_partial(
                cmd, timeout=_AUTOMATION_TIMEOUT, extra_env=extra_env
            )
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
    "consume_harness_python_secret_eager",
    "install_extension_in_executor",
    "reload_vscode_window",
    "reset_executor_sandbox_state",
    "run_playwright_automation",
]
