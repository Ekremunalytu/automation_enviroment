"""W13-4 (cancellation lifecycle hardening): integration coverage for
``analysis_service.run_analysis_job`` exception handler dispatch.

W13-3 wired ``run_analysis_job`` to call ``job_service.finalize_cancelled_job``
on **both** exception paths:

1. **AnalysisCancelledError path** (``analysis_service.py:236-256``):
   the worker observed a cancel signal at one of the 5
   ``_raise_if_cancelled`` poll points (or via the monitoring
   heartbeat). The handler must promote the row from ``cancelling``
   to terminal ``cancelled`` so the partial-unique-index lock
   releases.
2. **Hard-error-with-cancel-signal path** (``analysis_service.py:264-292``):
   the worker hit a ``FileNotFoundError``/``ExecutorError``/etc. but
   ``is_job_cancelled(job_id)`` returns True (the cancel signal arrived
   during the failure). Cancel intent is authoritative — the row must
   land as ``cancelled``, not ``failed``.

W13-3 close evidence (W13-3.6 § Threat coverage) names this dispatch
as the linchpin of the cancel-during-error race fix; without it a
worker that crashes on shutdown could overwrite the cancel intent.
The 6 W13-3 architecture gates pin AST invariants on
``execute_analysis_request`` (poll points + helper export) but do
NOT cover ``run_analysis_job``'s exception-handler shape — these
tests close that gap.

W13-4.2 lands as ``@pytest.mark.skip`` RED precursors; W13-4.5
removes the skip.
"""

from __future__ import annotations

from unittest.mock import patch

from appcore.contracts.schema_defs.static_analysis_bundle import StaticAnalysisReport
from appcore.contracts.schemas import AnalyzeRequest
from executor.control import ExecutorError
from executor.static_control import StaticAnalyzerError
from packages.analysis_contracts.static_detection import (
    StaticDetectionReport,
    StaticGateDecision,
    StaticGateOutcome,
)
from workflows.marketplace import analysis_service, job_service
from workflows.marketplace.analysis_errors import AnalysisCancelledError
from workflows.marketplace.static_analysis import (
    StaticAnalysisBlockedError,
    StaticReportError,
)

_BLOCKED_STATIC_REPORT = StaticAnalysisReport(
    detection_report=StaticDetectionReport(),
    gate_outcome=StaticGateOutcome(
        decision=StaticGateDecision.BLOCK, blocked_by=["extrace.s2.typosquat"]
    ),
)


def _request() -> AnalyzeRequest:
    return AnalyzeRequest(
        publisher="ms-python",
        name="python",
        version="2026.5.0",
        scenario=None,
        analysis_profile=None,
    )


def test_run_analysis_job_finalizes_on_analysis_cancelled_error() -> None:
    """``AnalysisCancelledError`` path: handler calls ``finalize_cancelled_job`` exactly once.

    Wiring under test (analysis_service.py:236-256):

    .. code-block:: python

        try:
            result = execute_analysis_request(...)
        except AnalysisCancelledError:
            try:
                job_service.finalize_cancelled_job(job_id)
            except (job_service.JobNotCancellableError, KeyError):
                ...
            return

    The handler must NOT call ``fail_job`` (that would flip the row to
    ``failed`` instead of ``cancelled``) and must NOT call
    ``complete_job``. The W13-3 contract: ``finalize_cancelled_job``
    is the single terminal writer on the cancel path.
    """
    job_id = "test-cancel-job-uuid"

    with (
        patch.object(
            analysis_service,
            "execute_analysis_request",
            side_effect=AnalysisCancelledError("simulated worker poll observed cancel"),
        ),
        patch.object(
            job_service, "get_job_snapshot", return_value={"report_path": "r.json"}
        ),
        patch.object(job_service, "update_job") as update_job,
        patch.object(
            job_service, "finalize_cancelled_job", return_value={"status": "cancelled"}
        ) as finalize,
        patch.object(job_service, "fail_job") as fail_job,
        patch.object(job_service, "complete_job") as complete_job,
        patch.object(analysis_service, "_open_job_session") as open_session,
    ):
        analysis_service.run_analysis_job(job_id, _request())

    # W13-13 Path B: the worker entry no longer routes the queued -> running
    # transition through ``job_service.update_job``; it mutates the locked
    # row directly under ``with_for_update()`` and ``db.commit()``s. So
    # the wrapper helper must NOT be called on the cancel-handler path.
    # The handler still dispatches ``finalize_cancelled_job`` exactly once.
    update_job.assert_not_called()
    finalize.assert_called_once_with(job_id)
    fail_job.assert_not_called()
    complete_job.assert_not_called()
    # The session opened in run_analysis_job is closed in the finally block.
    open_session.return_value.close.assert_called_once()


