"""ES-3b (ADR 0016 §Decision 1): the ``rejected_static`` terminal transition.

Behavioral coverage for ``reject_analysis_job_static`` — the CRUD primitive
that drives a job to terminal ``rejected_static`` when the static pre-check gate
BLOCKs. Mirrors the cancel-finalize regression suite in
``test_analysis_jobs_lifecycle.py``: a row-locked terminal write, step records
finalized (gate completed, dynamic stages skipped), the single-active slot
released, and a terminal-state guard that rejects a late writer.
"""

from __future__ import annotations

import time
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from appcore.contracts.schema_defs.analysis_jobs import (
    ANALYSIS_JOB_STEP_NAMES,
    AnalysisJobCreateSnapshot,
    AnalysisJobFailure,
    AnalysisJobStepRecord,
    AnalysisJobUpdate,
)
from appcore.storage.crud_ops.analysis_jobs import lifecycle, static_gate
from appcore.storage.models import AnalysisJob

pytestmark = pytest.mark.requires_db


def _empty_steps() -> list[AnalysisJobStepRecord]:
    return [
        AnalysisJobStepRecord(name=name, status="pending", message="Queued.")
        for name in ANALYSIS_JOB_STEP_NAMES
    ]


def _snapshot(*, job_id: str | None = None) -> AnalysisJobCreateSnapshot:
    now = time.time()
    return AnalysisJobCreateSnapshot(
        job_id=job_id or uuid4().hex,
        owner_boot_id="boot-test",
        owner_pid=1234,
        status="queued",
        publisher="ms-python",
        name="python",
        version="2025.0.0",
        scenario=None,
        analysis_profile=None,
        current_step=None,
        message="Queued for sandbox analysis.",
        steps=_empty_steps(),
        report_path="activation_report.json",
        install_output=None,
        automation_output=None,
        error_detail=None,
        error_code=None,
        created_at=now,
        started_at=None,
        finished_at=None,
        updated_at=now,
    )


def _persist_at_gate(db: Session) -> AnalysisJob:
    """Persist a running job whose ``decision_gate`` step is in-flight."""
    job = lifecycle.create_analysis_job(db, _snapshot())
    steps = list(job.steps)
    for index, step in enumerate(steps):
        if step["name"] == "decision_gate":
            step["status"] = "running"
            steps[index] = step
            break
    job.steps = steps
    flag_modified(job, "steps")
    job.status = "running"
    job.current_step = "decision_gate"
    db.commit()
    db.refresh(job)
    return job


def test_reject_static_drives_terminal_rejected_static(db_session: Session) -> None:
    job = _persist_at_gate(db_session)

    rejected = static_gate.reject_analysis_job_static(
        db_session,
        job.job_id,
        "Static pre-check blocked the extension (extrace.s2.typosquat).",
        static_report_path="static_report_job.json",
    )

    assert rejected.status == "rejected_static"
    assert rejected.error_code == "static_gate_blocked"
    assert "blocked" in rejected.error_detail.lower()
    assert rejected.static_report_path == "static_report_job.json"
    assert rejected.finished_at is not None
    assert rejected.current_step is None

    steps = rejected.steps
    # The gate ran to a verdict -> completed (not failed); the rejection is
    # carried by the terminal job status.
    assert steps[0]["name"] == "static_analysis"
    assert steps[1]["name"] == "decision_gate"
    assert steps[1]["status"] == "completed"
    # Every dynamic sandbox stage (reset_sandbox..finalize_report) is skipped.
    for step in steps[2:]:
        assert step["status"] == "skipped"
        assert "blocked" in step["message"].lower()


def test_reject_static_releases_single_active_slot(db_session: Session) -> None:
    job = _persist_at_gate(db_session)
    static_gate.reject_analysis_job_static(db_session, job.job_id, "blocked")

    # rejected_static is terminal, never active -> the single-active slot
    # releases so reserve_job can admit the next job.
    assert lifecycle.get_active_analysis_job(db_session) is None


def test_reject_static_raises_keyerror_for_unknown_id(db_session: Session) -> None:
    with pytest.raises(KeyError):
        static_gate.reject_analysis_job_static(db_session, "does-not-exist", "blocked")


@pytest.mark.parametrize("terminal_driver", ["complete", "fail", "reject_static"])
def test_reject_static_raises_for_terminal_status(
    db_session: Session, terminal_driver: str
) -> None:
    """A row already terminal must not be regressed by a late static reject."""
    job = _persist_at_gate(db_session)
    if terminal_driver == "complete":
        lifecycle.complete_analysis_job(
            db_session, job.job_id, AnalysisJobUpdate(message="done")
        )
    elif terminal_driver == "fail":
        lifecycle.fail_analysis_job(
            db_session, job.job_id, AnalysisJobFailure(detail="boom")
        )
    elif terminal_driver == "reject_static":
        static_gate.reject_analysis_job_static(db_session, job.job_id, "blocked")

    with pytest.raises(lifecycle.JobNotCancellableError) as exc_info:
        static_gate.reject_analysis_job_static(db_session, job.job_id, "again")

    assert exc_info.value.status in {"completed", "failed", "rejected_static"}
