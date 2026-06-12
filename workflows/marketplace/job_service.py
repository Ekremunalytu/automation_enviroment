"""DB-backed orchestration helpers for marketplace analysis jobs."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from copy import deepcopy
from typing import Any, TypeVar
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobCreateSnapshot,
    AnalysisJobFailure,
    AnalysisJobPersistedRecord,
    AnalysisJobStepName,
    AnalysisJobStepProgress,
    AnalysisJobStepRecord,
    AnalysisJobStepStatus,
    AnalysisJobStepUpdate,
    AnalysisJobUpdate,
)
from appcore.contracts.schemas import (
    AnalyzeJobStatusResponse,
    AnalyzeRequest,
    AnalyzeResponse,
)
from appcore.db.session import SessionLocal
from appcore.logging import get_extrace_logger
from appcore.storage.crud import (
    JobNotCancellableError,
    cancel_analysis_job,
    complete_analysis_job,
    create_analysis_job,
    fail_analysis_job,
    finalize_cancelled_analysis_job,
    get_active_analysis_job,
    get_analysis_job,
    reap_stale_running_analysis_jobs,
    recover_interrupted_analysis_jobs,
    reject_analysis_job_static,
    touch_analysis_job_heartbeat,
    update_analysis_job,
    update_analysis_job_step,
)
from appcore.storage.models import AnalysisJob
from packages.marketplace_identity import safe_marketplace_slug

logger = get_extrace_logger("extrace.workflows.marketplace.job_service")

_PROCESS_BOOT_ID = uuid4().hex
T = TypeVar("T")


def _env_float(name: str, default: float) -> float:
    """Read a positive float tunable from the environment, falling back safely."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


# S2 (W23 B3, same-boot wedged-job recovery) tunables — env-overridable with
# sane single-operator defaults; no new pydantic settings group (operational
# knobs, mirrors the ``EXTRACE_*`` os.getenv pattern in main.py).
#
# - HEARTBEAT_INTERVAL: how often the worker stamps ``last_heartbeat_at`` while
#   a job is running. Matches the existing monitoring-heartbeat cadence.
# - STALE_JOB_TIMEOUT: a running job whose heartbeat (or started_at fallback)
#   predates ``now - timeout`` is treated as wedged. Conservative so a slow
#   phase is never false-reaped; the dedicated heartbeat thread ticks every
#   ~5s independent of phase, so 120s = ~24 missed ticks.
# - REAPER_SWEEP_INTERVAL: how often the background reaper thread sweeps.
_HEARTBEAT_INTERVAL_S = _env_float("EXTRACE_HEARTBEAT_INTERVAL_S", 5.0)
_STALE_JOB_TIMEOUT_S = _env_float("EXTRACE_STALE_JOB_TIMEOUT_S", 120.0)
_REAPER_SWEEP_INTERVAL_S = _env_float("EXTRACE_REAPER_SWEEP_INTERVAL_S", 30.0)


class ActiveAnalysisJobError(RuntimeError):
    """Raised when a new analysis job is requested while another job is active."""

    def __init__(self, active_job: dict[str, Any]) -> None:
        super().__init__("Another sandbox analysis is already in progress.")
        self.active_job = deepcopy(active_job)


def now() -> float:
    return time.time()


