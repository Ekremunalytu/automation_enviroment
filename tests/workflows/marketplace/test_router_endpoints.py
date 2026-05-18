"""Tests for /api/marketplace/analyze + /api/marketplace/analyze/{id} endpoints (error paths + lifecycle).

Split from tests/workflows/marketplace/test_router.py during W16-6 to reduce single-file size.
Covers analyze error paths, start-job snapshot flow, cancel/status endpoints, theme-fixture integration.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from executor.host import ExecutorError
from workflows.marketplace import (
    analysis_service,
    router as marketplace_router,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ANALYZE_PAYLOAD = {
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
}


def _vsix_path_exists(exists: bool = True):
    """Return a mock Path whose .exists() returns the given value."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = exists
    mock_path.name = "ms-python.python-2025.0.0.vsix"
    return mock_path


def _resolve_exact_fixture(
    publisher: str,
    name: str,
    version: str,
) -> tuple[Path, Path]:
    extensions_dir = Path(marketplace_router.settings.project.EXTENSION_DIR)
    vsix_path = extensions_dir / f"{publisher}.{name}-{version}.vsix"
    extracted_dir = extensions_dir / f"{publisher}.{name}-{version}"
    if not vsix_path.exists():
        pytest.skip(f"{publisher}.{name} VSIX fixture is unavailable")
    if not extracted_dir.exists():
        pytest.skip(f"{publisher}.{name} extracted fixture directory is unavailable")
    return vsix_path, extracted_dir


def _scenario_zero_report_payload(target_extension_id: str) -> dict[str, object]:
    automation_health = {
        "status": "healthy",
        "reasons": [],
        "trigger_requested": False,
        "trigger_loaded": False,
        "trigger_applied": False,
        "extension_host_log_present": False,
        "extension_host_output_present": False,
        "target_stream_present": False,
        "target_activation_count": 0,
        "failed_scenarios": [],
        "extra_trigger_failures": [],
        "extra_trigger_failure_count": 0,
        "extension_host_log_found": False,
    }
    log_health = {
        "extension_host_log_found": False,
        "extension_host_output_present": False,
        "target_extension_log_entries": 0,
        "total_activation_entries": 0,
    }
    signal_summary = {
        "level": "benign",
        "score": 8,
        "note": "No executable surface was observed for the color-theme fixture.",
    }
    return {
        "report_version": 2,
        "target_extension_expected": target_extension_id,
        "target_extension_observed": False,
        "trigger_plan_requested": False,
        "trigger_plan_loaded": False,
        "trigger_plan_applied": False,
        "trigger_plan_path": "",
        "trigger_execution_mode": "skip_automation",
        "requested_scenarios": [],
        "failed_scenarios": [],
        "extra_trigger_failures": [],
        "verification_gap": 0,
        "heuristic_verification_gap": 0,
        "run_quality": "scenario_zero",
        "run_quality_reasons": [
            "No automation scenario was required for this non-executable fixture."
        ],
        "automation_health": automation_health,
        "log_health": log_health,
        "attribution_summary": {},
        "risk_signals": [],
        "risk_summary": {},
        "signal_summary": signal_summary,
        "summary": {
            "total_activated": 0,
            "unique_extensions": 0,
            "unique_event_extensions": 0,
            "running_extensions": 0,
            "monitoring_duration_s": 0.0,
            "monitoring_started_at": 0.0,
            "monitoring_ended_at": 0.0,
            "extension_ids": [],
            "scenarios_run": [],
            "failed_scenarios": [],
            "network_events": 0,
            "network_hosts": 0,
            "file_events": 0,
            "sensitive_file_events": 0,
            "target_file_events": 0,
            "target_network_events": 0,
            "attempted_capabilities": [],
            "verified_capabilities": [],
            "official_attempted_capabilities": [],
            "official_verified_capabilities": [],
            "heuristic_attempted_capabilities": [],
            "heuristic_verified_capabilities": [],
            "ui_blocker_count": 0,
            "target_extension_expected": target_extension_id,
            "target_extension_observed": False,
            "official_event_coverage": {},
            "heuristic_workflow_coverage": {},
            "trigger_execution_mode": "skip_automation",
            "trigger_plan_applied": False,
            "verification_gap": 0,
            "heuristic_verification_gap": 0,
            "run_quality": "scenario_zero",
            "automation_health": automation_health,
            "log_health": log_health,
            "attribution_summary": {},
            "risk_summary": {},
            "signal_summary": signal_summary,
        },
        "attempted_capabilities": [],
        "verified_capabilities": [],
        "official_attempted_capabilities": [],
        "official_verified_capabilities": [],
        "heuristic_attempted_capabilities": [],
        "heuristic_verified_capabilities": [],
        "network_capture_error": "",
        "file_capture_error": "",
        "file_capture_diagnostics": {},
        "activated": [],
        "running_extensions": [],
        "scenario_traces": [],
        "stimulus_passes": [],
        "prerequisite_results": [],
        "event_attempts": [],
        "evidence_events": [],
        "evidence_links": [],
        "network_events": [],
        "network_summary": {},
        "file_events": [],
        "file_summary": {},
        "coverage_summary": {},
        "coverage_matrix": [],
        "coverage_tracks": {},
        "official_event_coverage": {},
        "heuristic_workflow_coverage": {},
        "extension_host_output_lines": 0,
        "extension_host_output": "",
        "log_streams": {
            "automation": [],
            "target_extension_host": [],
            "other_extension_host": [],
        },
        "log_file": "",
    }