def test_run_analysis_job_finalizes_on_hard_error_with_cancel_signal() -> None:
    """Hard-error path: ``ExecutorError`` + ``is_job_cancelled``=True → finalize, NOT fail.

    Wiring under test (analysis_service.py:264-292):

    .. code-block:: python

        except (FileNotFoundError, ExecutorError, ...) as exc:
            if job_service.is_job_cancelled(job_id):
                try:
                    job_service.finalize_cancelled_job(job_id)
                except (job_service.JobNotCancellableError, KeyError):
                    ...
                return
            job_service.fail_job(job_id, str(exc), ...)

    Cancel intent is authoritative: an incidental ExecutorError that
    arrives after the cancel signal must NOT be allowed to flip the
    row to ``failed`` — it lands as ``cancelled`` via the finalize
    helper. Without this branch, a worker that hit a sandbox-shutdown
    error during cancel would record the wrong terminal status.
    """
    job_id = "test-cancel-during-error-uuid"

    with (
        patch.object(
            analysis_service,
            "execute_analysis_request",
            side_effect=ExecutorError("automation crashed during cancel-induced reset"),
        ),
        patch.object(
            job_service, "get_job_snapshot", return_value={"report_path": "r.json"}
        ),
        patch.object(job_service, "update_job"),
        # Critical: is_job_cancelled returns True because the row was
        # already drained to `cancelling` by the API cancel call.
        patch.object(job_service, "is_job_cancelled", return_value=True),
        patch.object(
            job_service, "finalize_cancelled_job", return_value={"status": "cancelled"}
        ) as finalize,
        patch.object(job_service, "fail_job") as fail_job,
        patch.object(job_service, "complete_job") as complete_job,
        patch.object(analysis_service, "_open_job_session"),
    ):
        analysis_service.run_analysis_job(job_id, _request())

    # Critical assertion: finalize wins over fail_job. The W13-3 hard
    # error handler explicitly returns BEFORE falling through to fail_job
    # when is_job_cancelled is True.
    finalize.assert_called_once_with(job_id)
    fail_job.assert_not_called()
    complete_job.assert_not_called()


def test_run_analysis_job_rejects_static_on_blocked_error() -> None:
    """ES-3b: a static-gate BLOCK routes to ``reject_static_job`` (terminal
    ``rejected_static``), NOT ``fail_job``, and records the per-job static
    report path.

    Wiring under test: the dedicated ``except StaticAnalysisBlockedError``
    handler in ``run_analysis_job``, placed AHEAD of the generic recoverable
    clause (which also lists ``StaticAnalysisBlockedError``), calls
    ``reject_static_job(job_id, str(exc), static_report_path=f"static_report_{job_id}.json")``.
    The combined bundle was already persisted by the gate stage; the handler
    only records its path on the row.
    """
    job_id = "test-static-block-uuid"

    with (
        patch.object(
            analysis_service,
            "execute_analysis_request",
            side_effect=StaticAnalysisBlockedError(
                "Static pre-check blocked the extension (extrace.s2.typosquat).",
                static_report=_BLOCKED_STATIC_REPORT,
            ),
        ),
        patch.object(
            job_service,
            "reject_static_job",
            return_value={"status": "rejected_static"},
        ) as reject_static,
        patch.object(job_service, "fail_job") as fail_job,
        patch.object(job_service, "complete_job") as complete_job,
        patch.object(job_service, "finalize_cancelled_job") as finalize,
        patch.object(analysis_service, "_open_job_session"),
    ):
        analysis_service.run_analysis_job(job_id, _request())

    # BLOCK is routed to the dedicated reject path, not fail/complete/cancel.
    reject_static.assert_called_once()
    assert reject_static.call_args.kwargs.get("static_report_path") == (
        f"static_report_{job_id}.json"
    )
    fail_job.assert_not_called()
    complete_job.assert_not_called()
    finalize.assert_not_called()


def test_run_analysis_job_fails_on_static_analyzer_error() -> None:
    """A static-stage INFRASTRUCTURE failure (analyzer container missing / exec
    error / timeout -> ``StaticAnalyzerError``) must fail the job CLOSED
    (terminal ``failed`` via ``fail_job``), NOT escape the worker and leave the
    row active holding the partial-unique-index lock.

    Regression for the pre-fix P1: ``StaticAnalyzerError`` subclasses
    ``Exception`` only, so it matched none of the worker's except clauses and
    propagated out of ``run_analysis_job`` without any terminal write — the job
    stayed ``running`` forever and wedged ``reserve_job``.
    """
    job_id = "test-static-analyzer-error-uuid"

    with (
        patch.object(
            analysis_service,
            "execute_analysis_request",
            side_effect=StaticAnalyzerError(
                "static-analyzer docker exec failed", returncode=1, output="boom"
            ),
        ),
        patch.object(job_service, "is_job_cancelled", return_value=False),
        patch.object(job_service, "fail_job") as fail_job,
        patch.object(job_service, "reject_static_job") as reject_static,
        patch.object(job_service, "complete_job") as complete_job,
        patch.object(job_service, "finalize_cancelled_job") as finalize,
        patch.object(analysis_service, "_open_job_session"),
    ):
        # Must NOT raise out of the worker (pre-fix it propagated uncaught).
        analysis_service.run_analysis_job(job_id, _request())

    fail_job.assert_called_once()
    assert fail_job.call_args.args[0] == job_id
    reject_static.assert_not_called()
    complete_job.assert_not_called()
    finalize.assert_not_called()


def test_run_analysis_job_fails_on_static_report_error() -> None:
    """An unreadable / truncated / schema-invalid analyzer report
    (``StaticReportError``, a ``RuntimeError`` subclass) must also fail the job
    CLOSED via ``fail_job`` rather than escape the worker — fail-closed is the
    documented contract (a broken analyzer must never be mistaken for an ALLOW).
    """
    job_id = "test-static-report-error-uuid"

    with (
        patch.object(
            analysis_service,
            "execute_analysis_request",
            side_effect=StaticReportError("static analyzer report unreadable"),
        ),
        patch.object(job_service, "is_job_cancelled", return_value=False),
        patch.object(job_service, "fail_job") as fail_job,
        patch.object(job_service, "reject_static_job") as reject_static,
        patch.object(job_service, "complete_job") as complete_job,
        patch.object(job_service, "finalize_cancelled_job") as finalize,
        patch.object(analysis_service, "_open_job_session"),
    ):
        analysis_service.run_analysis_job(job_id, _request())

    fail_job.assert_called_once()
    assert fail_job.call_args.args[0] == job_id
    reject_static.assert_not_called()
    complete_job.assert_not_called()
    finalize.assert_not_called()