def empty_job_steps() -> list[AnalysisJobStepRecord]:
    # ES-3b (ADR 0016): the static pre-check leads the canonical 7-step order.
    # When the feature flag is OFF (default until ES-5) the two static steps are
    # seeded `skipped` so the UI shows the gate was not run; when ON they start
    # `pending` and the orchestrator drives them. The dynamic stages are
    # unchanged. Keep in lockstep with ANALYSIS_JOB_STEP_NAMES (_validate_steps
    # pins the exact order on persist).
    static_enabled = settings.static_analysis.ENABLED
    static_status: AnalysisJobStepStatus = "pending" if static_enabled else "skipped"
    static_message = (
        "Queued for static pre-check."
        if static_enabled
        else "Static pre-check disabled."
    )
    gate_message = (
        "Waiting for the static gate verdict."
        if static_enabled
        else "Static pre-check disabled."
    )
    return [
        AnalysisJobStepRecord(
            name="static_analysis",
            status=static_status,
            message=static_message,
        ),
        AnalysisJobStepRecord(
            name="decision_gate",
            status=static_status,
            message=gate_message,
        ),
        AnalysisJobStepRecord(
            name="reset_sandbox",
            status="pending",
            message="Waiting for sandbox cleanup.",
        ),
        AnalysisJobStepRecord(
            name="install_extension",
            status="pending",
            message="Queued.",
        ),
        AnalysisJobStepRecord(
            name="build_triggers",
            status="pending",
            message="Waiting for activation metadata.",
        ),
        AnalysisJobStepRecord(
            name="run_monitoring",
            status="pending",
            message="Waiting for sandbox automation.",
        ),
        AnalysisJobStepRecord(
            name="finalize_report",
            status="pending",
            message="Waiting for report export.",
        ),
    ]


def build_report_name(request: AnalyzeRequest, run_id: str) -> str:
    slug = safe_marketplace_slug(request.publisher, request.name, request.version)
    return f"activation_report_{slug}-{run_id[:12]}.json"


def create_job_snapshot(
    request: AnalyzeRequest,
    *,
    owner_boot_id: str | None = None,
    owner_pid: int | None = None,
) -> dict[str, Any]:
    created_at = now()
    job_id = uuid4().hex
    snapshot = AnalysisJobCreateSnapshot(
        job_id=job_id,
        owner_boot_id=owner_boot_id or _PROCESS_BOOT_ID,
        owner_pid=owner_pid or os.getpid(),
        status="queued",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        scenario=request.scenario,
        analysis_profile=request.analysis_profile,
        current_step=None,
        message="Queued for sandbox analysis.",
        steps=empty_job_steps(),
        report_path=build_report_name(request, job_id),
        install_output=None,
        automation_output=None,
        error_detail=None,
        error_code=None,
        created_at=created_at,
        started_at=None,
        finished_at=None,
        updated_at=created_at,
    )
    return snapshot.model_dump(mode="python")


def _run_in_session(
    db: Session | None,
    operation: Callable[[Session], T],
) -> T:
    if db is not None:
        return operation(db)

    session = SessionLocal()
    try:
        return operation(session)
    finally:
        session.close()


def _persisted_snapshot(job: AnalysisJob) -> dict[str, Any]:
    record = AnalysisJobPersistedRecord.model_validate(job, from_attributes=True)
    return record.model_dump(mode="python")


def _public_snapshot(job: AnalysisJob) -> dict[str, Any]:
    persisted = _persisted_snapshot(job)
    response_fields = AnalyzeJobStatusResponse.model_fields
    payload = {
        field_name: persisted[field_name]
        for field_name in response_fields
        if field_name in persisted
    }
    response = AnalyzeJobStatusResponse.model_validate(payload)
    return response.model_dump(mode="python")


