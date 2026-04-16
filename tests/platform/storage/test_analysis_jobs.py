from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from workflows.marketplace import job_service

pytestmark = pytest.mark.requires_db


def _request(**overrides: object) -> AnalyzeRequest:
    payload: dict[str, object] = {
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "scenario": None,
        "analysis_profile": None,
    }
    payload.update(overrides)
    return AnalyzeRequest(**payload)


def test_reserve_job_persists_snapshot_and_reads_after_session_clear(
    db_session: Session,
) -> None:
    job = job_service.reserve_job(_request(), db=db_session)

    db_session.expunge_all()
    persisted = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)

    assert persisted["job_id"] == job["job_id"]
    assert persisted["status"] == "queued"
    assert persisted["publisher"] == "ms-python"
    assert persisted["steps"][0]["name"] == "reset_sandbox"


def test_reserve_job_rejects_second_active_job(db_session: Session) -> None:
    first_job = job_service.reserve_job(_request(), db=db_session)

    with pytest.raises(job_service.ActiveAnalysisJobError) as exc_info:
        job_service.reserve_job(_request(name="python-alt"), db=db_session)

    assert exc_info.value.active_job["job_id"] == first_job["job_id"]


def test_update_job_step_transitions_current_step(db_session: Session) -> None:
    job = job_service.reserve_job(_request(), db=db_session)

    job_service.update_job_step(
        job["job_id"],
        "install_extension",
        "running",
        "Installing extension.",
        db=db_session,
    )
    running = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)

    job_service.update_job_step(
        job["job_id"],
        "install_extension",
        "completed",
        "Installed.",
        db=db_session,
    )
    completed = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)

    assert running["current_step"] == "install_extension"
    assert completed["current_step"] is None
    assert completed["steps"][1]["status"] == "completed"


def test_fail_job_marks_current_step_failed_and_skips_remaining(
    db_session: Session,
) -> None:
    job = job_service.reserve_job(_request(), db=db_session)
    job_service.update_job_step(
        job["job_id"],
        "run_monitoring",
        "running",
        "Running monitor.",
        db=db_session,
    )

    job_service.fail_job(job["job_id"], "monitor crashed", db=db_session)
    failed = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)

    assert failed["status"] == "failed"
    assert failed["error_detail"] == "monitor crashed"
    assert failed["current_step"] == "run_monitoring"
    assert failed["steps"][3]["status"] == "failed"
    assert failed["steps"][4]["status"] == "skipped"


def test_complete_job_persists_final_outputs(db_session: Session) -> None:
    job = job_service.reserve_job(_request(), db=db_session)
    result = AnalyzeResponse(
        status="success",
        publisher="ms-python",
        name="python",
        version="2025.0.0",
        message="done",
        install_output="install-ok",
        automation_output="automation-ok",
        report_path="activation_report.json",
    )

    job_service.complete_job(job["job_id"], result, db=db_session)
    completed = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)

    assert completed["status"] == "completed"
    assert completed["message"] == "done"
    assert completed["report_path"] == "activation_report.json"
    assert completed["install_output"] == "install-ok"
    assert completed["automation_output"] == "automation-ok"
    assert completed["finished_at"] is not None


def test_recover_interrupted_jobs_marks_stale_active_rows_failed(
    db_session: Session,
) -> None:
    snapshot = job_service.create_job_snapshot(
        _request(),
        owner_boot_id="stale-process",
        owner_pid=4321,
    )
    snapshot["status"] = "running"
    snapshot["current_step"] = "run_monitoring"
    snapshot["steps"][3]["status"] = "running"
    snapshot["steps"][3]["message"] = "Monitoring"
    job_service.store_job(snapshot, db=db_session)

    assert job_service.recover_interrupted_jobs(db=db_session) == 1

    recovered = job_service.get_persisted_job_snapshot(
        snapshot["job_id"], db=db_session
    )
    assert recovered["status"] == "failed"
    assert "interrupted by an api restart" in recovered["error_detail"].lower()
    assert recovered["steps"][3]["status"] == "failed"
