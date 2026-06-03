"""Shared helpers and constants for runtime capture modules.

These helpers are duplicated (re-exported) from ``monitor`` to break
the import cycle between ``monitor`` and the capture submodules.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
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

# W22: the harness rewrites ``/workspace/.extrace-harness/context.json`` once
# per harness-routed attempt (see ``stimulus/materializers.py``). Once the
# planner synthesizes an ``onCommand`` attempt per contributed command, those
# writes multiply into a file-event flood that is pure harness bookkeeping —
# not target-extension behavior — and also fires the language server's
# ``didChangeWatchedFiles`` storm. Drop any path inside this directory from
# capture (matches the ``files.watcherExclude`` entry seeded in ``start.sh``).
_HARNESS_ARTIFACT_DIRNAME = ".extrace-harness"


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


def _is_harness_artifact_path(path: str) -> bool:
    """True for paths inside the ``.extrace-harness`` bookkeeping directory.

    Keys off the exact path component (with slash boundaries) so a sibling
    such as ``/workspace/.extrace-harness-notes/`` is not misclassified.
    Also matches the directory node itself (e.g. an inotify ``CREATE,ISDIR``).
    """
    return f"/{_HARNESS_ARTIFACT_DIRNAME}/" in path or path.endswith(
        f"/{_HARNESS_ARTIFACT_DIRNAME}"
    )


def _is_relevant_file_path(path: str) -> bool:
    normalized = path.strip()
    if not normalized or normalized in {".", ".."}:
        return False
    if any(normalized.startswith(prefix) for prefix in _NOISY_PATH_PREFIXES):
        return False
    if _is_harness_artifact_path(normalized):
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


def _enumerate_proc_pids() -> list[int]:
    """Snapshot currently-running PIDs from /proc.

    Used at strace-attach time to seed parent/cwd lineage for processes that
    already exist before tracing begins (and therefore never emit a
    clone/fork/vfork line for strace to observe).
    """
    pids: list[int] = []
    try:
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit():
                pids.append(int(entry.name))
    except OSError:
        pass
    return pids


def _read_proc_ppid(pid: int) -> int | None:
    """Return the parent PID for ``pid`` from /proc, or None if unavailable.

    Prefers /proc/<pid>/status ``PPid:`` (robust to a comm field containing
    spaces or parentheses); falls back to field 4 of /proc/<pid>/stat parsed
    after the final ')' that closes the comm field.
    """
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("PPid:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except ValueError:
                    return None
    except OSError:
        pass
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    rparen = raw.rfind(")")
    if rparen == -1:
        return None
    # After the comm field the layout is ``state ppid pgrp ...`` so ppid is the
    # second whitespace-separated token following the closing paren.
    fields = raw[rparen + 1 :].split()
    if len(fields) < 2:
        return None
    try:
        return int(fields[1])
    except ValueError:
        return None


def _read_proc_cwd(pid: int) -> str:
    """Return the working directory for ``pid`` from /proc, or '' if unavailable."""
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return ""


def backfill_ppids_from_proc(
    pids: Iterable[int],
    ppid_by_pid: dict[int, int | None],
    *,
    cwd_by_pid: dict[int, str] | None = None,
) -> None:
    """Seed parent (and optionally cwd) lineage for pre-existing processes.

    strace's ``-f`` only records a parent when it observes the
    clone/fork/vfork that creates a child. Processes that already exist when
    strace attaches therefore have no observed parent, leaving
    ``ppid_by_pid.get(pid)`` None and breaking pid-lineage attribution. This
    reads /proc once at attach time to fill that gap. Live clone observations
    run afterwards and overwrite these entries, so observed parentage always
    wins over the snapshot.
    """
    for pid in pids:
        ppid = _read_proc_ppid(pid)
        if ppid is not None:
            ppid_by_pid.setdefault(pid, ppid)
        if cwd_by_pid is not None:
            cwd = _read_proc_cwd(pid)
            if cwd:
                cwd_by_pid.setdefault(pid, cwd)
