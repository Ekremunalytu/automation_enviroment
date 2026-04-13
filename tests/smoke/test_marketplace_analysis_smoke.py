from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from appcore.api.config import settings

_PUBLISHER = "ms-python"
_NAME = "python"
_FIXTURE_PREFIX = f"{_PUBLISHER}.{_NAME}-"
_SMOKE_SCENARIO = "coding_session"
_POLL_TIMEOUT_S = 420
_POLL_INTERVAL_S = 5


def _require_executor_container() -> None:
    docker_path = shutil.which("docker")
    if docker_path is None:
        pytest.skip("docker is unavailable; smoke acceptance requires the executor")

    result = subprocess.run(  # noqa: S603
        [
            docker_path,
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
        pytest.skip("executor container is not running; smoke acceptance skipped")


def _resolve_ms_python_fixture() -> tuple[str, Path, Path]:
    extensions_dir = Path(settings.project.EXTENSION_DIR)
    matches = sorted(extensions_dir.glob(f"{_FIXTURE_PREFIX}*.vsix"))
    if not matches:
        pytest.skip("ms-python.python VSIX fixture is unavailable")

    vsix_path = matches[-1]
    version = vsix_path.stem.replace(_FIXTURE_PREFIX, "", 1)
    extracted_dir = extensions_dir / f"{_PUBLISHER}.{_NAME}-{version}"
    if not extracted_dir.exists():
        pytest.skip("ms-python.python extracted fixture directory is unavailable")
    return version, vsix_path, extracted_dir


def _poll_job(client: TestClient, job_id: str) -> dict[str, object]:
    deadline = time.time() + _POLL_TIMEOUT_S
    last_payload: dict[str, object] | None = None
    while time.time() < deadline:
        response = client.get(f"/api/marketplace/analyze/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)
        last_payload = payload
        if payload.get("status") in {"completed", "failed"}:
            return payload
        time.sleep(_POLL_INTERVAL_S)

    pytest.fail(f"analysis job {job_id} timed out: {last_payload}")


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.slow
def test_ms_python_analysis_smoke(client: TestClient) -> None:
    _require_executor_container()
    version, _vsix_path, extracted_dir = _resolve_ms_python_fixture()
    assert extracted_dir.exists()

    download_response = client.post(
        "/api/marketplace/download",
        json={"publisher": _PUBLISHER, "name": _NAME, "version": version},
    )
    assert download_response.status_code == 200

    start_response = client.post(
        "/api/marketplace/analyze/start",
        json={
            "publisher": _PUBLISHER,
            "name": _NAME,
            "version": version,
            "scenario": _SMOKE_SCENARIO,
        },
    )
    assert start_response.status_code == 202
    job = start_response.json()
    completed_job = _poll_job(client, str(job["job_id"]))

    assert completed_job["status"] == "completed", completed_job.get("error_detail")
    report_name = str(completed_job["report_path"])
    report_response = client.get(f"/api/activations/{report_name}")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["target_extension_expected"] == "ms-python.python"
    assert report["target_extension_observed"] is True
    assert report["automation_health"]["status"] in {"healthy", "degraded"}
    assert report["automation_health"]["status"] != "inconclusive"
    assert report["automation_health"]["target_activation_count"] >= 1
    assert report["automation_health"]["extension_host_output_present"] is True
    assert report["automation_health"]["target_stream_present"] is True
    assert any(
        entry["extension_id"] == "ms-python.python"
        for entry in report.get("activated", [])
    )
    assert report["log_streams"]["target_extension_host"]
    assert report["summary"]["scenarios_run"] == [_SMOKE_SCENARIO]


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.slow
def test_missing_trigger_payload_never_looks_benign(client: TestClient) -> None:
    _require_executor_container()
    version, _vsix_path, _extracted_dir = _resolve_ms_python_fixture()

    with patch(
        "workflows.marketplace.analysis_service.build_trigger_payload",
        return_value=(
            "/results/missing-trigger-payload.json",
            ["coding_session"],
            "Trigger requested for ms-python.python with a missing payload.",
        ),
    ):
        start_response = client.post(
            "/api/marketplace/analyze/start",
            json={"publisher": _PUBLISHER, "name": _NAME, "version": version},
        )
        assert start_response.status_code == 202
        job = start_response.json()
        completed_job = _poll_job(client, str(job["job_id"]))

    assert completed_job["status"] == "completed", completed_job.get("error_detail")
    report_name = str(completed_job["report_path"])
    report_response = client.get(f"/api/activations/{report_name}")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["automation_health"]["status"] in {"degraded", "inconclusive"}
    assert report["verdict"]["level"] != "benign"