# ---------------------------------------------------------------------------
# Analyze Endpoint Tests — error paths + start/cancel/status lifecycle
# ---------------------------------------------------------------------------


def test_analyze_vsix_not_found_404(client: TestClient) -> None:
    """Missing .vsix file returns 404."""
    with patch(
        "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
        return_value=_vsix_path_exists(False),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 404
    assert "VSIX file not found" in response.json()["detail"]


def test_analyze_install_failure_502(client: TestClient) -> None:
    """ExecutorError during install returns 502."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=ExecutorError("Install failed", returncode=1, output="error"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "install extension" in response.json()["detail"].lower()


def test_analyze_automation_failure_502(client: TestClient) -> None:
    """ExecutorError during automation returns 502 with redacted detail."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=ExecutorError("Automation crashed", returncode=1, output="err"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail.startswith("Automation failed in sandbox.")
    assert "error_id=" in detail
    assert "Automation crashed" not in detail


@pytest.mark.integration
def test_theme_fixture_analysis_uses_scenario_zero_flow(
    db_client: TestClient,
    tmp_path: Path,
) -> None:
    publisher = "extrace"
    name = "fixture-theme"
    version = "0.0.1"
    target_extension_id = f"{publisher}.{name}"
    _vsix_path, extracted_dir = _resolve_exact_fixture(publisher, name, version)
    assert extracted_dir.exists()

    report_payload = _scenario_zero_report_payload(target_extension_id)
    original_output_dir = marketplace_router.settings.project.OUTPUT_DIR

    class ScenarioZeroExecutorControl:
        def reset_sandbox(self, reload_window: bool = True) -> str:
            assert reload_window is True
            return "Sandbox reset."

        def consume_harness_python_secret(self) -> str | None:
            return None

        def install_extension(
            self, install_publisher: str, install_name: str, install_version: str
        ) -> str:
            assert (install_publisher, install_name, install_version) == (
                publisher,
                name,
                version,
            )
            return "Extension installed successfully."

        def run_automation(
            self,
            *,
            report_path: str,
            scenario: str | None = None,
            trigger_container_path: str | None = None,
            skip_automation: bool = False,
            reload_before_run: bool = False,
            target_extension_id: str | None = None,
            harness_python_secret: str | None = None,
        ) -> str:
            assert scenario is None
            assert trigger_container_path is None
            assert skip_automation is True
            assert reload_before_run is True
            assert target_extension_id == f"{publisher}.{name}"
            assert harness_python_secret is None
            resolved_report_path = tmp_path / Path(report_path).name
            resolved_report_path.write_text(
                json.dumps(report_payload, indent=2),
                encoding="utf-8",
            )
            return "Automation skipped for scenario-zero analysis."

    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    try:
        with patch(
            "workflows.marketplace.analysis_service.default_executor_control",
            ScenarioZeroExecutorControl(),
        ):
            download_response = db_client.post(
                "/api/marketplace/download",
                json={
                    "publisher": publisher,
                    "name": name,
                    "version": version,
                },
            )
            assert download_response.status_code == 200

            response = db_client.post(
                "/api/marketplace/analyze",
                json={
                    "publisher": publisher,
                    "name": name,
                    "version": version,
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["report_path"].endswith(".json")
        assert "health=healthy" in payload["message"].lower()

        report_response = db_client.get(f"/api/activations/{payload['report_path']}")
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["target_extension_expected"] == target_extension_id
        assert report["trigger_execution_mode"] == "skip_automation"
        assert report["summary"]["scenarios_run"] == []
        assert report["summary"]["failed_scenarios"] == []
        assert report["scenario_traces"] == []
        assert report["stimulus_passes"] == []
        assert report["event_attempts"] == []
        assert report["run_quality"] == "scenario_zero"
        assert report["trigger_plan_requested"] is False
        assert report["trigger_plan_loaded"] is False
        assert report["trigger_plan_applied"] is False
        assert report["automation_health"]["status"] == "healthy"
        assert report["automation_health"]["target_activation_count"] == 0
    finally:
        marketplace_router.settings.project.OUTPUT_DIR = original_output_dir


def test_analyze_trigger_plan_failure_502(client: TestClient) -> None:
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=analysis_service.TriggerPlanError(
                "trigger_apply_failed",
                "Executor did not apply the trigger payload during sandbox automation.",
            ),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "trigger payload" in response.json()["detail"].lower()


def test_analyze_start_returns_job_snapshot(client: TestClient) -> None:
    """Async analyze start returns a queued job payload."""
    job_snapshot = {
        "job_id": "job-123",
        "status": "queued",
        "publisher": ANALYZE_PAYLOAD["publisher"],
        "name": ANALYZE_PAYLOAD["name"],
        "version": ANALYZE_PAYLOAD["version"],
        "scenario": None,
        "current_step": None,
        "message": "Queued for sandbox analysis.",
        "steps": [
            {"name": "reset_sandbox", "status": "pending", "message": "Waiting"},
            {"name": "install_extension", "status": "pending", "message": "Queued"},
            {"name": "build_triggers", "status": "pending", "message": "Waiting"},
            {"name": "run_monitoring", "status": "pending", "message": "Waiting"},
            {"name": "finalize_report", "status": "pending", "message": "Waiting"},
        ],
        "report_path": "activation_report_ms-python.python-2025.0.0-job123.json",
        "install_output": None,
        "automation_output": None,
        "error_detail": None,
        "error_code": None,
        "created_at": 1.0,
        "started_at": None,
        "finished_at": None,
        "updated_at": 1.0,
    }
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.job_service.reserve_job",
            return_value=job_snapshot,
        ),
        patch(
            "workflows.marketplace.router.job_service.get_job_snapshot",
            return_value=job_snapshot,
        ),
        patch("workflows.marketplace.router.threading.Thread") as mock_thread,
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["publisher"] == ANALYZE_PAYLOAD["publisher"]
    assert len(payload["steps"]) == 5
    assert payload["report_path"].startswith(
        "activation_report_ms-python.python-2025.0.0-"
    )
    mock_thread.return_value.start.assert_called_once()


def test_analyze_start_rejects_second_active_job(client: TestClient) -> None:
    """Single-sandbox mode should reject overlapping analysis jobs."""
    active_job = {"job_id": "running-job"}
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.job_service.reserve_job",
            side_effect=marketplace_router.job_service.ActiveAnalysisJobError(
                active_job
            ),
        ),
        patch("workflows.marketplace.router.threading.Thread") as mock_thread,
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 409
    assert "already in progress" in response.json()["detail"].lower()
    mock_thread.return_value.start.assert_not_called()


def test_analyze_start_missing_vsix_404(client: TestClient) -> None:
    """Async analyze start validates the VSIX before queueing a job."""
    with patch(
        "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
        return_value=_vsix_path_exists(False),
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 404
    assert "VSIX file not found" in response.json()["detail"]


def test_cancel_analysis_job_returns_cancelled_snapshot(client: TestClient) -> None:
    cancelled_snapshot = {
        "job_id": "job-456",
        "status": "cancelled",
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "scenario": None,
        "current_step": "run_monitoring",
        "message": "Cancelled by user.",
        "steps": [
            {"name": "reset_sandbox", "status": "completed", "message": "ok"},
            {"name": "install_extension", "status": "completed", "message": "ok"},
            {"name": "build_triggers", "status": "completed", "message": "ok"},
            {
                "name": "run_monitoring",
                "status": "cancelled",
                "message": "Cancelled by user.",
            },
            {"name": "finalize_report", "status": "skipped", "message": "Skipped"},
        ],
        "report_path": "activation_report_ms-python.python-2025.0.0-job456.json",
        "install_output": None,
        "automation_output": None,
        "error_detail": "Cancelled by user.",
        "error_code": "cancelled_by_user",
        "created_at": 1.0,
        "started_at": 2.0,
        "finished_at": 3.0,
        "updated_at": 3.0,
    }
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        return_value=cancelled_snapshot,
    ) as mock_cancel:
        response = client.post("/api/marketplace/analyze/job-456/cancel")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["error_code"] == "cancelled_by_user"
    assert body["steps"][3]["status"] == "cancelled"
    mock_cancel.assert_called_once()


@pytest.mark.parametrize("terminal_status", ["completed", "failed", "cancelled"])
def test_cancel_analysis_job_terminal_returns_409(
    client: TestClient, terminal_status: str
) -> None:
    """A cancel request that races against any terminal-state transition
    surfaces 409 with the offending status preserved in the detail. Mirrors
    the CRUD-level cancel-after-finish race coverage; closes the router-side
    half of POST_POC_BACKLOG `[FOLLOWUP simulation-progress-cancel]`
    cancel-after-finish race gap."""
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        side_effect=marketplace_router.JobNotCancellableError(
            "job-789", terminal_status
        ),
    ):
        response = client.post("/api/marketplace/analyze/job-789/cancel")

    assert response.status_code == 409
    detail = response.json()["detail"].lower()
    assert "terminal status" in detail
    assert terminal_status in detail


