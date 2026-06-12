"""W11-8: focused unit tests for ``analysis_jobs.lifecycle``.

Imports the module at its real subpackage path so a future refactor that
moves ``cancel_analysis_job`` etc. off ``lifecycle`` breaks here. The
existing ``tests/platform/storage/test_analysis_jobs.py`` exercises the
same code paths through ``workflows.marketplace.job_service`` (one layer
up) — these cases pin the CRUD surface directly so the workflow layer
cannot mask a regression.
"""

from __future__ import annotations

import time
from typing import Any
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
from appcore.storage.crud_ops.analysis_jobs import lifecycle
from appcore.storage.models import AnalysisJob

pytestmark = pytest.mark.requires_db


# ES-3b: track the canonical 7-step order from the contract so the snapshot
# fixtures stay valid against `_validate_steps` as the order evolves.
_CANONICAL_STEPS = ANALYSIS_JOB_STEP_NAMES


def _empty_steps() -> list[AnalysisJobStepRecord]:
    return [
        AnalysisJobStepRecord(name=name, status="pending", message="Queued.")
        for name in _CANONICAL_STEPS
    ]


def _snapshot(
    *,
    status: str = "queued",
    current_step: str | None = None,
    boot_id: str = "boot-test",
    name: str = "python",
    job_id: str | None = None,
    created_at: float | None = None,
) -> AnalysisJobCreateSnapshot:
    now = created_at if created_at is not None else time.time()
    return AnalysisJobCreateSnapshot(
        job_id=job_id or uuid4().hex,
        owner_boot_id=boot_id,
        owner_pid=1234,
        status=status,  # type: ignore[arg-type]
        publisher="ms-python",
        name=name,
        version="2025.0.0",
        scenario=None,
        analysis_profile=None,
        current_step=current_step,  # type: ignore[arg-type]
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


def _persist_active(
    db: Session,
    *,
    current_step: str | None = None,
    boot_id: str = "boot-test",
    name: str = "python",
) -> AnalysisJob:
    snapshot = _snapshot(
        status="running" if current_step else "queued",
        current_step=current_step,
        boot_id=boot_id,
        name=name,
    )
    job = lifecycle.create_analysis_job(db, snapshot)
    return job


def _force_step_status(
    db: Session, job: AnalysisJob, step_name: str, status: str
) -> None:
    """Mutate a single step's status on a persisted job (test fixture helper).

    JSONB mutation needs `flag_modified` — without it SQLAlchemy may skip
    the column on commit because the bound dict is the same object. The
    pre-W13-3 cancel path masked this because `_interrupt_job` rewrote
    the column on cancel anyway; W13-3 keeps step records untouched, so
    the mutation has to be persisted faithfully now.
    """
    steps: list[dict[str, Any]] = list(job.steps)
    for index, step in enumerate(steps):
        if step["name"] == step_name:
            step["status"] = status
            step["message"] = f"forced to {status} by fixture"
            steps[index] = step
            break
    job.steps = steps
    flag_modified(job, "steps")
    job.current_step = step_name
    job.status = "running"
    db.commit()
    db.refresh(job)


def test_create_analysis_job_persists_snapshot(db_session: Session) -> None:
    snapshot = _snapshot()
    persisted = lifecycle.create_analysis_job(db_session, snapshot)

    assert persisted.job_id == snapshot.job_id
    assert persisted.status == "queued"
    assert persisted.publisher == "ms-python"
    # ES-3b: the static pre-check now leads the canonical 7-step order.
    assert persisted.steps[0]["name"] == "static_analysis"
    assert persisted.steps[2]["name"] == "reset_sandbox"
    assert persisted.created_at == pytest.approx(snapshot.created_at)


def test_get_analysis_job_returns_none_for_unknown(db_session: Session) -> None:
    assert lifecycle.get_analysis_job(db_session, "does-not-exist") is None


def test_get_analysis_job_round_trips_persisted_row(db_session: Session) -> None:
    snapshot = _snapshot()
    lifecycle.create_analysis_job(db_session, snapshot)

    fetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert fetched is not None
    assert fetched.job_id == snapshot.job_id


def test_get_active_analysis_job_returns_only_active_row(db_session: Session) -> None:
    # The ``uq_analysis_jobs_single_active`` partial unique index allows at most
    # one queued/running row at a time; this pins the read path against that
    # invariant rather than fighting it.
    snapshot = _snapshot()
    lifecycle.create_analysis_job(db_session, snapshot)

    fetched = lifecycle.get_active_analysis_job(db_session)
    assert fetched is not None
    assert fetched.job_id == snapshot.job_id


def test_get_active_analysis_job_returns_none_when_all_terminal(
    db_session: Session,
) -> None:
    snapshot = _snapshot()
    lifecycle.create_analysis_job(db_session, snapshot)
    lifecycle.complete_analysis_job(
        db_session, snapshot.job_id, AnalysisJobUpdate(message="done")
    )

    assert lifecycle.get_active_analysis_job(db_session) is None


def test_update_analysis_job_applies_partial_fields(db_session: Session) -> None:
    snapshot = _snapshot()
    lifecycle.create_analysis_job(db_session, snapshot)
    before = time.time()

    updated = lifecycle.update_analysis_job(
        db_session,
        snapshot.job_id,
        AnalysisJobUpdate(status="running", message="install starting"),
    )

    assert updated.status == "running"
    assert updated.message == "install starting"
    # Untouched field stays put — `model_dump(exclude_unset=True)` semantics.
    assert updated.publisher == "ms-python"
    assert updated.updated_at >= before


def test_update_analysis_job_raises_for_unknown_id(db_session: Session) -> None:
    with pytest.raises(KeyError):
        lifecycle.update_analysis_job(
            db_session,
            "does-not-exist",
            AnalysisJobUpdate(message="ignored"),
        )


def test_complete_analysis_job_sets_status_completed(db_session: Session) -> None:
    snapshot = _snapshot()
    lifecycle.create_analysis_job(db_session, snapshot)

    completed = lifecycle.complete_analysis_job(
        db_session,
        snapshot.job_id,
        AnalysisJobUpdate(message="done", report_path="final.json"),
    )

    assert completed.status == "completed"
    assert completed.message == "done"
    assert completed.report_path == "final.json"


def test_cancel_then_finalize_marks_current_step_cancelled_and_skips_pending(
    db_session: Session,
) -> None:
    # W13-3: cancel signals drain (`cancelling`), finalize promotes to
    # terminal `cancelled` with step records finalized. The earlier
    # single-phase cancel collapses into this two-phase sequence.
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")

    draining = lifecycle.cancel_analysis_job(db_session, job.job_id)
    assert draining.status == "cancelling"
    # While draining the step records are untouched — worker still owns them.
    assert draining.steps[5]["status"] == "running"
    assert draining.finished_at is None

    finalized = lifecycle.finalize_cancelled_analysis_job(db_session, job.job_id)

    assert finalized.status == "cancelled"
    assert finalized.error_code == "cancelled_by_user"
    assert finalized.error_detail == "Cancelled by user."
    assert finalized.current_step == "run_monitoring"
    # ES-3b: `run_monitoring` is index 5; the trailing `finalize_report` step
    # (index 6) was pending and must be marked skipped.
    steps_dump = finalized.steps
    assert steps_dump[5]["status"] == "cancelled"
    assert steps_dump[5]["progress"] is None
    assert steps_dump[6]["status"] == "skipped"
    assert "cancelled" in steps_dump[6]["message"].lower()
    assert finalized.finished_at is not None


@pytest.mark.parametrize(
    "terminal_driver",
    [
        "complete",
        "fail",
        "cancel_then_finalize",
    ],
)
def test_cancel_analysis_job_raises_for_terminal_status(
    db_session: Session, terminal_driver: str
) -> None:
    snapshot = _snapshot()
    lifecycle.create_analysis_job(db_session, snapshot)

    if terminal_driver == "complete":
        lifecycle.complete_analysis_job(
            db_session, snapshot.job_id, AnalysisJobUpdate(message="done")
        )
    elif terminal_driver == "fail":
        lifecycle.fail_analysis_job(
            db_session,
            snapshot.job_id,
            AnalysisJobFailure(detail="boom"),
        )
    elif terminal_driver == "cancel_then_finalize":
        # W13-3 two-phase cancel: first call signals drain; second call
        # would be idempotent — drive the row terminal via finalize so
        # the third cancel can be tested against the terminal raise.
        lifecycle.cancel_analysis_job(db_session, snapshot.job_id)
        lifecycle.finalize_cancelled_analysis_job(db_session, snapshot.job_id)

    with pytest.raises(lifecycle.JobNotCancellableError) as exc_info:
        lifecycle.cancel_analysis_job(db_session, snapshot.job_id)

    assert exc_info.value.job_id == snapshot.job_id
    assert exc_info.value.status in {"completed", "failed", "cancelled"}


def test_cancel_analysis_job_raises_keyerror_for_unknown_id(
    db_session: Session,
) -> None:
    with pytest.raises(KeyError):
        lifecycle.cancel_analysis_job(db_session, "does-not-exist")


def test_fail_analysis_job_marks_current_step_failed_and_skips_pending(
    db_session: Session,
) -> None:
    job = _persist_active(db_session, current_step="install_extension")
    _force_step_status(db_session, job, "install_extension", "running")

    failed = lifecycle.fail_analysis_job(
        db_session,
        job.job_id,
        AnalysisJobFailure(detail="installer crashed", error_code="install_failed"),
    )

    assert failed.status == "failed"
    assert failed.error_detail == "installer crashed"
    assert failed.error_code == "install_failed"
    assert failed.current_step == "install_extension"
    steps_dump = failed.steps
    # ES-3b: install_extension is now index 3 (static_analysis/decision_gate
    # lead). The trailing dynamic steps (4..6) go to skipped.
    assert steps_dump[3]["status"] == "failed"
    for trailing in steps_dump[4:]:
        assert trailing["status"] == "skipped"


def test_recover_interrupted_analysis_jobs_marks_stale_active_jobs_failed(
    db_session: Session,
) -> None:
    job = _persist_active(
        db_session, current_step="run_monitoring", boot_id="stale-boot"
    )
    _force_step_status(db_session, job, "run_monitoring", "running")

    recovered = lifecycle.recover_interrupted_analysis_jobs(
        db_session,
        current_boot_id="fresh-boot",
        detail="Interrupted by an api restart.",
    )

    assert recovered == 1
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "failed"
    assert refetched.error_detail == "Interrupted by an api restart."
    assert refetched.steps[5]["status"] == "failed"


def test_recover_interrupted_analysis_jobs_returns_zero_when_owner_matches(
    db_session: Session,
) -> None:
    job = _persist_active(
        db_session, current_step="run_monitoring", boot_id="same-boot"
    )

    recovered = lifecycle.recover_interrupted_analysis_jobs(
        db_session,
        current_boot_id="same-boot",
        detail="should not run",
    )

    assert recovered == 0
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "running"  # untouched


# ---------------------------------------------------------------------------
# S2 (W23 B3) — heartbeat stamp + same-boot stale-running reaper.
#
# `recover_interrupted_analysis_jobs` (above) only reaps a *different* boot.
# A worker that hangs / crashes within the SAME boot keeps its row `running`
# and holds the single-active slot until an API restart. `touch_*_heartbeat`
# stamps liveness; `reap_stale_running_analysis_jobs` recovers a wedged row
# whose heartbeat (or started_at fallback) is older than the stale timeout,
# without a restart.
# ---------------------------------------------------------------------------


def _persist_running_with_times(
    db_session: Session,
    *,
    boot_id: str = "same-boot",
    started_at: float | None = None,
    last_heartbeat_at: float | None = None,
    status: str = "running",
) -> AnalysisJob:
    """Persist a row in ``status`` with explicit started/heartbeat timestamps."""
    job = _persist_active(db_session, current_step="run_monitoring", boot_id=boot_id)
    job.status = status
    job.started_at = started_at
    job.last_heartbeat_at = last_heartbeat_at
    db_session.commit()
    return job


def test_touch_heartbeat_stamps_running_job(db_session: Session) -> None:
    job = _persist_running_with_times(db_session)
    assert job.last_heartbeat_at is None

    rowcount = lifecycle.touch_analysis_job_heartbeat(
        db_session, job.job_id, now=1000.0
    )

    assert rowcount == 1
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.last_heartbeat_at == 1000.0


def test_touch_heartbeat_is_noop_on_non_running_job(db_session: Session) -> None:
    # A queued row has no running worker — the heartbeat must not stamp it.
    snapshot = _snapshot(status="queued")
    job = lifecycle.create_analysis_job(db_session, snapshot)

    rowcount = lifecycle.touch_analysis_job_heartbeat(
        db_session, job.job_id, now=1000.0
    )

    assert rowcount == 0
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.last_heartbeat_at is None


def test_reap_stale_running_fails_same_boot_stale_job(db_session: Session) -> None:
    # Heartbeat 1000s old at now=2000 with a 120s timeout → wedged.
    job = _persist_running_with_times(
        db_session, started_at=900.0, last_heartbeat_at=1000.0
    )
    _force_step_status(db_session, job, "run_monitoring", "running")

    reaped = lifecycle.reap_stale_running_analysis_jobs(
        db_session,
        current_boot_id="same-boot",
        stale_after_s=120.0,
        detail="stale heartbeat",
        now=2000.0,
    )

    assert reaped == 1
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "failed"
    assert refetched.error_code == lifecycle.STALE_HEARTBEAT_REAP_ERROR_CODE
    assert refetched.steps[5]["status"] == "failed"


def test_reap_stale_running_skips_fresh_heartbeat(db_session: Session) -> None:
    # Heartbeat only 10s old at now=2000 → healthy, not reaped.
    job = _persist_running_with_times(
        db_session, started_at=900.0, last_heartbeat_at=1990.0
    )

    reaped = lifecycle.reap_stale_running_analysis_jobs(
        db_session,
        current_boot_id="same-boot",
        stale_after_s=120.0,
        detail="stale heartbeat",
        now=2000.0,
    )

    assert reaped == 0
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "running"


def test_reap_stale_running_falls_back_to_started_at(db_session: Session) -> None:
    # No heartbeat ever written; started_at is old → reaped via COALESCE.
    job = _persist_running_with_times(
        db_session, started_at=1000.0, last_heartbeat_at=None
    )

    reaped = lifecycle.reap_stale_running_analysis_jobs(
        db_session,
        current_boot_id="same-boot",
        stale_after_s=120.0,
        detail="stale heartbeat",
        now=2000.0,
    )

    assert reaped == 1
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "failed"


def test_reap_stale_running_skips_other_boot(db_session: Session) -> None:
    # A different boot's row is the boot-id recovery sweep's job, not this
    # reaper's — even when stale, this reaper leaves it untouched.
    job = _persist_running_with_times(
        db_session, boot_id="other-boot", started_at=900.0, last_heartbeat_at=1000.0
    )

    reaped = lifecycle.reap_stale_running_analysis_jobs(
        db_session,
        current_boot_id="same-boot",
        stale_after_s=120.0,
        detail="stale heartbeat",
        now=2000.0,
    )

    assert reaped == 0
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "running"


def test_reap_stale_running_skips_cancelling(db_session: Session) -> None:
    # `cancelling` is owned by the two-phase cancel contract — the reaper
    # targets only `running`, so a stale cancelling row is left alone.
    job = _persist_running_with_times(
        db_session,
        status="cancelling",
        started_at=900.0,
        last_heartbeat_at=1000.0,
    )

    reaped = lifecycle.reap_stale_running_analysis_jobs(
        db_session,
        current_boot_id="same-boot",
        stale_after_s=120.0,
        detail="stale heartbeat",
        now=2000.0,
    )

    assert reaped == 0
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "cancelling"


# ---------------------------------------------------------------------------
# W13-3 (Codex H4) — two-phase cancel + finalize regression coverage.
#
# `cancel_analysis_job` signals drain (`running -> cancelling`);
# `finalize_cancelled_analysis_job` promotes the drained row to terminal
# (`cancelling -> cancelled`). The partial unique index
# `uq_analysis_jobs_single_active` widens its WHERE clause to include
# `cancelling`, so `reserve_job` blocks while a cancelled-but-still-running
# worker exists.
#
# Originally landed as W13-3.2 @pytest.mark.skip RED precursors; W13-3.4
# delivers the CRUD side (this commit) and the skip decorators come off.
#
# See documents/active-work/W13-test-expansion-observability.md →
# Per-Item Detail → W13-3 (Design Decision Locked-In: Option A).
# ---------------------------------------------------------------------------


def test_cancel_during_running_transitions_to_cancelling_not_cancelled(
    db_session: Session,
) -> None:
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")

    draining = lifecycle.cancel_analysis_job(db_session, job.job_id)

    # W13-3 contract: cancel signals drain start, not termination.
    assert draining.status == "cancelling"
    assert draining.finished_at is None
    # `requested_cancel_at` records when the drain was signalled.
    assert getattr(draining, "requested_cancel_at", None) is not None
    # Steps are not yet finalized — worker still drains.
    assert draining.steps[5]["status"] == "running"
    assert draining.error_code == "cancelled_by_user"


def test_cancel_during_cancelling_is_idempotent_no_op(
    db_session: Session,
) -> None:
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")
    first = lifecycle.cancel_analysis_job(db_session, job.job_id)
    assert first.status == "cancelling"

    # Second cancel on a draining job must not raise (UI double-click
    # tolerance) and must not regress `requested_cancel_at`.
    second = lifecycle.cancel_analysis_job(db_session, job.job_id)
    assert second.status == "cancelling"
    assert second.requested_cancel_at == first.requested_cancel_at  # type: ignore[attr-defined]
    assert second.finished_at is None


def test_finalize_cancelled_only_from_cancelling_raises_otherwise(
    db_session: Session,
) -> None:
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")
    # The drain-finalize helper transitions cancelling -> cancelled and
    # finalizes the step records; it must reject any other source state so
    # the two-phase contract cannot be short-circuited.
    finalize = lifecycle.finalize_cancelled_analysis_job  # type: ignore[attr-defined]

    with pytest.raises(lifecycle.JobNotCancellableError):
        finalize(db_session, job.job_id)  # job is still running; must reject

    lifecycle.cancel_analysis_job(db_session, job.job_id)
    finalized = finalize(db_session, job.job_id)

    assert finalized.status == "cancelled"
    assert finalized.finished_at is not None
    assert finalized.steps[5]["status"] == "cancelled"
    assert finalized.steps[6]["status"] == "skipped"


def test_complete_analysis_job_rejected_from_cancelling(
    db_session: Session,
) -> None:
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")
    lifecycle.cancel_analysis_job(db_session, job.job_id)

    # A drained worker that successfully finished its happy-path AFTER
    # being signalled to cancel must not be allowed to complete the job —
    # the cancellation was authoritative.
    with pytest.raises(lifecycle.JobNotCancellableError):
        lifecycle.complete_analysis_job(
            db_session,
            job.job_id,
            AnalysisJobUpdate(message="late completion", report_path="r.json"),
        )


def test_get_active_analysis_job_returns_cancelling_row(
    db_session: Session,
) -> None:
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")
    lifecycle.cancel_analysis_job(db_session, job.job_id)

    # While the worker drains, the row holds the single-active slot so
    # reserve_job sees an ActiveAnalysisJobError and refuses to admit a
    # second job over the shared executor.
    active = lifecycle.get_active_analysis_job(db_session)
    assert active is not None
    assert active.job_id == job.job_id
    assert active.status == "cancelling"


def test_module_path_pins_lifecycle_surface() -> None:
    """Pin the lifecycle module's public surface against silent reshuffle.

    If a future refactor moves any of these names off ``lifecycle`` (e.g.
    onto a free function file or back into the facade), this fails so the
    move is intentional. W16-2 (2026-05-18) extended the surface with the
    worker-entry CRUD primitive ``claim_queued_analysis_job_at_worker_entry``
    plus its result types ``WorkerEntryClaim`` / ``WorkerEntryOutcome``,
    moving the W13-13 row-lock-aware ``queued -> running`` cancel-aware
    transition out of ``workflows.marketplace.analysis_service`` for
    AGENTS.md:57 compliance.
    """
    expected = {
        # S2 (W23 B3, 2026-06-12) extended the surface with the same-boot
        # wedged-job recovery primitives: ``touch_analysis_job_heartbeat``
        # (liveness stamp), ``reap_stale_running_analysis_jobs`` (the reaper),
        # and the ``STALE_HEARTBEAT_REAP_ERROR_CODE`` constant they stamp.
        "STALE_HEARTBEAT_REAP_ERROR_CODE",
        "JobNotCancellableError",
        "WorkerEntryClaim",
        "WorkerEntryOutcome",
        "cancel_analysis_job",
        "claim_queued_analysis_job_at_worker_entry",
        "complete_analysis_job",
        "create_analysis_job",
        "fail_analysis_job",
        "finalize_cancelled_analysis_job",
        "get_active_analysis_job",
        "get_analysis_job",
        "reap_stale_running_analysis_jobs",
        "recover_interrupted_analysis_jobs",
        "touch_analysis_job_heartbeat",
        "update_analysis_job",
    }
    for name in expected:
        assert hasattr(lifecycle, name), (
            f"lifecycle.{name} missing — W11-8/W16-2 surface invariant broken."
        )
    assert set(lifecycle.__all__) == expected


# ---------------------------------------------------------------------------
# W13-4 (cancellation lifecycle hardening) — finalize negative cases.
#
# `finalize_cancelled_analysis_job` is the single terminal writer on the
# cancel path. W13-3 added it as a two-phase helper but didn't pin its
# negative contracts:
#
#  - Absent job_id → KeyError (matches the existing
#    `cancel_analysis_job` and `update_analysis_job` contract for
#    unknown ids).
#  - Already-terminal source state → JobNotCancellableError (matches
#    the `cancel_analysis_job` terminal-state contract; double-finalize
#    must be a contract-level raise so the worker exception handler's
#    `try/except (JobNotCancellableError, KeyError)` swallow in
#    `analysis_service.run_analysis_job:247-255` is well-defined).
#
# W13-4.2 lands these as @pytest.mark.skip RED precursors; W13-4.6
# removes the skip decorators (no production code change — the
# guards already exist in lifecycle.py:181-187).
# ---------------------------------------------------------------------------


def test_finalize_cancelled_raises_keyerror_for_unknown_id(
    db_session: Session,
) -> None:
    """``finalize_cancelled_analysis_job`` on a non-existent job_id raises
    ``KeyError`` (matches the existing absent-row contract for the rest
    of the lifecycle helpers — see ``cancel_analysis_job`` line 290).
    """
    with pytest.raises(KeyError):
        lifecycle.finalize_cancelled_analysis_job(db_session, "does-not-exist")


def test_finalize_cancelled_idempotent_on_double_finalize(
    db_session: Session,
) -> None:
    """A second ``finalize_cancelled_analysis_job`` after the row is already
    terminal raises ``JobNotCancellableError`` (not silently no-op).

    Production swallows this in
    ``workflows/marketplace/analysis_service.py:247-255`` — the
    ``try/except (JobNotCancellableError, KeyError)`` makes the
    worker-side dispatch idempotent. This test pins the *contract*
    layer: the helper itself MUST raise (so a caller without the
    swallow can detect the double-write attempt), and the row MUST
    NOT be mutated by the second call.
    """
    job = _persist_active(db_session, current_step="run_monitoring")
    _force_step_status(db_session, job, "run_monitoring", "running")
    lifecycle.cancel_analysis_job(db_session, job.job_id)
    first = lifecycle.finalize_cancelled_analysis_job(db_session, job.job_id)
    assert first.status == "cancelled"
    first_finished_at = first.finished_at

    with pytest.raises(lifecycle.JobNotCancellableError) as exc_info:
        lifecycle.finalize_cancelled_analysis_job(db_session, job.job_id)

    assert exc_info.value.status == "cancelled"  # already terminal source state

    # Row state preserved exactly; second call did not mutate.
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "cancelled"
    assert refetched.finished_at == first_finished_at
