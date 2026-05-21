"""W13-13 (CLOSE-GATE codex-second-opinion-F3): worker-start cancel-race CAS.

W13-3 wired a two-phase cancel state machine: ``cancel_analysis_job``
atomically flips ``queued/running -> cancelling`` under
``with_for_update()`` and ``finalize_cancelled_analysis_job`` is the
sole writer that promotes ``cancelling -> cancelled``. The contract is
"cancel intent authoritative" — once the row enters ``cancelling``,
the worker must not be allowed to overwrite it back to ``running``.

The Codex Cloud second-opinion review (`2026-05-11`) surfaced that
``analysis_service.run_analysis_job`` violates this at the worker-entry
seam: the function spawned by ``router.start_analysis_job`` does an
**unconditional** ``job_service.update_job(job_id, status="running",
...)`` as its first DB write (pre-W13-13 ``analysis_service.py:198-211``).
A cancel that lands in the window between ``reserve_job`` commit and
the worker thread reaching ``run_analysis_job`` is silently overwritten
back to ``running``; ``cancel_check`` then returns False for the rest
of the scan and the cancel intent is lost.

W13-13 closes this via **Path B** — at worker entry, take a
``select(...).with_for_update()`` row-level lock and branch on the
observed status:

- ``cancelling`` -> ``finalize_cancelled_analysis_job(db, ...)`` + return
  (symmetric with the existing W13-3 ``AnalysisCancelledError`` handler
  at ``analysis_service.py:247-267``)
- terminal (``completed``/``failed``/``cancelled``) -> log + rollback + return
- row missing -> log warning + rollback + return
- ``queued`` -> atomic transition to ``running`` under the lock + commit
  + proceed with the existing analysis flow

This file pins the three observable behaviors at the worker-entry
boundary. The architecture gate in
``tests/architecture/test_run_analysis_job_entry_snapshot.py`` enforces
the structural lock-ordering invariant via an AST walk; these
behavioral cases pin the observable row state after
``run_analysis_job`` returns.

Test seam choice. The W13-4 file
``tests/workflows/marketplace/test_run_analysis_job_finalize.py``
covers the W13-3 *exception-handler* dispatch via heavy mocking
(MagicMock session, ``patch.object`` on every ``job_service.*``
helper). That seam tests call counts. W13-13 needs to pin **row state
transitions** against a real PostgreSQL row, so we use the
``db_session`` fixture and route the internal ``job_service._run_in_session``
helper to the same session via a monkeypatch — fresh
``SessionLocal()`` callsites would land on a different connection
that cannot see the test fixture's outer transaction. ``execute_analysis_request``
is monkeypatched to a trap (cancel + terminal cases — must not fire)
or a stub (queued happy-path — returns an ``AnalyzeResponse``); no
worker thread is spawned because the race is encoded by the
pre-positioned row state.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy.orm import Session

from appcore.contracts.schema_defs.analysis_jobs import AnalysisJobUpdate
from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from appcore.storage.crud_ops.analysis_jobs import lifecycle
from tests.platform.storage.test_analysis_jobs_lifecycle import _snapshot
from workflows.marketplace import analysis_service, job_service

pytestmark = pytest.mark.requires_db


def _request() -> AnalyzeRequest:
    return AnalyzeRequest(
        publisher="ms-python",
        name="python",
        version="2026.5.0",
        scenario=None,
        analysis_profile=None,
    )


def _route_job_service_to(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Route every ``job_service._run_in_session(None, op)`` call to ``db_session``.

    Fresh ``SessionLocal()`` callsites used by ``job_service.get_job_snapshot``,
    ``update_job``, ``is_job_cancelled``, ``finalize_cancelled_job``,
    ``complete_job``, etc. open a brand-new connection that cannot
    observe the test fixture's outer ``connection.begin()`` transaction.
    The patch makes the ``db=None`` branch reuse the test session so
    pre-positioned row state stays visible across every helper hop.
    """

    def _patched(db: Session | None, operation: Callable[[Session], Any]) -> Any:
        return operation(db if db is not None else db_session)

    monkeypatch.setattr(job_service, "_run_in_session", _patched)


