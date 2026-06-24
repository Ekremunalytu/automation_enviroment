"""Reset persistent executor state between extension analyses.

This script runs inside the executor container. It stops the VS Code
process from the previous analysis, clears user-installed extensions and
logs, drops any stale Chromium singleton locks, rebuilds the honeypot
workspace, and re-launches VS Code from scratch. The next
``code --install-extension`` then talks to a fresh instance instead of
racing an IPC socket left behind by the previous run — which is what
caused extensions with ``onStartupFinished`` activation (notably
``dbaeumer.vscode-eslint``) to fail install on the second scan.
"""

from __future__ import annotations

import errno
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from . import workspace

VSCODE_DATA_DIR = Path("/home/executor/.vscode")
EXTENSIONS_DIR = VSCODE_DATA_DIR / "extensions"
LOGS_DIR = VSCODE_DATA_DIR / "logs"

CHROMIUM_CONFIG_DIR = Path("/home/executor/.config/Code")
_SINGLETON_LOCK_NAMES = ("SingletonLock", "SingletonCookie", "SingletonSocket")

_PROC_ROOT = Path("/proc")

# Launch signature used to find the main VS Code process to terminate between
# analyses. ``launch_vscode.sh`` always passes ``--extensionDevelopmentPath``
# (the harness extension) and ONLY the main process carries it — the renderer/
# utility/gpu children and the integrated-terminal bash shells do not — so it
# identifies the right process in EVERY config, including the CDP-off Podman/
# air-gapped deploy where ``--remote-debugging-port`` is absent from argv.
#
# This replaced the old ``--remote-debugging-port`` needle, which was broken two
# ways: (1) it only appeared when CDP was opt-in ON (W14-3), so it matched
# nothing in CDP-off deploys; and (2) it was passed to ``pgrep -f`` WITHOUT a
# ``--`` separator, so pgrep parsed the ``--``-prefixed pattern as an unknown
# option (exit 2) → ``_find_vscode_pids`` returned ``[]`` and
# ``terminate_vscode`` silently no-op'd even with CDP ON. The stale VS Code
# instance (and its orphaned terminal shells) then survived every reset and
# accumulated across analyses, deterministically failing the 2nd same-container
# analyze at reload. See [FOLLOWUP sandbox-reset-stale-state-multi-analyze] +
# [BUG reset-cdp-needle-stale] (B2 / reliability-multi-analyze).
_VSCODE_PROCESS_NEEDLE = "--extensionDevelopmentPath"
_VSCODE_TERMINATE_GRACE_SECONDS = 5.0
_VSCODE_TERMINATE_POLL_INTERVAL = 0.25
_VSCODE_LAUNCH_SCRIPT = Path(
    os.environ.get(
        "EXECUTOR_VSCODE_LAUNCH_SCRIPT",
        "/home/executor/container/launch_vscode.sh",
    )
)


def _clear_directory(path: Path) -> int:
    """Remove all children from a directory and return the removal count."""
    path.mkdir(parents=True, exist_ok=True)

    removed = 0
    for child in path.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)
        removed += 1

    return removed


