"""Docker exec wrapper for the hardened static-analyzer container (ES-2, ADR 0016).

Host-side orchestration for ``automation_static_analyzer`` — a lean sibling of
``executor/host.py`` scoped to the static pre-check stage. Like ``host.py`` it
is baked into the ``automation_api`` image (``docker/api/Dockerfile`` ``COPY .``)
and drives the container from the host via ``docker exec``; it is NOT shipped
into any runtime container.

ES-2 lands this **dormant**: no caller wires it in until the ES-3b orchestrator.
It is exercised by ``tests/executor/test_static_control.py`` with a mocked
subprocess. The cancellation / off-thread coordinator (mirroring the analyze
monitor) also lands at ES-3b.
"""

from __future__ import annotations

import contextlib
import subprocess

from executor.binary_paths import STATIC_ANALYZER_PYTHON3_PATH, docker_path
from executor.config import settings


class StaticAnalyzerError(Exception):
    """Raised when a docker exec into the static-analyzer container fails."""

    def __init__(self, message: str, returncode: int | None = None, output: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.output = output


def _run_static_docker_exec(
    cmd: list[str], timeout: int
) -> subprocess.CompletedProcess[str]:
    """Run ``cmd`` inside the static-analyzer container via ``docker exec``.

    Lean relative to ``executor.host._run_docker_exec``: the static stage
    threads no harness secret, needs no ``-u`` user override, and runs against a
    local network-isolated one-shot container so it skips the docker-transport
    retry loop. argv is a list (never ``shell=True``); argv[0] is the absolute
    ``docker_path()`` so a tampered ``$PATH`` cannot swap the launcher (W8-4).
    """
    container = settings.static_analyzer.CONTAINER_NAME
    full_cmd = [
        docker_path(),
        "exec",
        "-e",
        "PYTHONUNBUFFERED=1",
        container,
        *cmd,
    ]
    try:
        result = subprocess.run(  # nosec B603 - argv list, absolute docker_path(), no shell
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise StaticAnalyzerError(
            f"Static analysis timed out after {timeout}s: {' '.join(full_cmd)}",
            returncode=None,
            output=str(exc.stdout or ""),
        ) from exc

    if result.returncode != 0:
        output = result.stderr or result.stdout or ""
        raise StaticAnalyzerError(
            f"Static analysis failed (rc={result.returncode}): {' '.join(full_cmd)}",
            returncode=result.returncode,
            output=output,
        )
    return result


def run_static_analysis_in_container(
    *,
    vsix_dir: str,
    report_path: str,
    rules_version: str,
    timeout_budget_s: int,
    vsix_sha256: str = "",
) -> str:
    """Invoke ``python -m static_runtime`` inside the static-analyzer container.

    Returns the container's stdout. The container writes the
    ``StaticDetectionReport`` JSON to ``report_path`` (a container-side path on
    the shared ``/results`` mount). ``timeout_budget_s`` is the in-container
    soft budget; the docker-exec wall-clock is capped slightly higher (bounded
    below by ``settings.static_analyzer.DOCKER_EXEC_TIMEOUT``) so the
    in-container budget trips first.

    This ``exec_timeout`` is the **authoritative** bound on an in-flight run:
    cancellation (``cancel_static_analysis_in_container``) is best-effort only,
    so from ES-4 — when Semgrep can make a scan long — it is the wall-clock, not
    the cancel signal, that guarantees a runaway pass terminates.
    """
    cmd = [
        STATIC_ANALYZER_PYTHON3_PATH,
        "-m",
        settings.static_analyzer.ENTRYPOINT_MODULE,
        "--vsix-dir",
        vsix_dir,
        "--report-path",
        report_path,
        "--rules-version",
        rules_version,
        "--timeout-budget-s",
        str(timeout_budget_s),
    ]
    # W26 / Stream 3 (B5, ADR 0016 amendment): additive 5th flag, appended only
    # when present so the frozen 4-flag invocation contract stays callable.
    if vsix_sha256:
        cmd.extend(["--vsix-sha256", vsix_sha256])
    exec_timeout = max(
        settings.static_analyzer.DOCKER_EXEC_TIMEOUT, timeout_budget_s + 5
    )
    result = _run_static_docker_exec(cmd, exec_timeout)
    return result.stdout or ""


def cancel_static_analysis_in_container() -> None:
    """Best-effort terminate of an in-flight ``static_runtime`` run (ES-3b cancel).

    The ES-3b off-thread coordinator calls this when a job is cancelled mid
    static pre-check so the network-isolated analyzer does not keep churning
    through its budget after the worker has moved on. **Timeout-authoritative by
    design:** the minimal hardened image ships no ``procps``, so ``pkill`` is a
    guaranteed no-op today — what actually bounds a runaway run is the docker-exec
    wall-clock in ``run_static_analysis_in_container`` (its ``exec_timeout``), not
    this signal. A non-zero rc (no matching process, or ``pkill`` absent) is
    swallowed — the coordinator has already raised ``AnalysisCancelledError``
    and the kill must never mask the cancel. argv-list invocation (never
    ``shell=True``); argv[0] is the absolute ``docker_path()`` so a tampered
    ``$PATH`` cannot swap the launcher (W8-4). The in-container ``pkill`` runs as
    the non-root ``static`` user and can only signal the ``static_runtime``
    process it owns.
    """
    container = settings.static_analyzer.CONTAINER_NAME
    full_cmd = [docker_path(), "exec", container, "pkill", "-f", "static_runtime"]
    # Best-effort cleanup; the cancel is already authoritative, so a missing
    # process or absent `pkill` (minimal image) must not surface.
    with contextlib.suppress(subprocess.SubprocessError, OSError):
        subprocess.run(  # nosec B603 - argv list, absolute docker_path(), no shell
            full_cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