# ---------------------------------------------------------------------------
# W13-3 (Codex H4) — `cancelling` non-terminal state exposed through the
# cancel + status endpoints. Originally W13-3.2 @pytest.mark.skip RED
# precursors; W13-3.5 (worker integration + AnalyzeJobStatusResponse
# Pydantic literal extension from W13-3.3) makes both cases green.
# ---------------------------------------------------------------------------


def test_cancel_analysis_job_returns_200_with_cancelling_snapshot(
    client: TestClient,
) -> None:
    cancelling_snapshot = {
        "job_id": "job-w13-3-drain",
        "status": "cancelling",
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "scenario": None,
        "current_step": "run_monitoring",
        "message": "Cancel signalled; worker draining.",
        "steps": [
            {"name": "reset_sandbox", "status": "completed", "message": "ok"},
            {"name": "install_extension", "status": "completed", "message": "ok"},
            {"name": "build_triggers", "status": "completed", "message": "ok"},
            {
                "name": "run_monitoring",
                "status": "running",
                "message": "Sandbox automation is still running inside the executor.",
            },
            {"name": "finalize_report", "status": "pending", "message": "Queued."},
        ],
        "report_path": "activation_report.json",
        "install_output": None,
        "automation_output": None,
        "error_detail": "Cancelled by user.",
        "error_code": "cancelled_by_user",
        "created_at": 1.0,
        "started_at": 2.0,
        "finished_at": None,  # draining — not yet terminal
        "updated_at": 3.0,
        "requested_cancel_at": 3.0,
    }
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        return_value=cancelling_snapshot,
    ) as mock_cancel:
        response = client.post("/api/marketplace/analyze/job-w13-3-drain/cancel")

    assert response.status_code == 200
    body = response.json()
    # The cancel API is no longer atomic-terminal: it signals a drain.
    assert body["status"] == "cancelling"
    assert body["finished_at"] is None
    assert body["error_code"] == "cancelled_by_user"
    # Step records are NOT yet finalized — worker still owns them.
    assert body["steps"][3]["status"] == "running"
    mock_cancel.assert_called_once()


