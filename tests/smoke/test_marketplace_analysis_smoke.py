from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from appcore.api.config import settings
from packages.analysis_contracts import activation_report_invariant_issues
from workflows.marketplace.trigger_service import TriggerPlan

_PUBLISHER = "ms-python"
_NAME = "python"
_FIXTURE_PREFIX = f"{_PUBLISHER}.{_NAME}-"
_CHAT_PUBLISHER = "extrace"
_CHAT_NAME = "fixture-chat"
_CHAT_VERSION = "0.0.1"
_SMOKE_SCENARIO = "coding_session"
# The host-side monitored automation ceiling is 1800s. Leave bounded headroom
# for reset/install/report-finalization so the smoke harness does not abandon a
# healthy layered run while the executor still owns the single-active slot.
_POLL_TIMEOUT_S = 2100
_POLL_INTERVAL_S = 5
_STAGNATION_TIMEOUT_S = 120
_CANCEL_DRAIN_TIMEOUT_S = 45
_DIAGNOSTIC_LOG_LINES = 120
_TERMINAL_JOB_STATUSES = {
    "cancelled",
    "completed",
    "failed",
    "rejected_static",
}


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


def _resolve_exact_fixture(
    publisher: str,
    name: str,
    version: str,
) -> tuple[Path, Path]:
    extensions_dir = Path(settings.project.EXTENSION_DIR)
    vsix_path = extensions_dir / f"{publisher}.{name}-{version}.vsix"
    extracted_dir = extensions_dir / f"{publisher}.{name}-{version}"
    if not vsix_path.exists():
        pytest.skip(f"{publisher}.{name} VSIX fixture is unavailable")
    if not extracted_dir.exists():
        pytest.skip(f"{publisher}.{name} extracted fixture directory is unavailable")
    return vsix_path, extracted_dir