def _stub_executor_returning_success(request: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message="Stubbed analysis success.",
        install_output=None,
        automation_output=None,
        report_path="activation_report.json",
    )


def test_cancel_between_reserve_and_worker_entry_finalizes_without_running(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancel that lands AFTER ``reserve_job`` but BEFORE worker entry: row finalizes ``cancelled``.

    Reproduces the W13-13 race: queued row, user cancels (row -> cancelling),
    then the worker thread reaches ``run_analysis_job``. Pre-W13-13 the
    unconditional ``update_job(status="running")`` overwrites the cancel
    intent and the analysis runs to completion. Post-W13-13 (Path B)
    the worker takes a ``with_for_update()`` snapshot, observes
    ``cancelling``, calls ``finalize_cancelled_analysis_job(db, ...)``
    directly (NOT the wrapper — see test_run_analysis_job_entry_snapshot
    architecture gate for the deadlock-avoidance rationale) and returns
    before ``execute_analysis_request`` ever fires.

    RED pre-W13-13: the trap on ``execute_analysis_request`` raises
    ``AssertionError`` because the worker reaches the analysis flow.
    GREEN post-W13-13: the trap is never invoked; the row lands as
    ``cancelled`` with ``started_at`` still ``None`` (worker never
    wrote it).
    """
    _route_job_service_to(db_session, monkeypatch)

    snapshot = _snapshot(status="queued")
    lifecycle.create_analysis_job(db_session, snapshot)
    lifecycle.cancel_analysis_job(db_session, snapshot.job_id)

    def _trap(*args: Any, **kwargs: Any) -> AnalyzeResponse:
        raise AssertionError(
            "execute_analysis_request must NOT run after a cancel "
            "lands in the reserve-job -> worker-entry window."
        )

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _trap)
    monkeypatch.setattr(analysis_service, "_open_job_session", lambda: db_session)

    analysis_service.run_analysis_job(snapshot.job_id, _request())

    refetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert refetched is not None
    assert refetched.status == "cancelled"
    assert refetched.started_at is None
    assert refetched.finished_at is not None


def test_worker_observes_queued_and_runs(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Queued happy-path: worker promotes ``queued -> running`` and proceeds.

    GREEN sentinel pinning that the new entry-block lock did not
    regress the no-cancel path. The worker must still observe ``queued``,
    atomically transition to ``running`` under the lock, and invoke
    ``execute_analysis_request``. The downstream ``complete_job`` call
    then lands the row in ``completed``.
    """
    _route_job_service_to(db_session, monkeypatch)

    snapshot = _snapshot(status="queued")
    lifecycle.create_analysis_job(db_session, snapshot)

    observed_status_at_execute: list[str] = []

    def _stub(request: AnalyzeRequest, db: Session, **kwargs: Any) -> AnalyzeResponse:
        # By the time execute fires, the entry block must have
        # transitioned the row to ``running``.
        row = lifecycle.get_analysis_job(db, snapshot.job_id)
        assert row is not None
        observed_status_at_execute.append(row.status)
        return _stub_executor_returning_success(request)

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _stub)
    monkeypatch.setattr(analysis_service, "_open_job_session", lambda: db_session)

    analysis_service.run_analysis_job(snapshot.job_id, _request())

    assert observed_status_at_execute == ["running"]
    refetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert refetched is not None
    assert refetched.status == "completed"
    assert refetched.started_at is not None


