"""Bounded, read-only Docker container state inspection."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any

from executor.binary_paths import HostBinaryNotFoundError, docker_path


@dataclass(frozen=True, slots=True)
class ContainerRuntimeStatus:
    """Normalized Docker state without exposing raw daemon output."""

    container: str
    status: str
    health: str
    running: bool
    started_at: str
    finished_at: str
    exit_code: int | None
    oom_killed: bool
    error: str | None = None


def _unknown_status(container: str, error: str) -> ContainerRuntimeStatus:
    return ContainerRuntimeStatus(
        container=container,
        status="unknown",
        health="unknown",
        running=False,
        started_at="",
        finished_at="",
        exit_code=None,
        oom_killed=False,
        error=error,
    )


def inspect_container_runtime(
    container: str,
    *,
    timeout_seconds: int = 5,
) -> ContainerRuntimeStatus:
    """Inspect one trusted, configuration-owned container name."""

    try:
        binary = docker_path()
    except HostBinaryNotFoundError:
        return _unknown_status(container, "Docker CLI unavailable")

    argv = [
        binary,
        "inspect",
        "--format",
        "{{json .State}}",
        container,
    ]
    try:
        result = subprocess.run(  # nosec B603 - absolute binary, fixed argv, no shell
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _unknown_status(container, "Docker inspection timed out")
    except OSError:
        return _unknown_status(container, "Docker inspection failed")

    if result.returncode != 0:
        return _unknown_status(container, "Container unavailable")

    try:
        state: Any = json.loads(result.stdout)
    except json.JSONDecodeError:
        return _unknown_status(container, "Docker returned malformed state")

    if not isinstance(state, dict):
        return _unknown_status(container, "Docker returned malformed state")

    health_doc = state.get("Health")
    health = (
        str(health_doc.get("Status", "unknown"))
        if isinstance(health_doc, dict)
        else "not-configured"
    )
    exit_code = state.get("ExitCode")

    return ContainerRuntimeStatus(
        container=container,
        status=str(state.get("Status", "unknown")),
        health=health,
        running=bool(state.get("Running", False)),
        started_at=str(state.get("StartedAt", "")),
        finished_at=str(state.get("FinishedAt", "")),
        exit_code=exit_code if isinstance(exit_code, int) else None,
        oom_killed=bool(state.get("OOMKilled", False)),
    )


__all__ = ["ContainerRuntimeStatus", "inspect_container_runtime"]