def _run_diagnostic_command(args: list[str]) -> str:
    result = subprocess.run(  # noqa: S603
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    chunks = [f"$ {' '.join(args)}", f"rc={result.returncode}"]
    if stdout:
        chunks.append(f"stdout:\n{stdout}")
    if stderr:
        chunks.append(f"stderr:\n{stderr}")
    if not stdout and not stderr:
        chunks.append("output: <empty>")
    return "\n".join(chunks)


def _executor_process_snapshot() -> str:
    docker_path = shutil.which("docker")
    if docker_path is None:
        return "docker is unavailable"

    return _run_diagnostic_command(
        [
            docker_path,
            "exec",
            settings.executor.CONTAINER_NAME,
            "ps",
            "-o",
            "pid=,etime=,command=",
            "-C",
            "python3",
        ]
    )


def _executor_log_tail() -> str:
    docker_path = shutil.which("docker")
    if docker_path is None:
        return "docker is unavailable"

    return _run_diagnostic_command(
        [
            docker_path,
            "logs",
            "--tail",
            str(_DIAGNOSTIC_LOG_LINES),
            settings.executor.CONTAINER_NAME,
        ]
    )


def _smoke_diagnostics(job_id: str, payload: dict[str, object] | None) -> str:
    rendered_payload = json.dumps(
        payload or {"status": "unknown"},
        indent=2,
        sort_keys=True,
        default=str,
    )
    return (
        f"analysis job {job_id} did not complete successfully.\n"
        f"last payload:\n{rendered_payload}\n\n"
        f"executor processes:\n{_executor_process_snapshot()}\n\n"
        f"executor logs:\n{_executor_log_tail()}"
    )


def _cancel_and_drain_job(
    client: TestClient,
    job_id: str,
) -> dict[str, object] | None:
    """Release the single-active slot before a timed-out smoke test fails."""
    cancel_response = client.post(f"/api/marketplace/analyze/{job_id}/cancel")
    assert cancel_response.status_code in {200, 409}

    deadline = time.time() + _CANCEL_DRAIN_TIMEOUT_S
    last_payload: dict[str, object] | None = None
    while time.time() < deadline:
        response = client.get(f"/api/marketplace/analyze/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)
        last_payload = payload
        if payload.get("status") in _TERMINAL_JOB_STATUSES:
            return payload
        time.sleep(_POLL_INTERVAL_S)
    return last_payload


def _poll_job(client: TestClient, job_id: str) -> dict[str, object]:
    deadline = time.time() + _POLL_TIMEOUT_S
    last_payload: dict[str, object] | None = None
    last_progress_key: tuple[object, ...] | None = None
    stagnant_for_s = 0
    while time.time() < deadline:
        response = client.get(f"/api/marketplace/analyze/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)
        last_payload = payload
        if payload.get("status") in _TERMINAL_JOB_STATUSES:
            return payload

        progress_key = (
            payload.get("status"),
            payload.get("current_step"),
            payload.get("updated_at"),
            payload.get("error_detail"),
        )
        if progress_key == last_progress_key:
            stagnant_for_s += _POLL_INTERVAL_S
        else:
            last_progress_key = progress_key
            stagnant_for_s = 0

        if stagnant_for_s >= _STAGNATION_TIMEOUT_S:
            drained_payload = _cancel_and_drain_job(client, job_id)
            pytest.fail(_smoke_diagnostics(job_id, drained_payload or payload))
        time.sleep(_POLL_INTERVAL_S)

    drained_payload = _cancel_and_drain_job(client, job_id)
    pytest.fail(
        f"analysis job {job_id} timed out after {_POLL_TIMEOUT_S}s.\n\n"
        f"{_smoke_diagnostics(job_id, drained_payload or last_payload)}"
    )


def _assert_completed_job(job_id: str, payload: dict[str, object]) -> None:
    assert payload["status"] == "completed", _smoke_diagnostics(job_id, payload)


def _skip_if_executor_reset_failed(payload: dict[str, object]) -> None:
    if payload.get("status") != "failed":
        return
    error_detail = str(payload.get("error_detail", "") or "")
    if "reload_vscode" not in error_detail:
        return
    pytest.skip(
        "executor reset failed before the smoke scenario could run; "
        "skipping behavior-specific validation."
    )


@pytest.fixture(autouse=True)
def _isolate_dynamic_executor_smoke(
    monkeypatch: pytest.MonkeyPatch,
    runtime_client: TestClient,
) -> Generator[None, None, None]:
    """Run this dynamic-executor lane independently from the static gate."""
    previous_response = runtime_client.get("/api/settings/executor/preferences")
    assert previous_response.status_code == 200
    previous_enabled = bool(
        previous_response.json().get("dynamic_analysis_enabled", False)
    )

    monkeypatch.setattr(settings.static_analysis, "ENABLED", False)
    enabled_response = runtime_client.put(
        "/api/settings/executor/preferences",
        json={
            "dynamic_analysis_enabled": True,
            "updated_by": "dynamic-smoke",
        },
    )
    assert enabled_response.status_code == 200
    yield
    restored_response = runtime_client.put(
        "/api/settings/executor/preferences",
        json={
            "dynamic_analysis_enabled": previous_enabled,
            "updated_by": "dynamic-smoke-restore",
        },
    )
    assert restored_response.status_code == 200


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.slow
def test_ms_python_analysis_smoke(runtime_client: TestClient) -> None:
    _require_executor_container()
    version, _vsix_path, extracted_dir = _resolve_ms_python_fixture()
    assert extracted_dir.exists()

    download_response = runtime_client.post(
        "/api/marketplace/download",
        json={"publisher": _PUBLISHER, "name": _NAME, "version": version},
    )
    assert download_response.status_code == 200

    start_response = runtime_client.post(
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
    completed_job = _poll_job(runtime_client, str(job["job_id"]))

    _skip_if_executor_reset_failed(completed_job)
    _assert_completed_job(str(job["job_id"]), completed_job)
    report_name = str(completed_job["report_path"])
    report_response = runtime_client.get(f"/api/activations/{report_name}")
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
    assert activation_report_invariant_issues(report) == []
    assert report["summary"]["scenarios_run"] == [_SMOKE_SCENARIO]


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.slow
def test_ms_python_layered_analysis_smoke_never_reads_as_clean_when_chat_tool_verification_is_open(
    runtime_client: TestClient,
) -> None:
    _require_executor_container()
    version, _vsix_path, extracted_dir = _resolve_ms_python_fixture()
    assert extracted_dir.exists()

    download_response = runtime_client.post(
        "/api/marketplace/download",
        json={"publisher": _PUBLISHER, "name": _NAME, "version": version},
    )
    assert download_response.status_code == 200

    start_response = runtime_client.post(
        "/api/marketplace/analyze/start",
        json={
            "publisher": _PUBLISHER,
            "name": _NAME,
            "version": version,
        },
    )
    assert start_response.status_code == 202
    job = start_response.json()
    completed_job = _poll_job(runtime_client, str(job["job_id"]))

    _skip_if_executor_reset_failed(completed_job)
    _assert_completed_job(str(job["job_id"]), completed_job)
    report_name = str(completed_job["report_path"])
    report_response = runtime_client.get(f"/api/activations/{report_name}")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["trigger_execution_mode"] == "layered_passes"
    assert activation_report_invariant_issues(report) == []

    chat_tool_attempts = [
        item
        for item in report.get("event_attempts", [])
        if item.get("official")
        and item.get("event_family") in {"onChatParticipant", "onLanguageModelTool"}
    ]
    assert chat_tool_attempts

    unresolved_chat_tool_attempts = [
        item for item in chat_tool_attempts if item.get("status") != "verified"
    ]
    if unresolved_chat_tool_attempts:
        assert report["automation_health"]["status"] != "healthy"
        assert report["run_quality"] == "low"


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.slow
def test_fixture_chat_analysis_smoke(runtime_client: TestClient) -> None:
    _require_executor_container()
    _vsix_path, extracted_dir = _resolve_exact_fixture(
        _CHAT_PUBLISHER,
        _CHAT_NAME,
        _CHAT_VERSION,
    )
    assert extracted_dir.exists()

    download_response = runtime_client.post(
        "/api/marketplace/download",
        json={
            "publisher": _CHAT_PUBLISHER,
            "name": _CHAT_NAME,
            "version": _CHAT_VERSION,
        },
    )
    assert download_response.status_code == 200

    start_response = runtime_client.post(
        "/api/marketplace/analyze/start",
        json={
            "publisher": _CHAT_PUBLISHER,
            "name": _CHAT_NAME,
            "version": _CHAT_VERSION,
        },
    )
    assert start_response.status_code == 202
    job = start_response.json()
    completed_job = _poll_job(runtime_client, str(job["job_id"]))

    _skip_if_executor_reset_failed(completed_job)
    _assert_completed_job(str(job["job_id"]), completed_job)
    report_name = str(completed_job["report_path"])
    report_response = runtime_client.get(f"/api/activations/{report_name}")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["target_extension_expected"] == "extrace.fixture-chat"
    assert report["target_extension_observed"] is True
    assert report["trigger_execution_mode"] == "layered_passes"
    assert report["automation_health"]["status"] in {"healthy", "degraded"}
    assert report["automation_health"]["status"] != "inconclusive"
    assert report["automation_health"]["target_activation_count"] >= 1
    assert activation_report_invariant_issues(report) == []
    assert any(
        item.get("official") and item.get("event_family") == "onChatParticipant"
        for item in report.get("event_attempts", [])
    )


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.slow
def test_missing_trigger_payload_never_looks_benign(runtime_client: TestClient) -> None:
    _require_executor_container()
    version, _vsix_path, _extracted_dir = _resolve_ms_python_fixture()

    with patch(
        "workflows.marketplace.analysis_service.build_trigger_payload",
        return_value=TriggerPlan(
            trigger_container_path="/results/missing-trigger-payload.json",
            selected_scenarios=["coding_session"],
            skip_automation=False,
            reason_code="generated_trigger_plan",
            message="Trigger requested for ms-python.python with a missing payload.",
        ),
    ):
        start_response = runtime_client.post(
            "/api/marketplace/analyze/start",
            json={"publisher": _PUBLISHER, "name": _NAME, "version": version},
        )
        assert start_response.status_code == 202
        job = start_response.json()
        completed_job = _poll_job(runtime_client, str(job["job_id"]))

    _skip_if_executor_reset_failed(completed_job)
    _assert_completed_job(str(job["job_id"]), completed_job)
    report_name = str(completed_job["report_path"])
    report_response = runtime_client.get(f"/api/activations/{report_name}")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["automation_health"]["status"] in {"degraded", "inconclusive"}
    assert report["signal_summary"]["level"] != "benign"
