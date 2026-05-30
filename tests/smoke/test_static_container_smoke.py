"""ES-2 smoke acceptance: static-analyzer container bring-up + stub run.

``@pytest.mark.smoke`` — runs under ``make test-smoke`` (``-m smoke``); skipped
by the default lane / ``make check-all`` (``-m "not smoke"``). Requires the
``static_analyzer`` container running (``make static-up``); skips cleanly
otherwise (pattern from ``tests/architecture/test_container_entrypoint.py``).
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from executor.config import settings

pytestmark = [pytest.mark.smoke, pytest.mark.integration]

_CONTAINER = settings.static_analyzer.CONTAINER_NAME


def _docker_or_skip() -> str:
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        pytest.skip("docker unavailable; static smoke acceptance skipped")
    result = subprocess.run(  # noqa: S603
        [docker_bin, "inspect", "-f", "{{.State.Running}}", _CONTAINER],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        pytest.skip(f"{_CONTAINER} not running; run `make static-up` first")
    return docker_bin


def test_static_runtime_imports_in_container() -> None:
    """``import static_runtime`` succeeds inside the minimal hardened image."""
    docker_bin = _docker_or_skip()
    result = subprocess.run(  # noqa: S603
        [docker_bin, "exec", _CONTAINER, "python3", "-c", "import static_runtime"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"static_runtime import failed in container (rc={result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_static_runtime_stub_writes_empty_report() -> None:
    """The stub writes a valid, empty ``StaticDetectionReport`` to the report path."""
    docker_bin = _docker_or_skip()
    report_path = "/tmp/es2_smoke_report.json"  # noqa: S108 — container-side tmp
    run = subprocess.run(  # noqa: S603
        [
            docker_bin,
            "exec",
            _CONTAINER,
            "python3",
            "-m",
            "static_runtime",
            "--vsix-dir",
            "/extensions-input",
            "--report-path",
            report_path,
            "--rules-version",
            "0.0.0",
            "--timeout-budget-s",
            "30",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, f"stub run failed:\nstderr: {run.stderr}"

    cat = subprocess.run(  # noqa: S603
        [docker_bin, "exec", _CONTAINER, "cat", report_path],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cat.returncode == 0, f"could not read report:\nstderr: {cat.stderr}"
    doc = json.loads(cat.stdout)
    assert doc["findings"] == []
    assert doc["tool_executions"] == []
    assert doc["schema_version"] == "1"