def store_job(job: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    snapshot = AnalysisJobCreateSnapshot.model_validate(job)

    def operation(session: Session) -> dict[str, Any]:
        stored = create_analysis_job(session, snapshot)
        return _persisted_snapshot(stored)

    return _run_in_session(db, operation)


def reserve_job(
    request: AnalyzeRequest,
    db: Session | None = None,
) -> dict[str, Any]:
    snapshot = AnalysisJobCreateSnapshot.model_validate(create_job_snapshot(request))

    def operation(session: Session) -> dict[str, Any]:
        active_job = get_active_analysis_job(session)
        if active_job is not None:
            raise ActiveAnalysisJobError(_public_snapshot(active_job))

        try:
            stored = create_analysis_job(session, snapshot)
        except IntegrityError:
            active_job = get_active_analysis_job(session)
            if active_job is not None:
                raise ActiveAnalysisJobError(_public_snapshot(active_job)) from None
            raise
        return _public_snapshot(stored)

    return _run_in_session(db, operation)


def get_job_snapshot(job_id: str, db: Session | None = None) -> dict[str, Any]:
    def operation(session: Session) -> dict[str, Any]:
        job = get_analysis_job(session, job_id)
        if job is None:
            raise KeyError(job_id)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def get_persisted_job_snapshot(
    job_id: str,
    db: Session | None = None,
) -> dict[str, Any]:
    def operation(session: Session) -> dict[str, Any]:
        job = get_analysis_job(session, job_id)
        if job is None:
            raise KeyError(job_id)
        return _persisted_snapshot(job)

    return _run_in_session(db, operation)


def get_active_job_snapshot(db: Session | None = None) -> dict[str, Any] | None:
    def operation(session: Session) -> dict[str, Any] | None:
        active_job = get_active_analysis_job(session)
        if active_job is None:
            return None
        return _public_snapshot(active_job)

    return _run_in_session(db, operation)


def get_active_persisted_job_snapshot(
    db: Session | None = None,
) -> dict[str, Any] | None:
    def operation(session: Session) -> dict[str, Any] | None:
        active_job = get_active_analysis_job(session)
        if active_job is None:
            return None
        return _persisted_snapshot(active_job)

    return _run_in_session(db, operation)


def update_job(
    job_id: str,
    db: Session | None = None,
    **updates: Any,
) -> dict[str, Any]:
    update = AnalysisJobUpdate.model_validate(updates)

    def operation(session: Session) -> dict[str, Any]:
        job = update_analysis_job(session, job_id, update)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def update_job_step(
    job_id: str,
    step_name: AnalysisJobStepName,
    status: AnalysisJobStepStatus,
    message: str,
    *,
    db: Session | None = None,
    error_code: str | None = None,
    progress: dict[str, int] | None = None,
) -> dict[str, Any]:
    step_progress = (
        AnalysisJobStepProgress.model_validate(progress)
        if progress is not None
        else None
    )
    step_update = AnalysisJobStepUpdate(
        step_name=step_name,
        status=status,
        message=message,
        error_code=error_code,
        progress=step_progress,
    )

    def operation(session: Session) -> dict[str, Any]:
        job = update_analysis_job_step(session, job_id, step_update)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def fail_job(
    job_id: str,
    detail: str,
    *,
    db: Session | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    failure = AnalysisJobFailure(detail=detail, error_code=error_code)

    def operation(session: Session) -> dict[str, Any]:
        job = fail_analysis_job(session, job_id, failure)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def cancel_job(
    job_id: str,
    *,
    detail: str = "Cancelled by user.",
    db: Session | None = None,
    error_code: str = "cancelled_by_user",
) -> dict[str, Any]:
    def operation(session: Session) -> dict[str, Any]:
        job = cancel_analysis_job(session, job_id, detail, error_code=error_code)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def is_job_cancelled(job_id: str, db: Session | None = None) -> bool:
    """Return True once a cancel signal has been received for ``job_id``.

    W13-3 (Codex H4): semantics widened from terminal-only to "cancel
    signalled". The worker poll primitive must see the signal during the
    drain window (`status == "cancelling"`) so the next cancel-poll point
    raises ``AnalysisCancelledError``; once the drain completes the row
    transitions to terminal `cancelled` and this still returns True.
    Unknown rows still return False — the worker uses this to gate
    behavior, and a missing snapshot must not crash the heartbeat.
    """

    def operation(session: Session) -> bool:
        job = get_analysis_job(session, job_id)
        if job is None:
            return False
        return job.status in ("cancelled", "cancelling")

    return _run_in_session(db, operation)


def reject_static_job(
    job_id: str,
    detail: str,
    *,
    db: Session | None = None,
    error_code: str = "static_gate_blocked",
    static_report_path: str | None = None,
) -> dict[str, Any]:
    """Drive a job to terminal ``rejected_static`` (ES-3b static-gate BLOCK).

    Worker-facing wrapper around ``crud.reject_analysis_job_static``. Called
    from ``analysis_service.run_analysis_job`` when the static pre-check gate
    raises ``StaticAnalysisBlockedError``: the in-flight ``decision_gate`` step
    is completed, the dynamic sandbox stages are marked skipped, the persisted
    combined-bundle path is recorded in ``static_report_path``, and the
    single-active slot releases so ``reserve_job`` can admit the next job.
    """

    def operation(session: Session) -> dict[str, Any]:
        job = reject_analysis_job_static(
            session,
            job_id,
            detail,
            error_code=error_code,
            static_report_path=static_report_path,
        )
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def finalize_cancelled_job(
    job_id: str,
    *,
    detail: str = "Cancelled by user.",
    db: Session | None = None,
    error_code: str = "cancelled_by_user",
) -> dict[str, Any]:
    """Promote a draining job to terminal `cancelled` (W13-3.4 helper).

    Worker-facing wrapper around
    ``lifecycle.finalize_cancelled_analysis_job``. Called from
    ``analysis_service.run_analysis_job`` once the worker observes
    ``AnalysisCancelledError`` and the in-flight step has been drained.
    """

    def operation(session: Session) -> dict[str, Any]:
        job = finalize_cancelled_analysis_job(
            session, job_id, detail, error_code=error_code
        )
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def complete_job(
    job_id: str,
    result: AnalyzeResponse,
    *,
    db: Session | None = None,
    static_report_path: str | None = None,
) -> dict[str, Any]:
    # ES-5 (ADR 0016): ``static_report_path`` records the persisted static-only
    # combined bundle for an ALLOW/WARN job (the BLOCK path records it via
    # ``reject_static_job`` instead). ``None`` when the static gate did not run
    # (flag OFF) leaves the column NULL, so the dynamic-only completion is
    # unchanged.
    update = AnalysisJobUpdate(
        status="completed",
        current_step=None,
        message=result.message,
        report_path=result.report_path,
        static_report_path=static_report_path,
        install_output=result.install_output,
        automation_output=result.automation_output,
        finished_at=now(),
    )

    def operation(session: Session) -> dict[str, Any]:
        job = complete_analysis_job(session, job_id, update)
        return _public_snapshot(job)

    return _run_in_session(db, operation)


def recover_interrupted_jobs(db: Session | None = None) -> int:
    detail = "Analysis job was interrupted by an API restart. Start a new run."

    def operation(session: Session) -> int:
        return recover_interrupted_analysis_jobs(session, _PROCESS_BOOT_ID, detail)

    return _run_in_session(db, operation)


# S2 (W23 B3): the operator-facing detail stamped on a reaped wedged job.
_STALE_REAP_DETAIL = (
    "Analysis job stopped sending heartbeats and was recovered so the queue "
    "could continue. The worker hung or crashed; start a new run."
)


def touch_job_heartbeat(job_id: str, db: Session | None = None) -> int:
    """Stamp the liveness heartbeat for a running job (S2 / W23 B3).

    Worker-facing wrapper around ``crud.touch_analysis_job_heartbeat``. Returns
    the affected row count (0 when the job is gone or no longer ``running``).
    """

    def operation(session: Session) -> int:
        return touch_analysis_job_heartbeat(session, job_id)

    return _run_in_session(db, operation)


def reap_stale_running_jobs(db: Session | None = None) -> int:
    """Recover same-boot ``running`` jobs whose heartbeat has gone stale.

    Worker-facing wrapper around ``crud.reap_stale_running_analysis_jobs``,
    bound to this process's boot id and the configured stale timeout. Invoked
    from the submit + status surfaces and the background reaper thread so a
    hung/crashed worker releases the single-active slot without an API restart
    (closes v1.0 bar B3). Returns the number of rows reaped.
    """

    def operation(session: Session) -> int:
        return reap_stale_running_analysis_jobs(
            session,
            _PROCESS_BOOT_ID,
            stale_after_s=_STALE_JOB_TIMEOUT_S,
            detail=_STALE_REAP_DETAIL,
        )

    return _run_in_session(db, operation)


def run_job_heartbeat(
    job_id: str,
    stop_event: threading.Event,
    *,
    interval_s: float = _HEARTBEAT_INTERVAL_S,
) -> None:
    """Heartbeat-thread loop: stamp ``last_heartbeat_at`` until stopped (S2).

    Spanning claim → terminal on a dedicated thread (NOT the per-phase
    monitoring heartbeat) so the stale-running reaper can tell a hung worker
    from a slow ``reset_sandbox`` / ``install_extension`` phase. Best-effort:
    a transient DB error or a vanished row must never crash the thread — the
    reaper falls back to ``started_at`` when ``last_heartbeat_at`` is NULL.
    Ticks immediately, then every ``interval_s`` until ``stop_event`` is set.
    """
    while not stop_event.is_set():
        try:
            touch_job_heartbeat(job_id)
        except (SQLAlchemyError, KeyError):
            logger.debug("heartbeat tick skipped for job %s.", job_id)
        stop_event.wait(interval_s)


def _stale_reaper_loop(
    stop_event: threading.Event,
    interval_s: float,
    sweep: Callable[[], int],
) -> None:
    """Background reaper loop: periodically sweep stale same-boot running jobs.

    Sleeps first so spawning the thread is side-effect-free (a freshly started
    process has nothing stale yet, and tests that immediately stop the event
    never touch the DB). A DB outage degrades to a logged skip, never a crash.
    """
    while not stop_event.is_set():
        stop_event.wait(interval_s)
        if stop_event.is_set():
            break
        try:
            sweep()
        except SQLAlchemyError:
            logger.debug("stale-job reaper sweep skipped (DB unavailable).")


def start_stale_job_reaper(
    stop_event: threading.Event | None = None,
    *,
    interval_s: float = _REAPER_SWEEP_INTERVAL_S,
    sweep: Callable[[], int] | None = None,
) -> threading.Thread:
    """Spawn the daemon background reaper thread (S2 / W23 B3).

    Started at app boot (``main.create_app``) so a same-boot wedged worker is
    auto-recovered even if the operator never re-submits. Daemon — dies with the
    process; the returned thread + the ``stop_event`` make it deterministically
    stoppable in tests. ``sweep`` is injectable for testing the loop without a DB.
    """
    event = stop_event if stop_event is not None else threading.Event()
    target_sweep = sweep if sweep is not None else reap_stale_running_jobs
    thread = threading.Thread(
        target=_stale_reaper_loop,
        args=(event, interval_s, target_sweep),
        name="extrace-stale-job-reaper",
        daemon=True,
    )
    thread.start()
    return thread


__all__ = [
    "ActiveAnalysisJobError",
    "JobNotCancellableError",
    "build_report_name",
    "cancel_job",
    "complete_job",
    "create_job_snapshot",
    "empty_job_steps",
    "fail_job",
    "finalize_cancelled_job",
    "get_active_job_snapshot",
    "get_active_persisted_job_snapshot",
    "get_job_snapshot",
    "get_persisted_job_snapshot",
    "is_job_cancelled",
    "now",
    "reap_stale_running_jobs",
    "recover_interrupted_jobs",
    "reject_static_job",
    "reserve_job",
    "run_job_heartbeat",
    "start_stale_job_reaper",
    "store_job",
    "touch_job_heartbeat",
    "update_job",
    "update_job_step",
]
