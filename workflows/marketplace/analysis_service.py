"""Sandbox analysis orchestration for marketplace workflow."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepName,
    AnalysisJobStepStatus,
)
from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from appcore.logging import get_extrace_logger
from appcore.storage.crud_ops.analysis_jobs.lifecycle import (
    WorkerEntryOutcome,
    claim_queued_analysis_job_at_worker_entry,
)
from executor.control import (
    ExecutorControl,
    ExecutorError,
    default_executor_control,
)
from packages.analysis_contracts import redact_secrets
from workflows.marketplace import client as marketplace_client
from workflows.marketplace import job_service
from workflows.marketplace.analysis_errors import (
    ActivationReportLoadError,
    AnalysisCancelledError,
    TriggerPlanError,
)
from workflows.marketplace.analysis_execution import (
    StepReporter as _StepReporter,
)
from workflows.marketplace.analysis_execution import (
    build_triggers as _build_triggers,
)
from workflows.marketplace.analysis_execution import (
    install_extension as _install_extension,
)
from workflows.marketplace.analysis_execution import (
    raise_if_cancelled as _raise_if_cancelled,
)
from workflows.marketplace.analysis_execution import (
    reset_sandbox as _reset_sandbox,
)
from workflows.marketplace.analysis_execution import (
    run_monitoring as _run_monitoring,
)
from workflows.marketplace.analysis_reports import (
    build_analysis_bundle_from_report_name,
    run_local_analysis,
)
from workflows.marketplace.analysis_reports import (
    build_report_messages as _build_report_messages,
)
from workflows.marketplace.analysis_reports import (
    load_report_payload as _load_report_payload,
)
from workflows.marketplace.analysis_reports import (
    trigger_payload_exists as _trigger_payload_exists,
)
from workflows.marketplace.analysis_reports import (
    validate_trigger_plan_report as _validate_trigger_plan_report,
)
from workflows.marketplace.trigger_service import TriggerPlan, build_trigger_payload

logger = get_extrace_logger("extrace.workflows.marketplace.analysis_service")


# W15-1 (Codex 2026-05-10 M10 close-out): the analyze pipeline raises this
# closed taxonomy into both the sync ``POST /api/marketplace/analyze``
# endpoint and the async job worker. Both surfaces must catch the same set
# so the same request shape never receives two different status codes.
# ``ANALYZE_PROGRAMMING_ERROR_TYPES`` and ``ANALYZE_RECOVERABLE_ERROR_TYPES``
# are kept as separate tuples because the async worker treats them
# differently (recoverable -> ``fail_job`` then ``return``; programming-class
# -> ``fail_job`` then ``raise`` so the worker thread surfaces the bug). The
# union ``ANALYZE_ERROR_TYPES`` is what the sync entry catches as a single
# except clause; the helper ``analyze_error_to_http_response`` maps each
# class to an HTTPException with a status code that mirrors the async
# ``fail_job`` semantics.
ANALYZE_RECOVERABLE_ERROR_TYPES: tuple[type[Exception], ...] = (
    FileNotFoundError,
    ExecutorError,
    TriggerPlanError,
    OSError,
    SQLAlchemyError,
    ValueError,
)
ANALYZE_PROGRAMMING_ERROR_TYPES: tuple[type[Exception], ...] = (
    TypeError,
    AttributeError,
)
ANALYZE_ERROR_TYPES: tuple[type[Exception], ...] = (
    ANALYZE_RECOVERABLE_ERROR_TYPES + ANALYZE_PROGRAMMING_ERROR_TYPES
)


def _open_job_session() -> Session:
    from appcore.db.session import SessionLocal

    return SessionLocal()


def ensure_vsix_exists(request: AnalyzeRequest) -> Path:
    vsix_path = marketplace_client.get_vsix_path(
        request.publisher,
        request.name,
        request.version,
    )
    if not vsix_path.exists():
        raise FileNotFoundError(
            f"VSIX file not found: {vsix_path.name}. "
            "Download the extension first via /api/marketplace/download."
        )
    return vsix_path


def execute_analysis_request(
    request: AnalyzeRequest,
    db: Session,
    progress_callback: Callable[
        [
            AnalysisJobStepName,
            AnalysisJobStepStatus,
            str,
            str | None,
            dict[str, int] | None,
        ],
        None,
    ]
    | None = None,
    report_name: str | None = None,
    executor_control: ExecutorControl | None = None,
    cancel_check: Callable[[], bool] | None = None,
    on_cancel_signal: Callable[[], None] | None = None,
) -> AnalyzeResponse:
    if executor_control is None:
        executor_control = default_executor_control
    reporter = _StepReporter(progress_callback)
    # W13-3 (Codex H4): cancel-poll points cover the gaps between the
    # 5-second heartbeat ticks. Each major phase boundary checks the
    # signal so a cancellation never has to wait for `_reset_sandbox` /
    # `_install_extension` / `_build_triggers` to complete before
    # propagating, and the worker drains within milliseconds of the
    # cancel API call.
    _raise_if_cancelled(cancel_check)
    ensure_vsix_exists(request)
    _raise_if_cancelled(cancel_check)
    _reset_sandbox(reporter, executor_control)
    _raise_if_cancelled(cancel_check)
    # W13-11 (Codex F1 close-pass for W13-1 H6): host-side eager-consume
    # of the per-launch HMAC python secret. ``_reset_sandbox`` has just
    # restarted VS Code so ``launch_vscode.sh`` wrote a fresh secret to
    # ``/results/_extrace_harness_python_secret`` (0600 executor:executor).
    # We read+unlink it here BEFORE the analyzed VSIX is admitted, so
    # the same-UID target cannot reach the file during the prior
    # install -> setup_monitor window. The value is held in this
    # frame's memory and threaded into ``_run_monitoring`` below.
    harness_python_secret = executor_control.consume_harness_python_secret()
    _raise_if_cancelled(cancel_check)
    install_output = _install_extension(request, reporter, executor_control)
    _raise_if_cancelled(cancel_check)
    trigger_plan = _build_triggers(
        db,
        request,
        reporter,
        build_trigger_payload_func=build_trigger_payload,
        trigger_plan_type=TriggerPlan,
    )
    report_name = report_name or job_service.build_report_name(request, uuid4().hex)
    _raise_if_cancelled(cancel_check)
    automation_output, finalize_message = _run_monitoring(
        request,
        report_name,
        trigger_plan,
        reporter,
        executor_control,
        trigger_payload_exists=_trigger_payload_exists,
        load_report_payload=_load_report_payload,
        validate_trigger_plan_report=_validate_trigger_plan_report,
        build_report_messages=_build_report_messages,
        cancel_check=cancel_check,
        on_cancel_signal=on_cancel_signal,
        harness_python_secret=harness_python_secret,
    )

    return AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            f"installed and analyzed successfully. {finalize_message}"
        ),
        install_output=install_output,
        automation_output=automation_output,
        report_path=report_name,
    )


def map_executor_error(exc: ExecutorError) -> HTTPException:
    raw = str(exc)
    error_id = uuid4().hex[:8]
    if "install" in raw.lower():
        public_detail = "Failed to install extension in executor."
    else:
        public_detail = "Automation failed in sandbox."
    # W10-7 (closes [FOLLOWUP w8-6-output-signals-redaction]): the W8-7
    # detail-leakage close routes only the generic public detail to the
    # HTTP response; the raw exception text still lands in logger.warning
    # for triage. Redact secrets before logging so log aggregation /
    # ingestion pipelines never see API keys / DB URLs / OAuth tokens
    # leaked through executor exception text.
    logger.warning(
        "executor_error error_id=%s message=%s",
        error_id,
        redact_secrets(raw),
    )
    return HTTPException(
        status_code=502,
        detail=f"{public_detail} (error_id={error_id})",
    )


def analyze_error_to_http_response(exc: Exception) -> HTTPException:
    """Map an ``ANALYZE_ERROR_TYPES`` member to its HTTPException counterpart.

    Status map (mirrors the async ``fail_job`` semantics so the same
    request shape returns the same status on both surfaces):

    - ``ExecutorError`` -> 502 (delegates to :func:`map_executor_error`
      for the structured ``error_id`` redaction contract).
    - ``FileNotFoundError`` -> 404 (missing prerequisite resource).
    - ``ActivationReportLoadError`` / ``TriggerPlanError`` / ``OSError``
      / ``SQLAlchemyError`` -> 502 (upstream / infrastructure faults).
    - ``ValueError`` (other than ``ActivationReportLoadError`` which is
      checked first) -> 400 (client-side data problems).
    - ``TypeError`` / ``AttributeError`` -> 500 (programming-class error
      surfaced explicitly so the body shape is consistent with the rest
      of the taxonomy instead of FastAPI's default 500 page).
    """
    if isinstance(exc, ExecutorError):
        return map_executor_error(exc)
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    # ActivationReportLoadError is a ValueError subclass — match it before
    # the generic ValueError branch so it lands on 502 (upstream-report
    # failure), not 400 (client input).
    if isinstance(
        exc,
        (ActivationReportLoadError, TriggerPlanError, OSError, SQLAlchemyError),
    ):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, (TypeError, AttributeError)):
        return HTTPException(status_code=500, detail=str(exc))
    raise AssertionError(
        f"Unmapped analyze error class: {type(exc).__name__}; update "
        "ANALYZE_ERROR_TYPES and analyze_error_to_http_response together."
    )


def run_analysis_job(job_id: str, request: AnalyzeRequest) -> None:
    # W13-13 (CLOSE-GATE codex-second-opinion-F3) + W16-2 (AGENTS.md:57
    # facade compliance): the worker-entry seam is owned by the
    # lifecycle CRUD facade. ``claim_queued_analysis_job_at_worker_entry``
    # takes a ``select(...).with_for_update()`` row lock, branches on
    # observed status, and either finalizes a ``cancelling`` row in
    # place (calling ``finalize_cancelled_analysis_job`` under the held
    # lock — avoiding the wrapper's nested ``SessionLocal()`` deadlock)
    # or atomically promotes ``queued -> running``. The W13-3
    # ``AnalysisCancelledError`` handler below continues to use
    # ``job_service.finalize_cancelled_job`` because by the time it
    # fires the entry-block transaction has already committed and
    # released the lock.
    #
    # Only the ``CLAIMED`` outcome continues to the analysis flow;
    # every other outcome (ROW_MISSING / ALREADY_TERMINAL /
    # CANCELLING_FINALIZED / CANCELLING_RACE) returns immediately.
    # Pre-W16-2 this dispatch lived inline in source order; the
    # architecture gate
    # ``tests/architecture/test_run_analysis_job_entry_snapshot.py``
    # now enforces the facade boundary instead of the inline AST shape.
    db = _open_job_session()
    try:
        claim = claim_queued_analysis_job_at_worker_entry(
            db,
            job_id,
            fallback_report_name=job_service.build_report_name(
                request, job_id
            ),
            cancel_detail="Cancelled before worker started.",
        )
        if claim.outcome is WorkerEntryOutcome.ROW_MISSING:
            logger.warning(
                "Worker entry: job %s vanished before snapshot lock; exiting.",
                job_id,
            )
            return
        if claim.outcome is WorkerEntryOutcome.ALREADY_TERMINAL:
            terminal_status = claim.job.status if claim.job else "unknown"
            logger.info(
                "Worker entry: job %s already terminal (%s); exiting "
                "without running.",
                job_id,
                terminal_status,
            )
            return
        if claim.outcome is WorkerEntryOutcome.CANCELLING_FINALIZED:
            # User cancelled in the reserve_job -> worker-entry window.
            # The lifecycle facade finalized the drain under the held
            # row lock; nothing more for this thread to do.
            return
        if claim.outcome is WorkerEntryOutcome.CANCELLING_RACE:
            # Race: another writer drove the row terminal between the
            # entry-block SELECT...FOR UPDATE and the in-place finalize.
            # Idempotent — nothing to clean up.
            logger.debug(
                "Worker entry: finalize_cancelled_analysis_job "
                "skipped for job %s (already terminal or absent).",
                job_id,
            )
            return
        # WorkerEntryOutcome.CLAIMED: row transitioned ``queued -> running``
        # under the held lock and the transition committed. Pull the
        # caller-visible report_path from the claim so the downstream
        # analysis flow uses the same name the facade wrote to the row.
        assert claim.report_path is not None, (
            "WorkerEntryOutcome.CLAIMED MUST populate report_path"
        )
        report_name = claim.report_path

        def progress_update(
            step: AnalysisJobStepName,
            status: AnalysisJobStepStatus,
            message: str,
            error_code: str | None = None,
            progress: dict[str, int] | None = None,
        ) -> None:
            try:
                job_service.update_job_step(
                    job_id,
                    step,
                    status,
                    message,
                    error_code=error_code,
                    progress=progress,
                )
            except KeyError:
                # Job row vanished (very unlikely outside tests); swallow so the
                # automation thread doesn't crash on a missing snapshot.
                logger.warning(
                    "Progress update dropped: job %s no longer exists.", job_id
                )

        def cancel_check() -> bool:
            return job_service.is_job_cancelled(job_id)

        try:
            result = execute_analysis_request(
                request,
                db,
                progress_callback=progress_update,
                report_name=report_name,
                cancel_check=cancel_check,
            )
        except AnalysisCancelledError:
            # W13-3 (Codex H4): worker observed the cancel signal at one of
            # the cancel-poll points (or via the monitoring heartbeat) and
            # has drained the in-flight step. Promote the row from the
            # non-terminal `cancelling` drain state to terminal `cancelled`
            # so the partial-unique-index lock releases and reserve_job can
            # admit the next job. The CRUD helper is idempotent on terminal
            # states via JobNotCancellableError, so a duplicate transition
            # cannot regress the row.
            try:
                job_service.finalize_cancelled_job(job_id)
            except (job_service.JobNotCancellableError, KeyError):
                # Idempotent: row may already be terminal (duplicate
                # finalize) or already gone (test fixtures / very late
                # worker exit). Either way nothing to clean up.
                logger.debug(
                    "finalize_cancelled_job skipped for job %s (already terminal "
                    "or absent).",
                    job_id,
                )
            return
        except ANALYZE_PROGRAMMING_ERROR_TYPES as exc:
            job_service.fail_job(
                job_id,
                str(exc),
                error_code=getattr(exc, "error_code", None),
            )
            raise
        except ANALYZE_RECOVERABLE_ERROR_TYPES as exc:
            if job_service.is_job_cancelled(job_id):
                # W13-3: cancel signal arrived during a hard error in the
                # worker thread. Treat the row as draining and finalize to
                # terminal `cancelled` rather than `failed` — the user's
                # cancel intent is authoritative over an incidental
                # downstream error.
                try:
                    job_service.finalize_cancelled_job(job_id)
                except (job_service.JobNotCancellableError, KeyError):
                    logger.debug(
                        "finalize_cancelled_job skipped for job %s (already "
                        "terminal or absent) from error path.",
                        job_id,
                    )
                return
            job_service.fail_job(
                job_id,
                str(exc),
                error_code=getattr(exc, "error_code", None),
            )
            return
    finally:
        db.close()

    job_service.complete_job(job_id, result)


__all__ = [
    "ANALYZE_ERROR_TYPES",
    "ANALYZE_PROGRAMMING_ERROR_TYPES",
    "ANALYZE_RECOVERABLE_ERROR_TYPES",
    "TriggerPlanError",
    "analyze_error_to_http_response",
    "build_analysis_bundle_from_report_name",
    "ensure_vsix_exists",
    "execute_analysis_request",
    "map_executor_error",
    "run_analysis_job",
    "run_local_analysis",
]
