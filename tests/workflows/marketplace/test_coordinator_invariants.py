"""W18-2 (heartbeat refactor) post-close-out invariant pins.

ADR 0012 Option A1 introduced a dedicated sandbox-reset coordinator thread
for the step-1 setup reset (``_run_reset_off_thread`` in
``workflows.marketplace.analysis_execution``). The lifecycle harness tests
at ``tests/workflows/marketplace/test_lifecycle_harness.py`` cover
parallel reset, idempotency, and the post-finalize barrier. These tests
close four narrower gaps that fall outside the harness scope:

* ``cancel_check`` kwarg default-``None`` signature pin — W18-2 picked
  the function-extension shape over a class-based coordinator
  precisely so the 6 ``patch.object(analysis_execution, "reset_sandbox")``
  call sites in ``test_analysis_execution_poll_points.py`` keep
  working without passing the new kwarg. If a future refactor makes
  ``cancel_check`` required, those patch sites would TypeError at
  runtime and produce false-green W13-3 cancel coverage.
* ``_COORDINATOR_POLL_INTERVAL_S ≤ 0.1`` constant pin — the W13-3
  cancel-cadence invariant ADR 0012 §Sub-decisions commits to. A
  silent regression to 1.0s would weaken cancel responsiveness
  without breaking any other test.
* Cancel-propagation-within-poll-interval behavioral pin — same
  invariant exercised on the ``_run_reset_off_thread`` wait loop with
  a blocking ``executor_control.reset_sandbox``; asserts elapsed
  time before ``AnalysisCancelledError`` raises stays ≤ 0.5s
  (one poll interval + generous CI slack).
* Reporter-emit thread-isolation pin — W18-2 risk disposition: the
  spawned coordinator thread runs ONLY ``executor_control.reset_sandbox()``,
  never any ``reporter.emit(...)``. Exercises both the success and
  ``ExecutorError`` failure paths.
"""

from __future__ import annotations

import inspect
import threading
import time
from unittest.mock import MagicMock

import pytest

from executor.control import ExecutorError
from workflows.marketplace.analysis_errors import AnalysisCancelledError
from workflows.marketplace.analysis_execution import (
    _COORDINATOR_POLL_INTERVAL_S,
    _run_reset_off_thread,
    reset_sandbox,
)


def test_reset_sandbox_signature_keeps_cancel_check_default_none() -> None:
    """Public ``reset_sandbox`` must keep ``cancel_check`` defaultable to ``None``.

    W18-2 deliberately picked the function-extension shape over a
    class-based ``SandboxResetCoordinator``. Six
    ``patch.object(analysis_execution, "reset_sandbox")`` call sites in
    ``test_analysis_execution_poll_points.py`` rely on the default —
    they call the patched stub without passing ``cancel_check``. If a
    future refactor makes the kwarg required, the patched stubs would
    TypeError at runtime instead of behaving as a no-op, producing a
    false-green regression for W13-3 cancel coverage.
    """
    sig = inspect.signature(reset_sandbox)
    param = sig.parameters.get("cancel_check")
    assert param is not None, (
        "reset_sandbox must expose a `cancel_check` parameter; got "
        f"parameters={list(sig.parameters)}."
    )
    assert param.default is None, (
        "reset_sandbox.cancel_check must default to None — preserves "
        "backwards-compat with patch.object(analysis_execution, "
        "'reset_sandbox') call sites in test_analysis_execution_poll_points.py. "
        f"Got default={param.default!r}."
    )


def test_coordinator_poll_interval_honors_cancel_cadence_bound() -> None:
    """``_COORDINATOR_POLL_INTERVAL_S`` must be ≤ 0.1s.

    ADR 0012 §Sub-decisions commits the coordinator wait loop to honor
    W13-3 cancel cadence (boundary ≤ 100ms). A silent regression of
    this constant to 1.0s would weaken cancel responsiveness without
    breaking any other test — this single-line gate prevents that.
    """
    assert _COORDINATOR_POLL_INTERVAL_S <= 0.1, (
        "_COORDINATOR_POLL_INTERVAL_S must be ≤ 0.1s per W13-3 cancel "
        "cadence (ADR 0012 §Sub-decisions); got "
        f"{_COORDINATOR_POLL_INTERVAL_S}."
    )


