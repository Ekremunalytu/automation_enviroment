"""W13-4 (cancellation lifecycle hardening): behavioral coverage for the
6 W13-3 + W13-11 cancel-poll points in ``execute_analysis_request``.

W13-3 landed `tests/architecture/test_cancel_poll_points.py::test_every_major_phase_is_preceded_by_a_cancel_poll`
which AST-walks ``execute_analysis_request`` body and asserts every
hot-zone helper (``ensure_vsix_exists``, ``_reset_sandbox``,
``executor_control.consume_harness_python_secret`` (W13-11),
``_install_extension``, ``_build_triggers``, ``_run_monitoring``) is
immediately preceded by a ``_raise_if_cancelled(cancel_check)`` call.
That gate catches refactor regression but not behavior: it cannot prove
the helper actually raises ``AnalysisCancelledError`` when the lambda
returns True, nor that the worker stops calling subsequent phases.

These tests close that gap. Each test wires ``cancel_check`` so it
returns ``True`` exactly at the boundary under test and asserts:

1. ``execute_analysis_request`` raises ``AnalysisCancelledError``.
2. The hot-zone helper *immediately following* the firing poll point
   was never invoked (regression guard for AST-gate refactor that
   reorders phases or swaps poll positions).

W13-4.2 lands these as ``@pytest.mark.skip`` RED precursors so the
suite still passes; W13-4.3 removes the skip decorators (no production
code change needed — W13-3 already wired the helpers correctly, this
sub-commit just proves it).
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from appcore.contracts.schemas import AnalyzeRequest
from workflows.marketplace import analysis_service
from workflows.marketplace.analysis_errors import AnalysisCancelledError
from workflows.marketplace.trigger_service import TriggerPlan


def _request() -> AnalyzeRequest:
    return AnalyzeRequest(
        publisher="ms-python",
        name="python",
        version="2026.5.0",
        scenario=None,
        analysis_profile=None,
    )


def _cancel_after_n_false_returns(n: int) -> Callable[[], bool]:
    """Return a ``cancel_check`` callable: ``False`` ``n`` times, then ``True``.

    The W13-3 + W13-11 wiring calls ``cancel_check`` once per poll point
    in ``execute_analysis_request``. ``n=0`` fires at poll point #1
    (before ``ensure_vsix_exists``); ``n=1`` fires at poll point #2
    (before ``_reset_sandbox``); ``n=2`` fires at poll point #3 (before
    ``executor_control.consume_harness_python_secret``, added by W13-11);
    ``n=3`` fires at poll point #4 (before ``_install_extension``); and
    so on through ``n=5`` which fires at poll point #6 (between
    ``_build_triggers`` and ``_run_monitoring``).
    """
    sequence = iter([False] * n + [True] * 50)

    def cancel_check() -> bool:
        return next(sequence)

    return cancel_check


def _make_trigger_plan() -> TriggerPlan:
    """Minimal TriggerPlan satisfying ``execute_analysis_request`` consumers."""
    return TriggerPlan(
        trigger_container_path=None,
        selected_scenarios=[],
        skip_automation=True,
        reason_code="test_no_op_plan",
        message="test trigger plan",
    )


def test_raises_on_cancel_before_ensure_vsix_exists() -> None:
    """Poll point #1: cancel signal observed *before* ``ensure_vsix_exists``."""
    cancel_check = _cancel_after_n_false_returns(0)

    with (
        patch.object(analysis_service, "ensure_vsix_exists") as ensure,
        patch.object(analysis_service, "_reset_sandbox") as reset,
        patch.object(analysis_service, "_install_extension") as install,
        patch.object(analysis_service, "_build_triggers") as build,
        patch.object(analysis_service, "_run_monitoring") as monitor,
        pytest.raises(AnalysisCancelledError),
    ):
        analysis_service.execute_analysis_request(
            _request(),
            MagicMock(),
            cancel_check=cancel_check,
        )

    # Poll point #1 fires BEFORE ensure_vsix_exists; nothing downstream runs.
    ensure.assert_not_called()
    reset.assert_not_called()
    install.assert_not_called()
    build.assert_not_called()
    monitor.assert_not_called()


