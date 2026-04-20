from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from workflows.marketplace.analysis_service import run_local_analysis

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_completed_marketplace_job_exposes_detection_report(
    client: TestClient,
) -> None:
    bundle = run_local_analysis(
        REPO_ROOT / "extensions" / "malicious" / "t1-a1-credential-read-canary"
    )
    snapshot = {
        "job_id": "job-1",
        "status": "completed",
        "publisher": "extrace",
        "name": "t1-a1-credential-read-canary",
        "version": "0.0.1",
        "scenario": None,
        "current_step": "finalize_report",
        "message": "Completed.",
        "steps": [],
        "report_path": "activation_report_fixture_bundle.json",
        "install_output": "installed",
        "automation_output": "ran",
        "error_detail": None,
        "error_code": None,
        "created_at": 1.0,
        "started_at": 2.0,
        "finished_at": 3.0,
        "updated_at": 3.0,
    }

    with (
        patch(
            "workflows.marketplace.router.job_service.get_job_snapshot",
            return_value=snapshot,
        ),
        patch(
            "workflows.marketplace.router.build_analysis_bundle_from_report_name",
            return_value=bundle,
        ),
    ):
        response = client.get("/api/marketplace/analyze/job-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["detection_report"]["findings"]
    assert payload["detection_report"]["verdict"] == "malicious"