def test_run_reset_off_thread_propagates_cancel_within_one_poll_interval() -> None:
    """Mid-reset cancel raises ``AnalysisCancelledError`` within ~0.5s.

    Wires a blocking ``executor_control.reset_sandbox`` (parked on an
    ``Event``) and a ``cancel_check`` that returns ``True`` from the
    start. The main frame in ``_run_reset_off_thread`` runs::

        while not done.wait(timeout=_COORDINATOR_POLL_INTERVAL_S):
            raise_if_cancelled(cancel_check)

    The first ``done.wait`` returns ``False`` (timeout — the spawned
    thread is parked), then ``raise_if_cancelled`` fires
    ``AnalysisCancelledError``.

    Pin: elapsed time ≤ 0.5s (~5x the poll interval + CI slack). If a
    future refactor swaps the wait loop for a bare ``thread.join()`` or
    drops the ``raise_if_cancelled`` poll, the timer blows past this
    bound.
    """
    executor_control = MagicMock()
    release = threading.Event()

    def _park_until_release() -> None:
        # Parks the spawned coordinator thread so the main wait loop
        # must time out and check cancel_check at least once.
        release.wait(timeout=5.0)

    executor_control.reset_sandbox.side_effect = _park_until_release

    started_at = time.monotonic()
    try:
        with pytest.raises(AnalysisCancelledError):
            _run_reset_off_thread(executor_control, lambda: True)
    finally:
        # daemon=True coordinator thread is OK to leak on process
        # exit, but explicit release keeps the suite tidy.
        release.set()
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.5, (
        f"Cancel propagation took {elapsed:.3f}s — should be ≤ one "
        "poll interval + slack (≤ 0.5s) per ADR 0012 §Sub-decisions. "
        "Suspect: wait loop replaced by bare join, or raise_if_cancelled "
        "bypassed."
    )


def test_reset_sandbox_reporter_emits_stay_in_caller_thread() -> None:
    """``reporter.emit`` must originate from the caller frame on both paths.

    W18-2 risk disposition (recorded in
    ``documents/active-work/W18-heartbeat-refactor.md`` §W18-2):
    "Reporter cross-thread emit — StepReporter.emit calls stay in the
    worker frame; ``_run_reset_off_thread`` runs the executor call only.
    No emit-thread-context drift."

    Records the thread name of every ``reporter.emit`` call across the
    success path (emit ``running`` + ``completed``) and the
    ``ExecutorError`` failure path (emit ``running`` + ``failed`` then
    re-raise). Asserts all emits originate from the caller thread, not
    from a coordinator thread. If a future refactor moved a
    ``reporter.emit`` call inside the coordinator's ``_target`` closure,
    this gate catches the thread-context drift.
    """
    caller_thread = threading.current_thread().name

    # Success path: emit("running") + emit("completed").
    reporter_ok = MagicMock()
    emit_threads_ok: list[str] = []

    def _record_ok(*_args: object, **_kwargs: object) -> None:
        emit_threads_ok.append(threading.current_thread().name)

    reporter_ok.emit.side_effect = _record_ok

    executor_ok = MagicMock()
    reset_sandbox(reporter_ok, executor_ok, cancel_check=None)

    assert reporter_ok.emit.call_count == 2, (
        "Success path: reset_sandbox emits 'running' + 'completed'."
    )
    assert all(t == caller_thread for t in emit_threads_ok), (
        f"reporter.emit must stay in caller thread {caller_thread!r}; "
        f"got success-path threads: {emit_threads_ok}."
    )

    # Failure path: emit("running") + emit("failed").
    reporter_err = MagicMock()
    emit_threads_err: list[str] = []

    def _record_err(*_args: object, **_kwargs: object) -> None:
        emit_threads_err.append(threading.current_thread().name)

    reporter_err.emit.side_effect = _record_err

    executor_err = MagicMock()
    executor_err.reset_sandbox.side_effect = ExecutorError("simulated reset failure")

    with pytest.raises(ExecutorError):
        reset_sandbox(reporter_err, executor_err, cancel_check=None)

    assert reporter_err.emit.call_count == 2, (
        "Failure path: reset_sandbox emits 'running' + 'failed' then re-raises."
    )
    assert all(t == caller_thread for t in emit_threads_err), (
        f"reporter.emit must stay in caller thread {caller_thread!r}; "
        f"got failure-path threads: {emit_threads_err}."
    )
