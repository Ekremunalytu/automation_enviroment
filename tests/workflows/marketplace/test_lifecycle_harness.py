"""W17-2: lifecycle harness scaffold for analysis-worker + monitoring-heartbeat
thread concurrency tests.

The harness exists to make W17-3 (heartbeat-sandbox-reset-off-thread) safe.
W16-5 deferred that work because moving the sandbox-reset call from the
analysis worker thread (``workflows.marketplace.analysis_execution.reset_sandbox``)
to the monitoring heartbeat thread (already issues
``executor_control.reset_sandbox(reload_window=True)`` on cancel at
``analysis_execution.py:292``) is concurrency-sensitive: lock ordering,
reset idempotency, and partial-state recovery cannot be verified without a
test rig that spawns both threads against a real DB row.

This file scaffolds the rig: a ``LifecycleHarness`` helper that composes
the session-scoped ``test_engine`` (so we get a real Postgres) with a
mock ``ExecutorControl`` that records every ``reset_sandbox`` call along
with the calling thread's name. The smoke test below claims a queued
``AnalysisJob`` row, spawns ``_run_monitoring_heartbeat`` with a
controllable ``cancel_check``, flips the cancel flag, and asserts:

* ``reset_sandbox`` was called exactly once.
* The call originated from the heartbeat thread (not the test's main
  thread) — pinning the W16-5 invariant that the heartbeat owns the
  cancel-time sandbox reset today.
* The job row transitioned ``queued → running`` under the worker-entry
  CAS (``WorkerEntryOutcome.CLAIMED``).

W17-3 was scope-reduced (`c4c0646`, doc-only) on `2026-05-18`; the
extension work carried forward to W18-3 per ADR 0012
(``documents/adrs/0012-heartbeat-thread-relocation.md``, Option A1
"dedicated sandbox-reset coordinator thread for step-1 reset").
**W18-3 will extend this harness** with the three concurrency tests
enumerated below; ADR 0012 §"Follow-On (W18-3 test surface)" pins
the exact test names and assertion shapes so W18-2 implementation
respects the surface this docstring describes:

* Parallel reset (``test_lifecycle_harness_parallel_reset_does_not_deadlock``):
  both the W18-2 sandbox-reset coordinator thread + the existing
  heartbeat thread issue ``reset_sandbox`` concurrently — verify
  lock ordering does not deadlock, total reset count = 2 (not
  collapsed), thread identities match production names.
* Reset idempotency (``test_lifecycle_harness_reset_idempotency``):
  two back-to-back resets from different threads do not corrupt the
  executor surface (HMAC secret file state, sandbox PID set,
  ``executor:executor`` ownership unchanged on re-create).
* Reset-during-finalize (``test_lifecycle_harness_reset_during_finalize``):
  heartbeat fires cancel while worker is in ``finalize_report``;
  the DB row must end in ``cancelled`` (not ``completed``) and the
  executor reset must not run twice after the finalize-start barrier.

Scope cuts (intentional W17-2 minimal scope):

* The harness does NOT drive ``run_analysis_job`` end-to-end. That would
  require mocking the full ``execute_analysis_request`` step pipeline
  (install_extension, build_triggers, run_monitoring, finalize_report).
  The cancel-via-heartbeat path is the narrow concurrency surface
  W17-3 needs to verify.
* The harness does NOT use ``fresh_alembic_engine`` (W16-6 fixture).
  Per-test isolation comes from UUID-keyed ``AnalysisJob`` rows + an
  explicit cleanup delete on fixture teardown, which is sufficient
  for concurrency assertions and lighter than a fresh-DB-per-test
  bootstrap.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import sessionmaker

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobCreateSnapshot,
    AnalysisJobStepRecord,
)
from appcore.storage.crud_ops.analysis_jobs import lifecycle as job_lifecycle
from appcore.storage.crud_ops.analysis_jobs.lifecycle import (
    WorkerEntryClaim,
    WorkerEntryOutcome,
)
from appcore.storage.models import AnalysisJob
from workflows.marketplace.analysis_execution import _run_monitoring_heartbeat

pytestmark = pytest.mark.requires_db


_CANONICAL_STEPS = (
    "reset_sandbox",
    "install_extension",
    "build_triggers",
    "run_monitoring",
    "finalize_report",
)


def _build_queued_snapshot(job_id: str) -> AnalysisJobCreateSnapshot:
    """Build the minimum ``AnalysisJobCreateSnapshot`` the rig persists."""
    now = time.time()
    return AnalysisJobCreateSnapshot(
        job_id=job_id,
        owner_boot_id="harness-boot",
        owner_pid=1234,
        status="queued",
        publisher="ms-python",
        name="python",
        version="2025.0.0",
        scenario=None,
        analysis_profile=None,
        current_step=None,
        message="Queued for sandbox analysis.",
        steps=[
            AnalysisJobStepRecord(name=step, status="pending", message="Queued.")
            for step in _CANONICAL_STEPS
        ],
        report_path=f"activation_report_{job_id[:8]}.json",
        install_output=None,
        automation_output=None,
        error_detail=None,
        error_code=None,
        created_at=now,
        started_at=None,
        finished_at=None,
        updated_at=now,
    )


class LifecycleHarness:
    """Rig that drives the analysis worker + monitoring heartbeat threads
    against a real DB row and a mocked ``ExecutorControl``.

    The harness mirrors the production wiring inside
    ``workflows.marketplace.analysis_execution.run_monitoring``: it builds
    its own ``_heartbeat_on_cancel`` closure that fires
    ``executor_control.reset_sandbox(reload_window=True)`` so the
    sandbox-reset call observed by the test is byte-identical with the
    cancel-path reset the production heartbeat issues.
    """

    HEARTBEAT_THREAD_NAME = "harness-monitoring-heartbeat"

    def __init__(self, *, engine: Any) -> None:
        self._engine = engine
        self._session_factory = sessionmaker(
            bind=engine, future=True, autoflush=False, expire_on_commit=False
        )
        self.executor_control = MagicMock()
        self._reset_calls: list[dict[str, Any]] = []

        def _record_reset(*args: Any, **kwargs: Any) -> None:
            self._reset_calls.append(
                {
                    "thread": threading.current_thread().name,
                    "args": args,
                    "kwargs": dict(kwargs),
                }
            )

        self.executor_control.reset_sandbox.side_effect = _record_reset
        self.job_id = uuid.uuid4().hex
        self._cancel_flag = threading.Event()
        self._stop_event = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._job_persisted = False

    def persist_queued_job(self) -> None:
        """Insert a queued ``AnalysisJob`` row owned by this harness."""
        snapshot = _build_queued_snapshot(self.job_id)
        with self._session_factory() as db:
            job_lifecycle.create_analysis_job(db, snapshot)
        self._job_persisted = True

    def claim_worker_entry(self) -> WorkerEntryClaim:
        """Run the W13-13/W16-2 worker-entry CAS; expect ``CLAIMED``."""
        with self._session_factory() as db:
            claim = job_lifecycle.claim_queued_analysis_job_at_worker_entry(
                db,
                self.job_id,
                fallback_report_name=f"activation_report_{self.job_id[:8]}.json",
            )
        return claim

    def signal_cancel(self) -> None:
        """Flip the cancel flag so the next heartbeat poll triggers ``on_cancel``."""
        self._cancel_flag.set()

    def start_heartbeat(self, *, interval_s: float = 0.05) -> None:
        """Spawn ``_run_monitoring_heartbeat`` with controllable cancel hooks.

        Mirrors ``run_monitoring`` thread construction (daemon=True, same
        target function, same kwarg shape) so harness traffic is
        observationally indistinguishable from the production thread.
        """
        reporter = MagicMock()
        reporter.emit = MagicMock()

        def _on_cancel() -> None:
            # Mirrors ``_heartbeat_on_cancel`` in
            # ``analysis_execution.run_monitoring`` — the reset_sandbox call
            # is what W17-3 will relocate; the harness must record it here
            # with its calling-thread identity.
            self.executor_control.reset_sandbox(reload_window=True)

        self._heartbeat_thread = threading.Thread(
            target=_run_monitoring_heartbeat,
            args=(self._stop_event, reporter),
            kwargs={
                "report_path": f"/results/{self.job_id[:8]}.json",
                "total_initial": 0,
                "load_report_payload": lambda _path: {},
                "cancel_check": self._cancel_flag.is_set,
                "on_cancel": _on_cancel,
                "interval_s": interval_s,
            },
            daemon=True,
            name=self.HEARTBEAT_THREAD_NAME,
        )
        self._heartbeat_thread.start()

    def stop_heartbeat(self, *, timeout: float = 2.0) -> None:
        """Signal the heartbeat to exit and join the thread."""
        self._stop_event.set()
        thread = self._heartbeat_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)
        self._heartbeat_thread = None

    def wait_for_reset_calls(self, *, count: int = 1, timeout: float = 3.0) -> None:
        """Block until at least ``count`` reset_sandbox calls have been observed."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if len(self._reset_calls) >= count:
                return
            time.sleep(0.01)
        raise AssertionError(
            f"Expected at least {count} executor_control.reset_sandbox call(s) "
            f"within {timeout}s; observed {len(self._reset_calls)}: "
            f"{self._reset_calls!r}"
        )

    @property
    def reset_calls(self) -> list[dict[str, Any]]:
        """Snapshot of every ``reset_sandbox`` call with the calling thread."""
        return list(self._reset_calls)

    def read_job_status(self) -> str:
        """Re-read the job row's current ``status`` column."""
        with self._session_factory() as db:
            job = db.get(AnalysisJob, self.job_id)
            assert job is not None, (
                f"AnalysisJob row missing for harness job_id={self.job_id!r}; "
                "did persist_queued_job() run?"
            )
            return job.status

    def cleanup(self) -> None:
        """Stop the heartbeat (if running) and delete the harness row."""
        self.stop_heartbeat()
        if not self._job_persisted:
            return
        with self._session_factory() as db:
            job = db.get(AnalysisJob, self.job_id)
            if job is not None:
                db.delete(job)
                db.commit()


