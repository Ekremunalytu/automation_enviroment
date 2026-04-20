"""Shared helpers and constants for runtime capture modules.

These helpers are duplicated (re-exported) from ``monitor`` to break
the import cycle between ``monitor`` and the capture submodules.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

VSCODE_USER_DATA = Path("/home/executor/.vscode")
VSCODE_LOGS_DIR = VSCODE_USER_DATA / "logs"

_FILE_WATCH_PATHS = [
    Path("/workspace"),
    Path("/home/executor/.ssh"),
    Path("/home/executor/.aws"),
    Path("/home/executor/.kube"),
    Path("/home/executor/.docker"),
    Path("/home/executor/.config/gcloud"),
    Path("/home/executor/credentials"),
    Path("/home/executor/.wallet"),
]
_SENSITIVE_PATH_PREFIXES = (
    "/workspace/.env",
    "/workspace/credentials",
    "/workspace/.wallet",
    "/home/executor/.ssh",
    "/home/executor/.aws",
    "/home/executor/.kube",
    "/home/executor/.docker",
    "/home/executor/.config/gcloud",
    "/home/executor/.npmrc",
    "/home/executor/.git-credentials",
)
_NOISY_PATH_PREFIXES = (
    "/proc/",
    "/dev/",
    "/sys/",
    "/usr/",
    "/etc/",
    "/home/executor/.vscode/logs/",
)


def _log(msg: str) -> None:
    print(f"[monitor] {msg}")


def _first_non_empty(*values: str) -> str:
    for value in values:
        item = value.strip()
        if item:
            return item
    return ""


def _is_sensitive_path(path: str) -> bool:
    normalized = path.strip()
    return any(normalized.startswith(prefix) for prefix in _SENSITIVE_PATH_PREFIXES)


def _is_relevant_file_path(path: str) -> bool:
    normalized = path.strip()
    if not normalized or normalized in {".", ".."}:
        return False
    if any(normalized.startswith(prefix) for prefix in _NOISY_PATH_PREFIXES):
        return False
    return normalized.startswith("/workspace") or normalized.startswith(
        "/home/executor"
    )


def _parse_iso_timestamp(timestamp: str) -> float | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp).timestamp()
    except ValueError:
        pass
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").timestamp()
    except ValueError:
        return None