def _find_vscode_pids() -> list[int]:
    """Return PIDs of the main VS Code process(es) this executor launched.

    The ``--`` separator is REQUIRED: ``_VSCODE_PROCESS_NEEDLE`` is a
    ``--``-prefixed flag, so ``pgrep -f <needle>`` parses it as an (unknown)
    option and exits 2, silently matching nothing. ``pgrep -f -- <needle>``
    forces it to be treated as the search pattern.
    """
    try:
        # arch-allow: bare-binary-path  # W8-4-followup: see POST_POC_BACKLOG.md
        result = subprocess.run(
            ["pgrep", "-f", "--", _VSCODE_PROCESS_NEEDLE],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode not in (0, 1):
        return []
    pids: list[int] = []
    for token in result.stdout.split():
        try:
            pids.append(int(token))
        except ValueError:
            continue
    return pids


def _read_proc_table() -> list[tuple[int, int]]:
    """Return ``(pid, ppid)`` for every live process by scanning ``/proc``.

    Pure ``/proc`` reads (no ``ps``/``pgrep`` subprocess), so terminate can walk
    the process tree without adding another bare-binary call. Used to reap the
    descendants of the main VS Code process — notably the integrated-terminal
    bash shells, which ``setsid`` into their own sessions/process groups and
    would otherwise orphan to PID 1 and accumulate across analyses.
    """
    table: list[tuple[int, int]] = []
    try:
        entries = [entry.name for entry in _PROC_ROOT.iterdir() if entry.name.isdigit()]
    except OSError:
        return table
    for name in entries:
        try:
            stat = (_PROC_ROOT / name / "stat").read_text(encoding="utf-8")
        except OSError:
            # Process exited mid-scan, or the /proc entry is unreadable — skip.
            continue
        # /proc/<pid>/stat: "<pid> (<comm>) <state> <ppid> ...". comm may hold
        # spaces and parentheses, so parse the fields after the final ')'.
        rparen = stat.rfind(")")
        if rparen == -1:
            continue
        fields = stat[rparen + 1 :].split()
        if len(fields) < 2:
            continue
        try:
            table.append((int(name), int(fields[1])))  # fields[1] == ppid
        except ValueError:
            continue
    return table


def _process_tree(
    roots: list[int],
    table: list[tuple[int, int]] | None = None,
) -> list[int]:
    """Return ``roots`` plus every transitive descendant (breadth-first).

    The order is root-first and deterministic; an already-seen PID is skipped
    so a malformed/cyclic ``/proc`` snapshot cannot loop forever.
    """
    if table is None:
        table = _read_proc_table()
    children: dict[int, list[int]] = {}
    for pid, ppid in table:
        children.setdefault(ppid, []).append(pid)
    ordered: list[int] = []
    seen: set[int] = set()
    queue = list(roots)
    while queue:
        pid = queue.pop(0)
        if pid in seen:
            continue
        seen.add(pid)
        ordered.append(pid)
        queue.extend(children.get(pid, ()))
    return ordered


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        return exc.errno != errno.ESRCH
    return True


def _send_signal(pid: int, sig: signal.Signals) -> None:
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        return
    except PermissionError:
        return


def terminate_vscode(
    *,
    grace_seconds: float = _VSCODE_TERMINATE_GRACE_SECONDS,
    poll_interval: float = _VSCODE_TERMINATE_POLL_INTERVAL,
) -> list[int]:
    """SIGTERM the VS Code process tree, fall back to SIGKILL after the grace.

    Reaps the main process AND its descendants (renderer/utility/gpu children
    plus the orphan-prone integrated-terminal shells) so no VS Code state
    survives into the next analyze. Returns every PID that was signalled (an
    empty list is a no-op).
    """
    roots = _find_vscode_pids()
    if not roots:
        return []
    pids = _process_tree(roots)

    for pid in pids:
        _send_signal(pid, signal.SIGTERM)

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not any(_process_alive(pid) for pid in pids):
            return pids
        time.sleep(poll_interval)

    for pid in pids:
        if _process_alive(pid):
            _send_signal(pid, signal.SIGKILL)

    return pids


def cleanup_singleton_locks() -> int:
    """Remove Chromium singleton files so the next launch does not bail out."""
    removed = 0
    if not CHROMIUM_CONFIG_DIR.exists():
        return 0
    for name in _SINGLETON_LOCK_NAMES:
        candidate = CHROMIUM_CONFIG_DIR / name
        try:
            candidate.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue
        removed += 1
    return removed


def launch_vscode() -> int | None:
    """Re-launch VS Code via the shared launch script, return the new PID."""
    if not _VSCODE_LAUNCH_SCRIPT.is_file():
        return None
    try:
        # arch-allow: bare-binary-path  # W8-4-followup: see POST_POC_BACKLOG.md
        result = subprocess.run(
            ["bash", str(_VSCODE_LAUNCH_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    stdout = result.stdout.strip()
    if not stdout:
        return None
    try:
        return int(stdout.splitlines()[-1].strip())
    except ValueError:
        return None


def reset_executor_state() -> dict[str, int]:
    """Reset the executor's persistent filesystem + VS Code process state."""
    workspace.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    workspace.clean_workspace()
    workspace.setup_dev_environment()

    terminated_pids = terminate_vscode()
    removed_extensions = _clear_directory(EXTENSIONS_DIR)
    removed_logs = _clear_directory(LOGS_DIR)
    removed_locks = cleanup_singleton_locks()
    relaunched_pid = launch_vscode()

    return {
        "removed_extensions": removed_extensions,
        "removed_logs": removed_logs,
        "terminated_vscode_processes": len(terminated_pids),
        "removed_singleton_locks": removed_locks,
        "relaunched_vscode_pid": relaunched_pid or 0,
    }


if __name__ == "__main__":
    summary = reset_executor_state()
    print(
        "[reset] sandbox ready "
        f"(extensions={summary['removed_extensions']}, "
        f"logs={summary['removed_logs']}, "
        f"vscode_terminated={summary['terminated_vscode_processes']}, "
        f"locks={summary['removed_singleton_locks']}, "
        f"vscode_pid={summary['relaunched_vscode_pid']})"
    )
