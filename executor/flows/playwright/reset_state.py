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
import sys
import time
from pathlib import Path

# Sibling helper module loaded by flat name; matches workspace.py / entrypoint.py
# pattern. The path-injection and the flat import drop in W9-3/W9-4.
_PKG_DIR = str(Path(__file__).resolve().parent)
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

import workspace  # noqa: E402

VSCODE_DATA_DIR = Path("/home/executor/.vscode")
EXTENSIONS_DIR = VSCODE_DATA_DIR / "extensions"
LOGS_DIR = VSCODE_DATA_DIR / "logs"

CHROMIUM_CONFIG_DIR = Path("/home/executor/.config/Code")
_SINGLETON_LOCK_NAMES = ("SingletonLock", "SingletonCookie", "SingletonSocket")

_VSCODE_PROCESS_NEEDLE = "--remote-debugging-port"
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
    """Return PIDs of VS Code processes this executor started, if any."""
    try:
        # arch-allow: bare-binary-path  # W8-4-followup: see POST_POC_BACKLOG.md
        result = subprocess.run(
            ["pgrep", "-f", _VSCODE_PROCESS_NEEDLE],
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
    """SIGTERM every VS Code process, fall back to SIGKILL after the grace.

    Returns the list of PIDs that were signalled (empty list is a no-op).
    """
    pids = _find_vscode_pids()
    if not pids:
        return []

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