def test_worker_observes_already_terminal_exits_silently(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Terminal short-circuit: worker that arrives on a ``completed`` row exits without mutating it.

    A worker can in principle reach ``run_analysis_job`` after the row
    has been driven terminal by an independent path (e.g. a stale boot
    sweep that landed mid-flight). Pre-W13-13 the unconditional
    ``update_job(status="running")`` would flip the terminal row back
    to ``running`` — a serious audit-trail regression. Post-W13-13 the
    entry-block ``with_for_update()`` reads the terminal status, logs,
    rolls back, and returns without ever calling ``update_job`` or
    ``execute_analysis_request``.

    RED pre-W13-13: the trap on ``execute_analysis_request`` raises;
    additionally the row's status may regress from ``completed`` back
    to ``running`` via the unconditional ``update_job`` write.
    GREEN post-W13-13: the trap is never invoked; the row's
    ``completed`` status and timestamps are untouched.
    """
    _route_job_service_to(db_session, monkeypatch)

    snapshot = _snapshot(status="queued")
    lifecycle.create_analysis_job(db_session, snapshot)
    lifecycle.complete_analysis_job(
        db_session,
        snapshot.job_id,
        AnalysisJobUpdate(message="Pre-positioned terminal."),
    )
    pre_state = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert pre_state is not None
    pre_finished_at = pre_state.finished_at

    def _trap(*args: Any, **kwargs: Any) -> AnalyzeResponse:
        raise AssertionError("execute_analysis_request must NOT run on a terminal row.")

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _trap)
    monkeypatch.setattr(analysis_service, "_open_job_session", lambda: db_session)

    analysis_service.run_analysis_job(snapshot.job_id, _request())

    refetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert refetched is not None
    assert refetched.status == "completed"
    assert refetched.finished_at == pre_finished_at


# ----------------------------------------------------------------------
# W13-13 post-landing behavioral pins (mirror W13-12 0d3e343 precedent).
#
# The 3 RED→GREEN cases above pin the primary cancel-race seam. These
# additional pins close defense-in-depth gaps the architecture gate
# can't directly express:
#
#   (a) Vanished-row branch — the defensive ``if job is None`` early
#       return has no behavioral coverage. A row could vanish between
#       reserve_job and worker entry via test-fixture cleanup or an
#       aggressive stale-boot sweep racing the worker.
#   (b) Idempotent finalize race — the entry-block ``cancelling``
#       branch wraps ``finalize_cancelled_analysis_job`` in
#       ``except (JobNotCancellableError, KeyError)``. If another
#       writer drives the row terminal between the SELECT...FOR UPDATE
#       and the finalize call, the worker must still exit cleanly.
#   (c) ``failed`` terminal short-circuit — only ``completed`` is
#       tested above; the other 2 terminal states (``failed``,
#       ``cancelled``) share the same code path but are not pinned.
#   (d) ``cancelled`` terminal short-circuit — same rationale as (c).
# ----------------------------------------------------------------------


def test_worker_handles_vanished_row_at_worker_entry(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Vanished-row branch (a): worker that arrives on a missing row must exit cleanly.

    The Path B entry block has a defensive ``if job is None`` branch
    that logs a warning and returns. The architecture gate cannot
    distinguish this from the terminal short-circuit at AST level; the
    behavioral test pins that an entirely-missing ``job_id`` does not
    propagate ``KeyError`` out of the worker thread (which would crash
    the daemon thread silently in production).
    """
    _route_job_service_to(db_session, monkeypatch)

    def _trap(*args: Any, **kwargs: Any) -> AnalyzeResponse:
        raise AssertionError(
            "execute_analysis_request must NOT run when the job row is missing."
        )

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _trap)
    monkeypatch.setattr(analysis_service, "_open_job_session", lambda: db_session)

    # No row was ever created — the entry block's SELECT returns None.
    analysis_service.run_analysis_job("does-not-exist-uuid", _request())

    # Sentinel: the function returned cleanly (no exception bubbled up,
    # no scan ran). The row stays absent.
    assert lifecycle.get_analysis_job(db_session, "does-not-exist-uuid") is None


