"""Absolute paths to binaries invoked via subprocess (W8-4).

Container-internal binaries are pinned to fixed Linux paths because the
executor image (Dockerfile) controls the install layout. The host-side
``docker`` CLI is resolved at first use via ``shutil.which`` because path
varies across Linux (/usr/bin), Docker Desktop on macOS (/usr/local/bin
or /opt/homebrew/bin), and CI runners.

PATH hijacking guard: every subprocess invocation under ``executor/`` must
use absolute paths so a tampered ``$PATH`` (container or host) cannot swap
the launcher. See ``tests/architecture/test_absolute_binary_paths.py`` for
the regression gate that pins this discipline.
"""

from __future__ import annotations

import shutil

CODE_PATH = "/usr/bin/code"
XDG_OPEN_PATH = "/usr/bin/xdg-open"
PYTHON3_PATH = "/usr/bin/python3"
PKILL_PATH = "/usr/bin/pkill"
RM_PATH = "/bin/rm"
# W14-6 sub-commit 6: variable-indirect ``subprocess.Popen(cmd)``
# coverage extension. Pre-W14-6 the runtime_capture subpackage built
# ``cmd = ["inotifywait", ...]`` / ``cmd = ["tshark", ...]`` /
# ``cmd = ["strace", ...]`` lists at call sites and passed the
# variable to ``subprocess.Popen`` — the existing
# ``test_absolute_binary_paths.py`` literal-detector intentionally
# skipped that form, leaving these binaries as opaque PATH-resolved
# names in production. The Dockerfile installs all three at canonical
# Debian/Ubuntu paths via ``apt install inotify-tools tshark strace``.
INOTIFYWAIT_PATH = "/usr/bin/inotifywait"
TSHARK_PATH = "/usr/bin/tshark"
STRACE_PATH = "/usr/bin/strace"

_DOCKER_PATH: str | None = None


class HostBinaryNotFoundError(RuntimeError):
    """Raised when a host-side binary cannot be resolved on PATH."""


def docker_path() -> str:
    """Return absolute path to host ``docker`` CLI; cache after first resolve."""
    global _DOCKER_PATH
    if _DOCKER_PATH is None:
        resolved = shutil.which("docker")
        if not resolved:
            raise HostBinaryNotFoundError(
                "docker binary not found on PATH; cannot invoke executor container"
            )
        _DOCKER_PATH = resolved
    return _DOCKER_PATH


def _reset_docker_path_cache() -> None:
    """Test-only hook to clear the lazily resolved docker path."""
    global _DOCKER_PATH
    _DOCKER_PATH = None


__all__ = [
    "CODE_PATH",
    "INOTIFYWAIT_PATH",
    "PKILL_PATH",
    "PYTHON3_PATH",
    "RM_PATH",
    "STRACE_PATH",
    "TSHARK_PATH",
    "XDG_OPEN_PATH",
    "HostBinaryNotFoundError",
    "docker_path",
]
