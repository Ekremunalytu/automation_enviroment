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


from appcore.contracts.schemas import AnalyzeRequest
from executor.control import ExecutorError
from workflows.marketplace import analysis_service, job_service
from workflows.marketplace.analysis_errors import AnalysisCancelledError


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

    # Initial running state was set then handler dispatched finalize.
    update_job.assert_called_once()
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