def test_worker_entry_finalize_idempotent_when_race_lands_terminal(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Idempotent finalize race (b): JobNotCancellableError in entry-block cancelling branch is swallowed.

    Models the race where another writer (e.g. a stale-boot sweep or a
    second worker spawn) drives the row terminal AFTER the entry-block
    SELECT...FOR UPDATE observes ``cancelling`` but BEFORE
    ``finalize_cancelled_analysis_job`` commits the
    ``cancelling -> cancelled`` transition. The lifecycle helper would
    raise ``JobNotCancellableError`` against the (now-terminal) row;
    the entry block's ``except (JobNotCancellableError, KeyError)``
    must catch it and exit cleanly. Without this defensive wrap, the
    worker thread crashes with an uncaught exception (silent daemon
    failure in production).
    """
    _route_job_service_to(db_session, monkeypatch)

    snapshot = _snapshot(status="queued")
    lifecycle.create_analysis_job(db_session, snapshot)
    lifecycle.cancel_analysis_job(db_session, snapshot.job_id)

    def _trap(*args: Any, **kwargs: Any) -> AnalyzeResponse:
        raise AssertionError(
            "execute_analysis_request must NOT run on the cancelling branch."
        )

    # Simulate the race: the entry block's SELECT sees ``cancelling``,
    # then the lifecycle helper raises JobNotCancellableError because a
    # concurrent writer drove the row terminal under the lock.
    def _finalize_raises_terminal(*args: Any, **kwargs: Any) -> Any:
        raise lifecycle.JobNotCancellableError(snapshot.job_id, "cancelled")

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _trap)
    monkeypatch.setattr(analysis_service, "_open_job_session", lambda: db_session)
    # W16-2: ``finalize_cancelled_analysis_job`` no longer lives on
    # ``analysis_service`` (the W16-2 facade refactor moved the call
    # site into the lifecycle CRUD primitive
    # ``claim_queued_analysis_job_at_worker_entry``). Patch the lifecycle
    # module directly — the claim helper resolves the bare name through
    # its own module scope, so the monkeypatch is observed there.
    monkeypatch.setattr(
        lifecycle,
        "finalize_cancelled_analysis_job",
        _finalize_raises_terminal,
    )

    # Must NOT propagate JobNotCancellableError; entry block's
    # defensive except clause swallows it.
    analysis_service.run_analysis_job(snapshot.job_id, _request())

    # The row is still ``cancelling`` (the helper raised before
    # committing the terminal transition); but the worker exited
    # without running the scan — correct behavior under the race.
    refetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert refetched is not None
    assert refetched.status == "cancelling"


@pytest.mark.parametrize(
    "terminal_driver,expected_status",
    [
        pytest.param("fail", "failed", id="failed"),
        pytest.param("cancel_then_finalize", "cancelled", id="cancelled"),
    ],
)
def test_worker_terminal_short_circuit_covers_all_terminal_statuses(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    terminal_driver: str,
    expected_status: str,
) -> None:
    """Terminal short-circuit (c) + (d): worker exits silently for ``failed`` + ``cancelled``.

    The ``completed`` variant is pinned above. Parametrizes the other
    two members of ``_TERMINAL_JOB_STATUSES`` so all three terminal
    states are behaviorally covered. ``failed`` is reached via
    ``lifecycle.fail_analysis_job``; ``cancelled`` via the W13-3
    two-phase ``cancel_analysis_job -> finalize_cancelled_analysis_job``
    chain. Both must short-circuit the worker without invoking
    ``execute_analysis_request`` and without mutating the row.
    """
    _route_job_service_to(db_session, monkeypatch)

    from appcore.contracts.schema_defs.analysis_jobs import AnalysisJobFailure

    snapshot = _snapshot(status="queued")
    lifecycle.create_analysis_job(db_session, snapshot)

    if terminal_driver == "fail":
        lifecycle.fail_analysis_job(
            db_session,
            snapshot.job_id,
            AnalysisJobFailure(detail="boom", error_code="install_failed"),
        )
    elif terminal_driver == "cancel_then_finalize":
        lifecycle.cancel_analysis_job(db_session, snapshot.job_id)
        lifecycle.finalize_cancelled_analysis_job(db_session, snapshot.job_id)

    pre_state = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert pre_state is not None
    assert pre_state.status == expected_status
    pre_finished_at = pre_state.finished_at

    def _trap(*args: Any, **kwargs: Any) -> AnalyzeResponse:
        raise AssertionError(
            f"execute_analysis_request must NOT run on a {expected_status} row."
        )

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _trap)
    monkeypatch.setattr(analysis_service, "_open_job_session", lambda: db_session)

    analysis_service.run_analysis_job(snapshot.job_id, _request())

    refetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert refetched is not None
    assert refetched.status == expected_status
    assert refetched.finished_at == pre_finished_at
