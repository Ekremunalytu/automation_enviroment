"""S2 (W23 B3): job_service heartbeat + stale-running reaper thread machinery.

Splits into two layers:

* Thread/loop unit tests (no DB) — the heartbeat tick loop, the background
  reaper loop's sleep-first / swallow-DB-error contract, and ``start_stale_job_reaper``
  spawning a daemon that drives the injected sweep.
* A DB-backed wrapper test — ``reap_stale_running_jobs`` binds this process's
  boot id + configured timeout and reaps a stale same-boot ``running`` row
  (the CRUD layer is exhaustively covered in
  ``tests/platform/storage/test_analysis_jobs_lifecycle.py``).
"""

from __future__ import annotations

import threading
import time
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    ANALYSIS_JOB_STEP_NAMES,
    AnalysisJobCreateSnapshot,
    AnalysisJobStepRecord,
)
from appcore.storage.crud_ops.analysis_jobs import lifecycle
from workflows.marketplace import job_service


# ---------------------------------------------------------------------------
# Thread / loop unit tests — no DB
# ---------------------------------------------------------------------------


def test_stale_reaper_loop_sweeps_then_stops() -> None:
    calls = 0
    stop = threading.Event()

    def sweep() -> int:
        nonlocal calls
        calls += 1
        stop.set()  # one pass then unwind
        return 0

    job_service._stale_reaper_loop(stop, interval_s=0.01, sweep=sweep)

    assert calls == 1


def test_stale_reaper_loop_sleeps_before_first_sweep() -> None:
    # Pre-set the event: the loop must sleep-check first and never sweep, so
    # spawning the thread is side-effect-free on a fresh process.
    calls = 0
    stop = threading.Event()
    stop.set()

    def sweep() -> int:
        nonlocal calls
        calls += 1
        return 0

    job_service._stale_reaper_loop(stop, interval_s=0.01, sweep=sweep)

    assert calls == 0


def test_stale_reaper_loop_swallows_db_error() -> None:
    calls = 0
    stop = threading.Event()

    def sweep() -> int:
        nonlocal calls
        calls += 1
        stop.set()
        raise SQLAlchemyError("db down")

    # Must not propagate — a DB outage degrades to a logged skip.
    job_service._stale_reaper_loop(stop, interval_s=0.01, sweep=sweep)

    assert calls == 1


def test_start_stale_job_reaper_spawns_daemon_driving_sweep() -> None:
    swept = threading.Event()
    stop = threading.Event()

    def sweep() -> int:
        swept.set()
        return 0

    thread = job_service.start_stale_job_reaper(stop, interval_s=0.01, sweep=sweep)
    try:
        assert thread.daemon is True
        assert swept.wait(2.0), "reaper thread did not call the sweep"
    finally:
        stop.set()
        thread.join(timeout=2.0)
    assert not thread.is_alive()


def test_run_job_heartbeat_ticks_until_stopped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    stop = threading.Event()

    def fake_touch(job_id: str, db: Session | None = None) -> int:
        nonlocal calls
        calls += 1
        stop.set()  # one tick then unwind
        return 1

    monkeypatch.setattr(job_service, "touch_job_heartbeat", fake_touch)

    job_service.run_job_heartbeat("job-1", stop, interval_s=0.01)

    assert calls == 1


def test_run_job_heartbeat_survives_db_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    stop = threading.Event()

    def fake_touch(job_id: str, db: Session | None = None) -> int:
        nonlocal calls
        calls += 1
        stop.set()
        raise SQLAlchemyError("db down")

    monkeypatch.setattr(job_service, "touch_job_heartbeat", fake_touch)

    # A transient DB error must not crash the heartbeat thread.
    job_service.run_job_heartbeat("job-1", stop, interval_s=0.01)

    assert calls == 1


# ---------------------------------------------------------------------------
# DB-backed wrapper — binds _PROCESS_BOOT_ID + configured timeout
# ---------------------------------------------------------------------------


def _running_snapshot(boot_id: str) -> AnalysisJobCreateSnapshot:
    now = time.time()
    return AnalysisJobCreateSnapshot(
        job_id=uuid4().hex,
        owner_boot_id=boot_id,
        owner_pid=1234,
        status="running",  # type: ignore[arg-type]
        publisher="ms-python",
        name="python",
        version="2025.0.0",
        current_step="run_monitoring",  # type: ignore[arg-type]
        message="running",
        steps=[
            AnalysisJobStepRecord(name=name, status="pending", message="Queued.")
            for name in ANALYSIS_JOB_STEP_NAMES
        ],
        report_path="activation_report.json",
        created_at=now,
        started_at=now,
        updated_at=now,
    )


@pytest.mark.requires_db
def test_reap_stale_running_jobs_wrapper_reaps_same_boot_stale(
    db_session: Session,
) -> None:
    # Same boot as this process, heartbeat well past the configured timeout.
    job = lifecycle.create_analysis_job(
        db_session, _running_snapshot(job_service._PROCESS_BOOT_ID)
    )
    job.last_heartbeat_at = time.time() - (job_service._STALE_JOB_TIMEOUT_S + 60)
    db_session.commit()

    reaped = job_service.reap_stale_running_jobs(db=db_session)

    assert reaped == 1
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.status == "failed"
    assert refetched.error_code == lifecycle.STALE_HEARTBEAT_REAP_ERROR_CODE


@pytest.mark.requires_db
def test_touch_job_heartbeat_wrapper_stamps_running(db_session: Session) -> None:
    job = lifecycle.create_analysis_job(
        db_session, _running_snapshot(job_service._PROCESS_BOOT_ID)
    )
    job.last_heartbeat_at = None
    db_session.commit()

    rowcount = job_service.touch_job_heartbeat(job.job_id, db=db_session)

    assert rowcount == 1
    refetched = lifecycle.get_analysis_job(db_session, job.job_id)
    assert refetched is not None
    assert refetched.last_heartbeat_at is not None
