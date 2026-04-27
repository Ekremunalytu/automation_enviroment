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


def test_cancel_job_marks_current_step_cancelled_and_skips_remaining(
    db_session: Session,
) -> None:
    job = job_service.reserve_job(_request(), db=db_session)
    job_service.update_job_step(
        job["job_id"],
        "run_monitoring",
        "running",
        "Running monitor.",
        db=db_session,
        progress={"completed": 1, "total": 5},
    )

    job_service.cancel_job(job["job_id"], db=db_session)
    cancelled = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)

    assert cancelled["status"] == "cancelled"
    assert cancelled["error_code"] == "cancelled_by_user"
    assert cancelled["error_detail"] == "Cancelled by user."
    assert cancelled["current_step"] == "run_monitoring"
    assert cancelled["steps"][3]["status"] == "cancelled"
    assert cancelled["steps"][3]["progress"] is None
    assert cancelled["steps"][4]["status"] == "skipped"
    assert "cancelled" in cancelled["steps"][4]["message"].lower()
    assert cancelled["finished_at"] is not None


def _drive_to_completed(job_id: str, db: Session) -> None:
    result = AnalyzeResponse(
        status="success",
        publisher="ms-python",
        name="python",
        version="2025.0.0",
        message="done",
        install_output=None,
        automation_output=None,
        report_path="activation_report.json",
    )
    job_service.complete_job(job_id, result, db=db)


def _drive_to_failed(job_id: str, db: Session) -> None:
    job_service.fail_job(job_id, "monitor crashed", db=db)


def _drive_to_cancelled(job_id: str, db: Session) -> None:
    job_service.cancel_job(job_id, db=db)


@pytest.mark.parametrize(
    ("driver", "expected_status"),
    [
        (_drive_to_completed, "completed"),
        (_drive_to_failed, "failed"),
        (_drive_to_cancelled, "cancelled"),
    ],
)
def test_cancel_job_on_terminal_status_raises_not_cancellable(
    db_session: Session,
    driver: object,
    expected_status: str,
) -> None:
    """`cancel_job` issued after the job reached any terminal status raises
    ``JobNotCancellableError`` rather than re-marking the job. Closes the
    in-flight race gap from POST_POC_BACKLOG `[FOLLOWUP
    simulation-progress-cancel]` (cancel-after-finish race coverage)."""
    job = job_service.reserve_job(_request(), db=db_session)
    driver(job["job_id"], db_session)  # type: ignore[operator]

    snapshot_before = job_service.get_persisted_job_snapshot(
        job["job_id"], db=db_session
    )
    assert snapshot_before["status"] == expected_status

    with pytest.raises(job_service.JobNotCancellableError) as exc_info:
        job_service.cancel_job(job["job_id"], db=db_session)

    assert exc_info.value.status == expected_status

    snapshot_after = job_service.get_persisted_job_snapshot(
        job["job_id"], db=db_session
    )
    assert snapshot_after["status"] == expected_status


def test_cancel_job_unknown_id_raises(db_session: Session) -> None:
    with pytest.raises(KeyError):
        job_service.cancel_job("does-not-exist", db=db_session)


def test_update_job_step_progress_field_is_persisted_and_cleared(
    db_session: Session,
) -> None:
    job = job_service.reserve_job(_request(), db=db_session)
    job_service.update_job_step(
        job["job_id"],
        "run_monitoring",
        "running",
        "Running 2/5",
        db=db_session,
        progress={"completed": 2, "total": 5},
    )
    running = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)
    assert running["steps"][3]["progress"] == {"completed": 2, "total": 5}

    job_service.update_job_step(
        job["job_id"],
        "run_monitoring",
        "completed",
        "Done",
        db=db_session,
    )
    done = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)
    assert done["steps"][3]["progress"] is None


def test_update_job_step_clears_progress_when_status_becomes_skipped(
    db_session: Session,
) -> None:
    """A 'skipped' transition is also terminal: stale progress numerator/total
    must be cleared so the UI doesn't keep showing 2/5 on a step that never
    actually finished."""
    job = job_service.reserve_job(_request(), db=db_session)
    job_service.update_job_step(
        job["job_id"],
        "run_monitoring",
        "running",
        "Running 2/5",
        db=db_session,
        progress={"completed": 2, "total": 5},
    )
    job_service.update_job_step(
        job["job_id"],
        "run_monitoring",
        "skipped",
        "Skipped because automation was interrupted.",
        db=db_session,
    )
    snapshot = job_service.get_persisted_job_snapshot(job["job_id"], db=db_session)
    assert snapshot["steps"][3]["status"] == "skipped"
    assert snapshot["steps"][3]["progress"] is None


def test_is_job_cancelled_returns_true_only_for_cancelled_status(
    db_session: Session,
) -> None:
    """is_job_cancelled is the polling primitive used by the analysis worker to
    decide whether to keep running. It must return True only for the cancelled
    terminal state — not for queued/running/completed/failed."""
    job = job_service.reserve_job(_request(), db=db_session)
    # queued: not cancelled
    assert job_service.is_job_cancelled(job["job_id"], db=db_session) is False

    job_service.update_job(
        job["job_id"],
        status="running",
        message="running",
        db=db_session,
    )
    assert job_service.is_job_cancelled(job["job_id"], db=db_session) is False

    job_service.cancel_job(job["job_id"], db=db_session)
    assert job_service.is_job_cancelled(job["job_id"], db=db_session) is True


def test_is_job_cancelled_returns_false_for_unknown_job(
    db_session: Session,
) -> None:
    """Unknown jobs are 'not cancelled' rather than raising — the worker uses
    this to gate behavior, and a missing row should never crash the heartbeat."""
    assert job_service.is_job_cancelled("does-not-exist", db=db_session) is False


def test_is_job_cancelled_returns_false_after_completion(
    db_session: Session,
) -> None:
    job = job_service.reserve_job(_request(), db=db_session)
    result = AnalyzeResponse(
        status="success",
        publisher="ms-python",
        name="python",
        version="2025.0.0",
        message="done",
        install_output=None,
        automation_output=None,
        report_path="activation_report.json",
    )
    job_service.complete_job(job["job_id"], result, db=db_session)

    assert job_service.is_job_cancelled(job["job_id"], db=db_session) is False


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
