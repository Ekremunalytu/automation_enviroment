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


def _route_job_service_to(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Route every ``job_service._run_in_session(None, op)`` call to ``db_session``.

    Fresh ``SessionLocal()`` callsites used by ``job_service.get_job_snapshot``,
    ``update_job``, ``is_job_cancelled``, ``finalize_cancelled_job``,
    ``complete_job``, etc. open a brand-new connection that cannot
    observe the test fixture's outer ``connection.begin()`` transaction.
    The patch makes the ``db=None`` branch reuse the test session so
    pre-positioned row state stays visible across every helper hop.
    """

    def _patched(
        db: Session | None, operation: Callable[[Session], Any]
    ) -> Any:
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
    monkeypatch.setattr(
        analysis_service, "_open_job_session", lambda: db_session
    )

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
    monkeypatch.setattr(
        analysis_service, "_open_job_session", lambda: db_session
    )

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
        raise AssertionError(
            "execute_analysis_request must NOT run on a terminal row."
        )

    monkeypatch.setattr(analysis_service, "execute_analysis_request", _trap)
    monkeypatch.setattr(
        analysis_service, "_open_job_session", lambda: db_session
    )

    analysis_service.run_analysis_job(snapshot.job_id, _request())

    refetched = lifecycle.get_analysis_job(db_session, snapshot.job_id)
    assert refetched is not None
    assert refetched.status == "completed"
    assert refetched.finished_at == pre_finished_at
