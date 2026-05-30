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
# Monitor privilege-drop wrapper (executor/container/monitor_entrypoint.sh,
# baked into the image). run_playwright_automation prepends this to the
# docker-exec'd monitor command and runs the exec as root so the wrapper can
# raise CAP_NET_RAW into the ambient set before dropping to the executor user —
# the only way tshark gets NET_RAW effective under no-new-privileges (ADR 0013).
MONITOR_ENTRYPOINT_PATH = "/usr/local/bin/monitor_entrypoint.sh"
# Static-analyzer container (ES-2, ADR 0016): the hardened image is built on
# python:3.11-slim-bookworm (the api image's audited base digest, reused rather
# than auditing a second base), whose interpreter lives under /usr/local (unlike
# the executor's Ubuntu /usr/bin/python3). executor/static_host.py invokes
# `python -m static_runtime` inside that container, so the in-container python
# path is pinned absolute here for the same PATH-hijack guard.
STATIC_ANALYZER_PYTHON3_PATH = "/usr/local/bin/python3"

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
    "MONITOR_ENTRYPOINT_PATH",
    "PKILL_PATH",
    "PYTHON3_PATH",
    "RM_PATH",
    "STATIC_ANALYZER_PYTHON3_PATH",
    "STRACE_PATH",
    "TSHARK_PATH",
    "XDG_OPEN_PATH",
    "HostBinaryNotFoundError",
    "docker_path",
]