def test_status_endpoint_exposes_cancelling_state_for_polling_clients(
    client: TestClient,
) -> None:
    cancelling_snapshot = {
        "job_id": "job-w13-3-poll",
        "status": "cancelling",
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "scenario": None,
        "current_step": "install_extension",
        "message": "Cancel signalled; worker draining install_extension.",
        "steps": [
            {"name": "reset_sandbox", "status": "completed", "message": "ok"},
            {
                "name": "install_extension",
                "status": "running",
                "message": "Installing extension VSIX.",
            },
            {"name": "build_triggers", "status": "pending", "message": "Queued."},
            {"name": "run_monitoring", "status": "pending", "message": "Queued."},
            {"name": "finalize_report", "status": "pending", "message": "Queued."},
        ],
        "report_path": "activation_report.json",
        "install_output": None,
        "automation_output": None,
        "error_detail": "Cancelled by user.",
        "error_code": "cancelled_by_user",
        "created_at": 1.0,
        "started_at": 2.0,
        "finished_at": None,
        "updated_at": 3.0,
        "requested_cancel_at": 3.0,
    }
    with patch(
        "workflows.marketplace.router.job_service.get_job_snapshot",
        return_value=cancelling_snapshot,
    ):
        response = client.get("/api/marketplace/analyze/job-w13-3-poll")

    assert response.status_code == 200
    body = response.json()
    # The polling-client contract: `cancelling` reaches the wire (UI can
    # render "Stopping…"); polling loop keeps polling because the row is
    # not yet terminal.
    assert body["status"] == "cancelling"
    assert body["finished_at"] is None


def test_cancel_analysis_job_unknown_returns_404(client: TestClient) -> None:
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        side_effect=KeyError("job-missing"),
    ):
        response = client.post("/api/marketplace/analyze/job-missing/cancel")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_analysis_job_status_404(client: TestClient) -> None:
    """Unknown analysis jobs return 404."""
    with patch(
        "workflows.marketplace.router.job_service.get_job_snapshot",
        side_effect=KeyError("missing-job"),
    ):
        response = client.get("/api/marketplace/analyze/missing-job")
    assert response.status_code == 404


def test_analyze_missing_publisher_422(client: TestClient) -> None:
    """Missing publisher field returns 422."""
    response = client.post(
        "/api/marketplace/analyze",
        json={"name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422
