"""W13-2: Codex H5 — writable VS Code launcher permission ratchet.

`executor/flows/playwright/reset_state.py::launch_vscode()` runs
`subprocess.run(["bash", str(_VSCODE_LAUNCH_SCRIPT)])` on every reset.
If `launch_vscode.sh` is owned by `executor:executor` with mode 0755,
a target extension running under the same `executor` UID inside the
Extension Host can overwrite it; the modified script then persists
across analyses and re-executes on the next reset → arbitrary command
execution under the executor UID.

This file pins the post-W13-2 invariant: `launch_vscode.sh` must end
up `root:executor` 0750 (root-own + executor group read+exec only).
The companion `start.sh` ratchet is defense-in-depth — `start.sh` is
already root:root in the Dockerfile (the entrypoint), but if a future
edit chowns it to `executor`, the same vector reopens.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from appcore.api.config import settings


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_DOCKERFILE = ROOT / "executor" / "container" / "Dockerfile"

LAUNCH_VSCODE_BASENAME = r"launch_vscode\.sh"
START_SH_BASENAME = r"start\.sh"
LAUNCH_VSCODE_PATH = "/home/executor/container/launch_vscode.sh"


def _dockerfile_text() -> str:
    return EXECUTOR_DOCKERFILE.read_text(encoding="utf-8")


def _resolve_executor_container() -> str:
    # Mirrors test_container_entrypoint._resolve_executor_container; keep in
    # sync if container provisioning changes.
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        pytest.skip("docker unavailable")
    result = subprocess.run(  # noqa: S603
        [
            docker_bin,
            "inspect",
            "-f",
            "{{.State.Running}}",
            settings.executor.CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        pytest.skip("executor container not running")
    return docker_bin


def test_launch_vscode_is_root_owned_and_executor_read_only() -> None:
    """Codex H5: launch_vscode.sh must be `root:executor` + 0750."""

    text = _dockerfile_text()

    forbidden_run_chown = re.search(
        rf"chown\s+executor(?::\S+)?\s+[^\n]*\b{LAUNCH_VSCODE_BASENAME}\b",
        text,
    )
    assert forbidden_run_chown is None, (
        f"Dockerfile: `chown executor:...` applied to launch_vscode.sh "
        f"({forbidden_run_chown.group(0)!r}) — Codex H5 reopens; "
        f"must be `chown root:executor`"
    )

    forbidden_copy_chown = re.search(
        rf"COPY\s+--chown=executor(?::\S+)?\s+[^\n]*\b{LAUNCH_VSCODE_BASENAME}\b",
        text,
    )
    assert forbidden_copy_chown is None, (
        f"Dockerfile: `COPY --chown=executor:...` applied to launch_vscode.sh "
        f"({forbidden_copy_chown.group(0)!r}) — Codex H5 reopens; "
        f"must be `--chown=root:executor`"
    )

    has_root_chown = (
        re.search(
            rf"chown\s+root(?::\S+)?\s+[^\n]*\b{LAUNCH_VSCODE_BASENAME}\b",
            text,
        )
        is not None
        or re.search(
            rf"COPY\s+--chown=root(?::\S+)?\s+[^\n]*\b{LAUNCH_VSCODE_BASENAME}\b",
            text,
        )
        is not None
    )
    assert has_root_chown, (
        "Dockerfile: launch_vscode.sh must be chown'd to root "
        "(e.g. `root:executor`); Codex H5 fix missing"
    )

    forbidden_chmod = re.search(
        rf"chmod\s+0?755\b[^\n]*\b{LAUNCH_VSCODE_BASENAME}\b",
        text,
    )
    assert forbidden_chmod is None, (
        f"Dockerfile: `chmod 755` applied to launch_vscode.sh "
        f"({forbidden_chmod.group(0)!r}) — Codex H5 reopens; "
        f"must be `chmod 0750`"
    )

    required_chmod = re.search(
        rf"chmod\s+0?750\b[^\n]*\b{LAUNCH_VSCODE_BASENAME}\b",
        text,
    )
    assert required_chmod is not None, (
        "Dockerfile: launch_vscode.sh must be `chmod 0750` "
        "(root-own + executor read+exec only); Codex H5 fix missing"
    )


def test_start_sh_remains_root_owned() -> None:
    """Defense-in-depth: start.sh entrypoint must stay root-owned.

    `start.sh` is the container ENTRYPOINT and is read by `bash` only —
    if it gets chowned to `executor`, the analyzed extension can
    overwrite the entrypoint itself, defeating the W13-2 launch_vscode.sh
    ratchet via a different path.
    """

    text = _dockerfile_text()

    forbidden_run_chown = re.search(
        rf"chown\s+executor(?::\S+)?\s+[^\n]*\b{START_SH_BASENAME}\b",
        text,
    )
    assert forbidden_run_chown is None, (
        f"Dockerfile: `chown executor:...` applied to start.sh "
        f"({forbidden_run_chown.group(0)!r}) — root-own ratchet broken"
    )

    forbidden_copy_chown = re.search(
        rf"COPY\s+--chown=executor(?::\S+)?\s+[^\n]*\b{START_SH_BASENAME}\b",
        text,
    )
    assert forbidden_copy_chown is None, (
        f"Dockerfile: `COPY --chown=executor:...` applied to start.sh "
        f"({forbidden_copy_chown.group(0)!r}) — root-own ratchet broken"
    )


@pytest.mark.smoke
@pytest.mark.integration
def test_launch_vscode_runtime_ownership_and_mode_smoke() -> None:
    """Runtime invariant: launch_vscode.sh ships root:executor 0750 in image.

    Second layer to the static Dockerfile gate: after the image is built,
    does the file actually carry the expected ownership and mode? A
    Dockerfile edit can pass the static regex check while a broken RUN
    order silently reopens the gate at runtime; this test closes that
    blind spot.
    """

    docker_bin = _resolve_executor_container()
    result = subprocess.run(  # noqa: S603
        [
            docker_bin,
            "exec",
            "--user",
            "root",
            settings.executor.CONTAINER_NAME,
            "stat",
            "-c",
            "%U:%G %a",
            LAUNCH_VSCODE_PATH,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"stat failed (rc={result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stdout.strip() == "root:executor 750", (
        f"launch_vscode.sh runtime ownership/mode drifted: "
        f"{result.stdout.strip()!r} — Codex H5 invariant broken "
        f"(expected 'root:executor 750')"
    )


@pytest.mark.smoke
@pytest.mark.integration
def test_executor_cannot_overwrite_launch_vscode_smoke() -> None:
    """Exploit vector negative test: executor UID write attempt must reject.

    The actual Codex H5 threat model: a target extension running inside
    the container under the `executor` UID overwrites `launch_vscode.sh`,
    and the next `reset_state.launch_vscode()` invocation executes the
    payload. The static gate pins the `chown root:executor + chmod 0750`
    Dockerfile line; this test verifies that an actual write attempt
    under the executor UID is rejected by the kernel at runtime.
    """

    docker_bin = _resolve_executor_container()
    # USER executor (Dockerfile:145) → `docker exec` default UID executor.
    result = subprocess.run(  # noqa: S603
        [
            docker_bin,
            "exec",
            settings.executor.CONTAINER_NAME,
            "bash",
            "-c",
            f"echo evil >> {LAUNCH_VSCODE_PATH}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        "executor UID was able to append to launch_vscode.sh — "
        "Codex H5 exploit vector reopened"
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "Permission denied" in combined, (
        f"write rejection lacked permission-deny signal:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
