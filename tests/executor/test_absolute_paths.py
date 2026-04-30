"""W8-4 security regression: absolute binary paths for executor subprocess invocations.

Covers three layers:

1. ``binary_paths`` module — every container-internal constant is an
   absolute path (``str.startswith("/")`` and ``Path.is_absolute()``).
2. ``host._docker_exec`` — the host-side ``docker`` invocation argv[0] is
   the cached ``docker_path()`` result; container-internal cmd[0] (``code``,
   ``pkill``, ``python3``, ``rm``) is the absolute constant.
3. ``docker_path()`` resolver — first call hits ``shutil.which``, raises
   ``HostBinaryNotFoundError`` on miss, caches subsequent calls.

PATH hijack guard: pinning argv[0] to an absolute path prevents a tampered
``$PATH`` (host or container) from swapping the launcher.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from executor import binary_paths, host
from executor.binary_paths import (
    CODE_PATH,
    PKILL_PATH,
    PYTHON3_PATH,
    RM_PATH,
    XDG_OPEN_PATH,
    HostBinaryNotFoundError,
    docker_path,
)


# ---------------------------------------------------------------------------
# Layer A — static: every container-internal constant is absolute
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "constant",
    [CODE_PATH, XDG_OPEN_PATH, PYTHON3_PATH, PKILL_PATH, RM_PATH],
)
def test_container_internal_binary_constant_is_absolute(constant: str) -> None:
    assert isinstance(constant, str)
    assert constant.startswith("/"), f"binary path must start with '/': {constant!r}"
    assert Path(constant).is_absolute(), f"binary path not absolute: {constant!r}"


def test_uri_validation_re_exports_xdg_open_constant() -> None:
    """Sites importing ``XDG_OPEN_PATH`` from ``uri_validation`` keep working
    after the W8-4 consolidation moved the source-of-truth into
    ``executor.binary_paths``."""
    import sys
    from pathlib import Path as _Path

    playwright_dir = (
        _Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
    )
    if str(playwright_dir) not in sys.path:
        sys.path.insert(0, str(playwright_dir))
    import uri_validation

    assert uri_validation.XDG_OPEN_PATH == XDG_OPEN_PATH
    assert uri_validation.XDG_OPEN_PATH == "/usr/bin/xdg-open"


# ---------------------------------------------------------------------------
# Layer B — host._docker_exec uses absolute paths in argv
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_docker_path(monkeypatch: pytest.MonkeyPatch) -> str:
    """Pin ``docker_path()`` to a deterministic value for argv assertions."""
    fake = "/fake/abs/docker"
    binary_paths._reset_docker_path_cache()
    monkeypatch.setattr(binary_paths.shutil, "which", lambda _name: fake)
    return fake


@patch("executor.host.subprocess.run")
def test_docker_exec_uses_absolute_docker_path(
    mock_run: MagicMock, fake_docker_path: str
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="ok", stderr=""
    )

    host._docker_exec(["echo", "hi"])

    argv = mock_run.call_args[0][0]
    assert argv[0] == fake_docker_path
    assert argv[0].startswith("/")
    assert argv[1:5] == [
        "exec",
        "-e",
        "PYTHONUNBUFFERED=1",
        host.settings.executor.CONTAINER_NAME,
    ]


@patch("executor.host.subprocess.run")
def test_install_extension_passes_absolute_code_path_to_docker_exec(
    mock_run: MagicMock, fake_docker_path: str
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="installed", stderr=""
    )

    host.install_extension_in_executor("publisher", "ext", "1.0.0")

    argv = mock_run.call_args[0][0]
    assert argv[0] == fake_docker_path
    container_cmd = argv[5:]
    assert container_cmd[0] == CODE_PATH
    assert container_cmd[0].startswith("/")
    assert container_cmd[0] == "/usr/bin/code"


@patch("executor.host.subprocess.run")
def test_reload_vscode_window_uses_absolute_python3(
    mock_run: MagicMock, fake_docker_path: str
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="reloaded", stderr=""
    )

    host.reload_vscode_window()

    python_invocation: list[Any] | None = None
    for call in mock_run.call_args_list:
        argv = call[0][0]
        if argv[0] != fake_docker_path:
            continue
        container_cmd = argv[5:]
        if container_cmd and container_cmd[0] == PYTHON3_PATH:
            python_invocation = argv
            break
    assert python_invocation is not None, (
        "reload_vscode_window did not invoke /usr/bin/python3 inside docker exec"
    )
    assert python_invocation[5] == "/usr/bin/python3"


@patch("executor.host.subprocess.run")
def test_cleanup_trigger_file_uses_absolute_rm(
    mock_run: MagicMock, fake_docker_path: str, tmp_path: Path
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    host.cleanup_trigger_file("/in/container/triggers.json")

    argv = mock_run.call_args[0][0]
    assert argv[0] == fake_docker_path
    container_cmd = argv[5:]
    assert container_cmd[0] == RM_PATH
    assert container_cmd[0] == "/bin/rm"


@patch("executor.host.subprocess.run")
def test_cleanup_stale_reload_processes_uses_absolute_pkill(
    mock_run: MagicMock, fake_docker_path: str
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    host._cleanup_stale_reload_processes()

    argv = mock_run.call_args[0][0]
    assert argv[0] == fake_docker_path
    container_cmd = argv[5:]
    assert container_cmd[0] == PKILL_PATH
    assert container_cmd[0] == "/usr/bin/pkill"


# ---------------------------------------------------------------------------
# Layer C — docker_path() resolver: lazy resolve, cache, miss raises
# ---------------------------------------------------------------------------


def test_docker_path_resolves_via_shutil_which_and_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary_paths._reset_docker_path_cache()
    calls: list[str] = []

    def fake_which(name: str) -> str | None:
        calls.append(name)
        return "/opt/homebrew/bin/docker"

    monkeypatch.setattr(binary_paths.shutil, "which", fake_which)

    first = docker_path()
    second = docker_path()

    assert first == "/opt/homebrew/bin/docker"
    assert second == first
    assert calls == ["docker"], "second call must hit the cache, not shutil.which"


def test_docker_path_raises_when_binary_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary_paths._reset_docker_path_cache()
    monkeypatch.setattr(binary_paths.shutil, "which", lambda _name: None)

    with pytest.raises(HostBinaryNotFoundError) as exc:
        docker_path()
    assert "docker binary not found" in str(exc.value).lower()


def test_docker_path_returns_absolute_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary_paths._reset_docker_path_cache()
    monkeypatch.setattr(binary_paths.shutil, "which", lambda _name: "/usr/bin/docker")

    resolved = docker_path()
    assert resolved.startswith("/")
    assert Path(resolved).is_absolute()
