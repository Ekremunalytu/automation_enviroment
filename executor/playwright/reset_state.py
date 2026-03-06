"""Reset persistent executor state between extension analyses.

This script runs inside the executor container. It clears user-installed
extensions and VS Code logs, then rebuilds the honeypot workspace so each
analysis starts from a clean baseline.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import workspace

VSCODE_DATA_DIR = Path("/home/executor/.vscode")
EXTENSIONS_DIR = VSCODE_DATA_DIR / "extensions"
LOGS_DIR = VSCODE_DATA_DIR / "logs"


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


def reset_executor_state() -> dict[str, int]:
    """Reset the executor's persistent filesystem state."""
    workspace.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    workspace.clean_workspace()
    workspace.setup_dev_environment()

    removed_extensions = _clear_directory(EXTENSIONS_DIR)
    removed_logs = _clear_directory(LOGS_DIR)

    return {
        "removed_extensions": removed_extensions,
        "removed_logs": removed_logs,
    }


if __name__ == "__main__":
    summary = reset_executor_state()
    print(
        "[reset] sandbox ready "
        f"(extensions={summary['removed_extensions']}, "
        f"logs={summary['removed_logs']})"
    )
