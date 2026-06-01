from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from workflows.marketplace.analysis_errors import ActivationReportLoadError
from workflows.marketplace.analysis_reports import (
    load_report_payload,
    load_static_report_from_name,
)
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


def test_completed_marketplace_job_reports_unreadable_activation_report(
    client: TestClient,
    tmp_path: Path,
) -> None:
    report_name = "activation_report_corrupt.json"
    (tmp_path / report_name).write_text("{not-json", encoding="utf-8")
    snapshot = {
        "job_id": "job-corrupt",
        "status": "completed",
        "publisher": "extrace",
        "name": "fixture-chat",
        "version": "0.0.1",
        "scenario": None,
        "current_step": "finalize_report",
        "message": "Completed.",
        "steps": [],
        "report_path": report_name,
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
            "workflows.marketplace.analysis_reports.settings.project.OUTPUT_DIR",
            str(tmp_path),
        ),
    ):
        response = client.get("/api/marketplace/analyze/job-corrupt")

    assert response.status_code == 200
    payload = response.json()
    assert payload["detection_report"] is None
    assert payload["report_error"] == (
        f"activation_report_schema_invalid: "
        f"Activation report {report_name} is not valid JSON."
    )


def test_activation_report_loader_raises_on_invalid_json(tmp_path: Path) -> None:
    report_name = "activation_report_corrupt.json"
    (tmp_path / report_name).write_text("{not-json", encoding="utf-8")

    with patch(
        "workflows.marketplace.analysis_reports.settings.project.OUTPUT_DIR",
        str(tmp_path),
    ):
        with pytest.raises(ActivationReportLoadError) as excinfo:
            load_report_payload(report_name)
    assert str(excinfo.value) == f"Activation report {report_name} is not valid JSON."


# ---------------------------------------------------------------------------
# ES-5: load_static_report_from_name (read-side graceful degradation)
# ---------------------------------------------------------------------------


def _write_static_bundle(directory: Path, name: str, *, decision: str) -> None:
    """Write a static-only CombinedAnalysisBundle (dynamic_bundle None) to disk."""
    from appcore.contracts.schema_defs.static_analysis_bundle import (
        CombinedAnalysisBundle,
        StaticAnalysisReport,
    )
    from packages.analysis_contracts.static_detection import (
        StaticDetectionReport,
        StaticGateDecision,
        StaticGateOutcome,
    )

    outcome = (
        StaticGateOutcome(
            decision=StaticGateDecision.WARN,
            warned_by=["extrace.s3.unusual_file_signature"],
        )
        if decision == "warn"
        else StaticGateOutcome(decision=StaticGateDecision.ALLOW, allow_reason="clean")
    )
    bundle = CombinedAnalysisBundle(
        static_report=StaticAnalysisReport(
            detection_report=StaticDetectionReport(), gate_outcome=outcome
        ),
        dynamic_bundle=None,
    )
    (directory / name).write_text(bundle.model_dump_json(indent=2), encoding="utf-8")


def test_load_static_report_returns_report_for_valid_bundle(tmp_path: Path) -> None:
    from packages.analysis_contracts.static_detection import StaticGateDecision

    name = "static_report_job-valid.json"
    _write_static_bundle(tmp_path, name, decision="warn")

    with patch(
        "workflows.marketplace.analysis_reports.settings.project.OUTPUT_DIR",
        str(tmp_path),
    ):
        report = load_static_report_from_name(name)

    assert report is not None
    assert report.gate_outcome.decision is StaticGateDecision.WARN
    assert report.gate_outcome.warned_by == ["extrace.s3.unusual_file_signature"]


def test_load_static_report_returns_none_for_missing_file(tmp_path: Path) -> None:
    with patch(
        "workflows.marketplace.analysis_reports.settings.project.OUTPUT_DIR",
        str(tmp_path),
    ):
        assert load_static_report_from_name("static_report_absent.json") is None


def test_load_static_report_returns_none_for_garbage_json(tmp_path: Path) -> None:
    name = "static_report_garbage.json"
    (tmp_path / name).write_text("{not json", encoding="utf-8")

    with patch(
        "workflows.marketplace.analysis_reports.settings.project.OUTPUT_DIR",
        str(tmp_path),
    ):
        # Read-side graceful degradation: a corrupt static artifact surfaces as
        # "no static report" (the router records a report_error note), never an
        # exception — distinct from the producer-side fail-closed StaticReportError.
        assert load_static_report_from_name(name) is None


def test_load_static_report_returns_none_for_schema_invalid_body(
    tmp_path: Path,
) -> None:
    import json

    name = "static_report_wrong_shape.json"
    # Valid JSON, but not a CombinedAnalysisBundle (missing static_report).
    (tmp_path / name).write_text(json.dumps({"foo": "bar"}), encoding="utf-8")

    with patch(
        "workflows.marketplace.analysis_reports.settings.project.OUTPUT_DIR",
        str(tmp_path),
    ):
        assert load_static_report_from_name(name) is None
