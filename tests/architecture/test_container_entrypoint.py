"""W9-5 architecture regression: container import-mode contract.

ADR 0008 §6 declares paket-mode invocation
(`python -m executor.flows.playwright.entrypoint`) as the sole supported
container entry path. AST gates in `test_import_graph.py` lock the source
contract (no dual-import fallback, no `sys.path.insert`); this test locks
the runtime layer the AST gates cannot reach: package-mode invocation must
succeed inside the live container, and flat-path script invocation
(`python /home/executor/flows/playwright/entrypoint.py`) must reject.

Tests skip when docker is unavailable or the executor container is not
running, so local pre-push remains ergonomic; the live signal triggers
when `make exec-up` has provisioned the container.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from appcore.api.config import settings


def _resolve_executor_container() -> str:
    """Skip-or-return absolute docker binary path with running container."""
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


@pytest.mark.smoke
@pytest.mark.integration
def test_package_mode_import_succeeds_in_container() -> None:
    docker_bin = _resolve_executor_container()
    result = subprocess.run(  # noqa: S603
        [
            docker_bin,
            "exec",
            settings.executor.CONTAINER_NAME,
            "python3",
            "-c",
            f"import {settings.executor.ENTRYPOINT_MODULE}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"package-mode import failed (rc={result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.smoke
@pytest.mark.integration
def test_flat_mode_invocation_fails_in_container() -> None:
    """Defensive: invoking entrypoint as a flat path script must error.

    Sibling imports inside `executor/flows/playwright/` are package-relative
    after W9-3, so a `python /home/.../entrypoint.py` invocation hits
    ImportError or ModuleNotFoundError at module load. This regression test
    breaks if a future change re-introduces flat-path support (sys.path
    fallback, dual-import, or absolute-pathed module reference).
    """
    docker_bin = _resolve_executor_container()
    flat_path = f"{settings.executor.PLAYWRIGHT_FLOW_DIR}/entrypoint.py"
    result = subprocess.run(  # noqa: S603
        [
            docker_bin,
            "exec",
            settings.executor.CONTAINER_NAME,
            "python3",
            flat_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        "flat-mode invocation unexpectedly succeeded — paket-mode "
        "invariant broken (ADR 0008 §6)"
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "ImportError" in combined or "ModuleNotFoundError" in combined, (
        "flat-mode rejection lacked import-error signal:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