def test_raises_on_cancel_before_reset_sandbox() -> None:
    """Poll point #2: ``ensure_vsix_exists`` runs, then cancel before ``_reset_sandbox``."""
    cancel_check = _cancel_after_n_false_returns(1)

    with (
        patch.object(analysis_service, "ensure_vsix_exists") as ensure,
        patch.object(analysis_service, "_reset_sandbox") as reset,
        patch.object(analysis_service, "_install_extension") as install,
        patch.object(analysis_service, "_build_triggers") as build,
        patch.object(analysis_service, "_run_monitoring") as monitor,
        pytest.raises(AnalysisCancelledError),
    ):
        analysis_service.execute_analysis_request(
            _request(),
            MagicMock(),
            cancel_check=cancel_check,
        )

    ensure.assert_called_once()
    reset.assert_not_called()
    install.assert_not_called()
    build.assert_not_called()
    monitor.assert_not_called()


def test_raises_on_cancel_before_consume_harness_python_secret() -> None:
    """Poll point #3 (W13-11): ensure + reset run, then cancel before
    ``executor_control.consume_harness_python_secret``."""
    cancel_check = _cancel_after_n_false_returns(2)
    executor_control = MagicMock()

    with (
        patch.object(analysis_service, "ensure_vsix_exists") as ensure,
        patch.object(analysis_service, "_reset_sandbox") as reset,
        patch.object(analysis_service, "_install_extension") as install,
        patch.object(analysis_service, "_build_triggers") as build,
        patch.object(analysis_service, "_run_monitoring") as monitor,
        pytest.raises(AnalysisCancelledError),
    ):
        analysis_service.execute_analysis_request(
            _request(),
            executor_control,
            cancel_check=cancel_check,
        )

    ensure.assert_called_once()
    reset.assert_called_once()
    executor_control.consume_harness_python_secret.assert_not_called()
    install.assert_not_called()
    build.assert_not_called()
    monitor.assert_not_called()


def test_raises_on_cancel_before_install_extension() -> None:
    """Poll point #4: ensure + reset + consume run, then cancel before ``_install_extension``."""
    cancel_check = _cancel_after_n_false_returns(3)

    with (
        patch.object(analysis_service, "ensure_vsix_exists") as ensure,
        patch.object(analysis_service, "_reset_sandbox") as reset,
        patch.object(analysis_service, "_install_extension") as install,
        patch.object(analysis_service, "_build_triggers") as build,
        patch.object(analysis_service, "_run_monitoring") as monitor,
        pytest.raises(AnalysisCancelledError),
    ):
        analysis_service.execute_analysis_request(
            _request(),
            MagicMock(),
            cancel_check=cancel_check,
        )

    ensure.assert_called_once()
    reset.assert_called_once()
    install.assert_not_called()
    build.assert_not_called()
    monitor.assert_not_called()


def test_raises_on_cancel_before_build_triggers() -> None:
    """Poll point #5: ensure + reset + consume + install run, then cancel before ``_build_triggers``."""
    cancel_check = _cancel_after_n_false_returns(4)

    with (
        patch.object(analysis_service, "ensure_vsix_exists") as ensure,
        patch.object(analysis_service, "_reset_sandbox") as reset,
        patch.object(
            analysis_service, "_install_extension", return_value="install ok"
        ) as install,
        patch.object(analysis_service, "_build_triggers") as build,
        patch.object(analysis_service, "_run_monitoring") as monitor,
        pytest.raises(AnalysisCancelledError),
    ):
        analysis_service.execute_analysis_request(
            _request(),
            MagicMock(),
            cancel_check=cancel_check,
        )

    ensure.assert_called_once()
    reset.assert_called_once()
    install.assert_called_once()
    build.assert_not_called()
    monitor.assert_not_called()


def test_raises_on_cancel_before_run_monitoring() -> None:
    """Poll point #6: 5 phases run, then cancel before ``_run_monitoring``."""
    cancel_check = _cancel_after_n_false_returns(5)

    with (
        patch.object(analysis_service, "ensure_vsix_exists") as ensure,
        patch.object(analysis_service, "_reset_sandbox") as reset,
        patch.object(
            analysis_service, "_install_extension", return_value="install ok"
        ) as install,
        patch.object(
            analysis_service,
            "_build_triggers",
            return_value=_make_trigger_plan(),
        ) as build,
        patch.object(analysis_service, "_run_monitoring") as monitor,
        # build_report_name is called between poll #4 and poll #5 to derive
        # report_name when caller didn't pass one; deterministic UUID stub
        # keeps the test from depending on global RNG state.
        patch.object(analysis_service, "uuid4", return_value=uuid4()),
        pytest.raises(AnalysisCancelledError),
    ):
        analysis_service.execute_analysis_request(
            _request(),
            MagicMock(),
            cancel_check=cancel_check,
        )

    ensure.assert_called_once()
    reset.assert_called_once()
    install.assert_called_once()
    build.assert_called_once()
    monitor.assert_not_called()