@pytest.fixture
def lifecycle_harness(test_engine: Any) -> Generator[LifecycleHarness, None, None]:
    """Yields a per-test ``LifecycleHarness`` bound to the session ``test_engine``."""
    harness = LifecycleHarness(engine=test_engine)
    try:
        yield harness
    finally:
        harness.cleanup()


def test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset(
    lifecycle_harness: LifecycleHarness,
) -> None:
    """W17-2 plumbing smoke: claim queued row, spawn heartbeat, signal cancel.

    Asserts the cancel-driven ``reset_sandbox`` is fired from the heartbeat
    thread with the production kwargs (``reload_window=True``), and that
    the worker-entry CAS transitioned the row from ``queued`` to
    ``running`` (``WorkerEntryOutcome.CLAIMED``). This is the minimum
    plumbing needed for W17-3 to extend with concurrency-specific
    assertions (parallel reset, idempotency, partial-state recovery).
    """
    lifecycle_harness.persist_queued_job()

    claim = lifecycle_harness.claim_worker_entry()
    assert claim.outcome is WorkerEntryOutcome.CLAIMED
    assert lifecycle_harness.read_job_status() == "running"

    lifecycle_harness.start_heartbeat(interval_s=0.05)
    lifecycle_harness.signal_cancel()
    lifecycle_harness.wait_for_reset_calls(count=1, timeout=3.0)
    lifecycle_harness.stop_heartbeat()

    calls = lifecycle_harness.reset_calls
    assert len(calls) == 1, (
        f"Expected exactly one cancel-driven sandbox reset; got {len(calls)}: {calls!r}"
    )
    assert calls[0]["thread"] == LifecycleHarness.HEARTBEAT_THREAD_NAME, (
        "Cancel-driven reset_sandbox must fire from the monitoring heartbeat "
        "thread today; W17-3 will extend the harness to assert thread "
        "identity at other lifecycle points too. Got thread="
        f"{calls[0]['thread']!r}."
    )
    assert calls[0]["kwargs"] == {"reload_window": True}, (
        "Heartbeat cancel path must call reset_sandbox(reload_window=True) — "
        "matches production wiring in analysis_execution.py "
        "(_heartbeat_on_cancel closure). Got kwargs="
        f"{calls[0]['kwargs']!r}."
    )
