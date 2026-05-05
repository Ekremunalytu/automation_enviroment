"""W11-8: focused unit tests for ``analysis_jobs.steps``.

Pin the JSON serialization helpers (`_job_steps`, `_write_steps`) and the
single public step-update entry point at their real module path. Anchors
the W11-8 cycle-break invariant: ``steps`` must not import from
``lifecycle`` — a regression that re-introduces the original
``_get_analysis_job_or_raise`` cross-import will crash at import time and
fail the whole test module.
"""

from __future__ import annotations

import time
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobCreateSnapshot,
    AnalysisJobStepProgress,
    AnalysisJobStepRecord,
    AnalysisJobStepUpdate,
)
from appcore.storage.crud_ops.analysis_jobs import lifecycle, steps
from appcore.storage.models import AnalysisJob

pytestmark = pytest.mark.requires_db


_CANONICAL_STEPS = (
    "reset_sandbox",
    "install_extension",
    "build_triggers",
    "run_monitoring",
    "finalize_report",
)


def _empty_steps() -> list[AnalysisJobStepRecord]:
    return [
        AnalysisJobStepRecord(name=name, status="pending", message="Queued.")
        for name in _CANONICAL_STEPS
    ]


def _seed_job(db: Session) -> AnalysisJob:
    now = time.time()
    snapshot = AnalysisJobCreateSnapshot(
        job_id=uuid4().hex,
        owner_boot_id="boot-test",
        owner_pid=4321,
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
    return lifecycle.create_analysis_job(db, snapshot)


def test_update_step_running_sets_current_step(db_session: Session) -> None:
    job = _seed_job(db_session)

    updated = steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="install_extension",
            status="running",
            message="Installing.",
        ),
    )

    assert updated.current_step == "install_extension"
    assert updated.steps[1]["status"] == "running"
    assert updated.steps[1]["message"] == "Installing."


def test_update_step_completed_clears_current_step_when_matching(
    db_session: Session,
) -> None:
    job = _seed_job(db_session)
    steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="install_extension",
            status="running",
            message="Installing.",
        ),
    )

    completed = steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="install_extension",
            status="completed",
            message="Installed.",
        ),
    )

    assert completed.current_step is None
    assert completed.steps[1]["status"] == "completed"
    # Terminal steps drop progress regardless of the inbound payload.
    assert completed.steps[1]["progress"] is None


def test_update_step_skipped_clears_progress_and_current_step(
    db_session: Session,
) -> None:
    job = _seed_job(db_session)
    steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="run_monitoring",
            status="running",
            message="Running 2/5",
            progress=AnalysisJobStepProgress(completed=2, total=5),
        ),
    )

    skipped = steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="run_monitoring",
            status="skipped",
            message="Skipped because automation was interrupted.",
        ),
    )

    assert skipped.steps[3]["status"] == "skipped"
    assert skipped.steps[3]["progress"] is None
    assert skipped.current_step is None


def test_update_step_failed_keeps_current_step_for_postmortem(
    db_session: Session,
) -> None:
    job = _seed_job(db_session)
    steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="run_monitoring",
            status="running",
            message="Running monitor.",
        ),
    )

    failed = steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="run_monitoring",
            status="failed",
            message="monitor crashed",
            error_code="monitor_crashed",
        ),
    )

    # `current_step` stays on the failed step name so postmortem reads land
    # on the right entry.
    assert failed.current_step == "run_monitoring"
    assert failed.steps[3]["status"] == "failed"
    assert failed.steps[3]["error_code"] == "monitor_crashed"


def test_update_step_progress_persists_for_running_status(
    db_session: Session,
) -> None:
    job = _seed_job(db_session)

    running = steps.update_analysis_job_step(
        db_session,
        job.job_id,
        AnalysisJobStepUpdate(
            step_name="run_monitoring",
            status="running",
            message="Running 2/5",
            progress=AnalysisJobStepProgress(completed=2, total=5),
        ),
    )

    assert running.steps[3]["progress"] == {"completed": 2, "total": 5}


def test_update_step_unknown_job_raises_keyerror(db_session: Session) -> None:
    """W11-8 cycle-break pin: the inline lookup in ``update_analysis_job_step``
    must keep the legacy ``KeyError(job_id)`` contract even though
    ``_get_analysis_job_or_raise`` no longer lives in this module."""
    with pytest.raises(KeyError):
        steps.update_analysis_job_step(
            db_session,
            "does-not-exist",
            AnalysisJobStepUpdate(
                step_name="install_extension",
                status="running",
                message="Installing.",
            ),
        )


def test_update_step_unknown_step_name_raises_value_error(
    db_session: Session,
) -> None:
    """`AnalysisJobStepUpdate.step_name` is `Literal[...]`-constrained so
    callers can't pass an unknown name in production. To exercise the
    fallback ``raise ValueError(...)`` branch, simulate the case by
    deleting one of the canonical steps from a persisted job."""
    job = _seed_job(db_session)
    pruned = list(job.steps)
    pruned = [step for step in pruned if step["name"] != "build_triggers"]
    job.steps = pruned
    db_session.commit()
    db_session.refresh(job)

    with pytest.raises(ValueError, match="canonical step build_triggers"):
        steps.update_analysis_job_step(
            db_session,
            job.job_id,
            AnalysisJobStepUpdate(
                step_name="build_triggers",
                status="running",
                message="Building triggers.",
            ),
        )


def test_module_path_pins_steps_surface() -> None:
    """Pin the steps module's public surface against silent W12 reshuffle."""
    assert hasattr(steps, "update_analysis_job_step")
    assert callable(steps.update_analysis_job_step)
    assert set(steps.__all__) == {"update_analysis_job_step"}
    # Cycle-break invariant: ``steps`` must not import from ``lifecycle``.
    # Reflective check — if a future PR adds ``from .lifecycle import …`` to
    # ``steps.py`` we would have a circular import; this attribute scan
    # surfaces the regression at module load time (since the import would
    # already have happened above) and additionally documents the intent.
    assert "lifecycle" not in steps.__dict__, (
        "appcore.storage.crud_ops.analysis_jobs.steps must not import "
        "from .lifecycle (W11-8 cycle-break invariant)."
    )
