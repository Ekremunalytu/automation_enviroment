"""Tests for analysis-execution helpers — execute_analysis_request + run_analysis_job + map_executor_error.

Split from tests/workflows/marketplace/test_router.py during W16-6 to reduce single-file size.
These tests exercise analysis_service module functions directly (no FastAPI TestClient).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from executor.host import ExecutorError
from workflows.marketplace import (
    analysis_service,
    router as marketplace_router,
    trigger_service,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ANALYZE_PAYLOAD = {
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
}


@pytest.fixture(autouse=True)
def _static_gate_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate the dynamic pipeline from the ES-5 static pre-check gate.

    These tests drive ``execute_analysis_request`` for real with only the
    executor mocked; they assert dynamic-stage behavior (reset / install /
    trigger / monitoring + cancel-poll points) that predates the static stage.
    The static gate is ON by default from ES-5 and would fire a real
    ``docker exec`` into ``automation_static_analyzer`` here. Pin it OFF so the
    dynamic path is tested in isolation — the gate has its own coverage in
    ``test_static_gate_stage.py`` / ``test_static_analysis_pipeline.py`` and the
    Docker smoke lane.
    """
    monkeypatch.setattr(analysis_service.settings.static_analysis, "ENABLED", False)


@pytest.fixture(autouse=True)
def _inert_job_heartbeat(monkeypatch: pytest.MonkeyPatch) -> None:
    """S2 (W23 B3): keep ``run_analysis_job``'s DB heartbeat thread inert.

    These worker tests mock the job session via ``_open_job_session`` but the
    heartbeat thread opens its own ``SessionLocal`` (sessions are not
    thread-safe). No-op it so the DB-free worker tests never touch a real DB.
    The heartbeat loop itself is covered in ``test_stale_job_reaper.py``.
    """
    monkeypatch.setattr(
        "workflows.marketplace.job_service.run_job_heartbeat",
        lambda *args, **kwargs: None,
    )


def _make_trigger_plan(
    *,
    trigger_container_path: str | None = "/results/triggers.json",
    selected_scenarios: list[str] | None = None,
    skip_automation: bool = False,
    reason_code: str = "generated_trigger_plan",
    message: str = "Trigger plan ready.",
) -> trigger_service.TriggerPlan:
    return trigger_service.TriggerPlan(
        trigger_container_path=trigger_container_path,
        selected_scenarios=selected_scenarios or [],
        skip_automation=skip_automation,
        reason_code=reason_code,
        message=message,
    )


def _make_executor_control(
    *,
    reset_sandbox: object = "Sandbox reset.",
    install_extension: object = "Extension installed successfully.",
    run_automation: object = "Automation completed.",
) -> MagicMock:
    control = MagicMock(spec=analysis_service.ExecutorControl)
    control.reset_sandbox.side_effect = (
        reset_sandbox if isinstance(reset_sandbox, Exception) else None
    )
    control.install_extension.side_effect = (
        install_extension if isinstance(install_extension, Exception) else None
    )
    control.run_automation.side_effect = (
        run_automation if isinstance(run_automation, Exception) else None
    )

    if not isinstance(reset_sandbox, Exception):
        control.reset_sandbox.return_value = str(reset_sandbox)
    if not isinstance(install_extension, Exception):
        control.install_extension.return_value = str(install_extension)
    if not isinstance(run_automation, Exception):
        control.run_automation.return_value = str(run_automation)
    return control


# ---------------------------------------------------------------------------
# Execute Analysis Request + Run Analysis Job + Map Executor Error Tests
# ---------------------------------------------------------------------------


def test_execute_analysis_request_fails_closed_when_trigger_build_fails() -> None:
    """Trigger payload failures should abort analysis before sandbox automation starts."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            side_effect=ValueError("bad trigger"),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name="activation_report.json",
            executor_control=executor_control,
        )

    assert exc_info.value.error_code == "trigger_build_failed"
    assert progress_events[-1] == (
        "build_triggers",
        "failed",
        "Trigger payload build failed before sandbox automation started.",
        "trigger_build_failed",
    )
    executor_control.run_automation.assert_not_called()


def test_execute_analysis_request_reports_reset_failure() -> None:
    """Reset failures should be reported on the reset step before bubbling up."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control(
        reset_sandbox=ExecutorError("reset failed", returncode=1, output="boom")
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            executor_control=executor_control,
        )

    assert progress_events[-1] == (
        "reset_sandbox",
        "failed",
        "Sandbox reset failed before extension installation.",
        None,
    )


def test_execute_analysis_request_reports_automation_failure() -> None:
    """Automation failures should mark the monitoring step as failed."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control(
        run_automation=ExecutorError("automation failed", returncode=1, output="boom")
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["scenario"],
                message="selected",
            ),
        ),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            executor_control=executor_control,
        )

    assert progress_events[-1] == (
        "run_monitoring",
        "failed",
        (
            "Sandbox automation failed before the report could be finalized: "
            "automation failed"
        ),
        None,
    )


def test_execute_analysis_request_reports_healthful_monitoring_summary(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "healthy",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 1,
            "failed_scenarios": ["coding_session"]
          },
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "completed"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": ["workspace_bootstrap"]}
          ],
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "layered_passes"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert response.status == "success"
    assert any(
        step == "run_monitoring"
        and "trigger requested=true, loaded=true, applied=true" in message.lower()
        for step, _, message, _ in progress_events
    )
    assert any(
        step == "finalize_report"
        and "health=healthy" in message.lower()
        and "failed scenarios=1" in message.lower()
        for step, _, message, _ in progress_events
    )


def test_execute_analysis_request_rejects_legacy_trigger_plan_tuple(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "healthy",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 1,
            "failed_scenarios": []
          },
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "completed"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": ["workspace_bootstrap"]}
          ],
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "layered_passes"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=(
                "/results/triggers.json",
                ["coding_session"],
                "legacy trigger payload",
            ),
        ),
    ):
        with pytest.raises(
            TypeError, match="build_trigger_payload must return TriggerPlan"
        ):
            analysis_service.execute_analysis_request(
                request,
                db=MagicMock(),
                report_name=report_name,
                executor_control=executor_control,
            )


def test_execute_analysis_request_falls_back_to_selected_scenario_when_legacy_trigger_file_is_missing(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "single_scenario",
          "automation_health": {
            "status": "inconclusive",
            "trigger_requested": true,
            "trigger_loaded": false,
            "trigger_applied": false,
            "target_activation_count": 0,
            "failed_scenarios": []
          },
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "single_scenario"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                trigger_container_path="/results/missing-trigger-payload.json",
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert response.status == "success"
    assert (
        executor_control.run_automation.call_args.kwargs["scenario"] == "coding_session"
    )
    assert (
        executor_control.run_automation.call_args.kwargs["trigger_container_path"]
        == "/results/missing-trigger-payload.json"
    )


@pytest.mark.parametrize("status", ["degraded", "inconclusive"])
def test_build_report_messages_include_extra_trigger_failures(
    status: str,
) -> None:
    monitoring_message, finalize_message = analysis_service._build_report_messages(
        "activation_report.json",
        payload={
            "automation_health": {
                "status": status,
                "trigger_requested": True,
                "trigger_loaded": True,
                "trigger_applied": False,
                "target_activation_count": 0,
                "failed_scenarios": ["coding_session"],
            },
            "summary": {
                "scenarios_run": ["coding_session"],
            },
            "extra_trigger_failures": ["uri_trigger", "command:Extension: Fail"],
        },
    )

    assert f"{status} health" in monitoring_message.lower()
    assert "extra trigger failures=2" in monitoring_message.lower()
    assert "failed scenarios=1" in finalize_message.lower()
    assert "extra trigger failures=2" in finalize_message.lower()


def test_execute_analysis_request_reports_degraded_monitoring_summary(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "degraded",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 1,
            "failed_scenarios": ["coding_session"],
            "extra_trigger_failures": ["uri_trigger", "command:Extension: Fail"],
            "extra_trigger_failure_count": 2
          },
          "extra_trigger_failures": [
            "uri_trigger",
            "command:Extension: Fail"
          ],
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "completed"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": ["workspace_bootstrap"]}
          ],
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "layered_passes"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert response.status == "success"
    assert "extra trigger failures=2" in response.message.lower()
    assert any(
        step == "run_monitoring"
        and "degraded health" in message.lower()
        and "extra trigger failures=2" in message.lower()
        for step, _, message, _ in progress_events
    )
    assert any(
        step == "finalize_report"
        and "failed scenarios=1" in message.lower()
        and "extra trigger failures=2" in message.lower()
        for step, _, message, _ in progress_events
    )


def test_execute_analysis_request_fails_when_trigger_report_cannot_load(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    (tmp_path / "triggers.json").write_text("{}", encoding="utf-8")

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name="missing_report.json",
            executor_control=executor_control,
        )

    assert exc_info.value.error_code == "trigger_load_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][1] == "failed"
    assert progress_events[-1][3] == "trigger_load_failed"


def test_execute_analysis_request_fails_when_trigger_plan_not_applied(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    (tmp_path / "triggers.json").write_text("{}", encoding="utf-8")
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "selected_scenarios",
          "automation_health": {
            "status": "inconclusive",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": false,
            "target_activation_count": 0,
            "failed_scenarios": []
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert exc_info.value.error_code == "trigger_apply_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][3] == "trigger_apply_failed"


def test_execute_analysis_request_fails_when_layered_evidence_is_missing(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    (tmp_path / "triggers.json").write_text("{}", encoding="utf-8")
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "degraded",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 0,
            "failed_scenarios": []
          },
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "planned"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": []}
          ]
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert exc_info.value.error_code == "trigger_apply_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][3] == "trigger_apply_failed"


# ---------------------------------------------------------------------------
# W13-11 defense-in-depth (b): orchestration-level runtime invariant.
#
# The AST/sequence architecture gate
# (``tests/architecture/test_harness_secret_eager_consume.py::
#  test_execute_analysis_request_consumes_secret_before_install``) pins the
# call order ``_reset_sandbox -> consume_harness_python_secret ->
# _install_extension`` at parse time. The behavioral unit test
# (``tests/executor/test_harness_secret_eager_consume.py::
#  test_eager_consume_returns_secret_and_unlinks_file``) pins the helper's
# unlink side effect on the bind-mounted path. This orchestration test ties
# the two together at runtime: when the real ``consume_harness_python_secret_eager``
# helper is wired through ``ExecutorControl.consume_harness_python_secret``
# and ``execute_analysis_request`` runs end-to-end, the bind-mount secret
# file must be absent at the instant ``executor_control.install_extension``
# is invoked. Without this guarantee the same-UID target VSIX would see a
# readable secret file during its activation window — the W13-11 close-pass
# F1 surface.
# ---------------------------------------------------------------------------


def test_execute_analysis_request_unlinks_secret_before_install(
    tmp_path: Path,
) -> None:
    """W13-11 (b) defense-in-depth — runtime invariant.

    ``execute_analysis_request`` must call ``executor_control.consume_harness_python_secret``
    (which goes through the real ``consume_harness_python_secret_eager``
    helper) BEFORE ``executor_control.install_extension`` is invoked, and
    the helper's unlink side effect must have completed by then. This pins
    the contract at orchestration runtime, complementing the AST sequence
    gate and the unit-level unlink behavioral case.
    """
    from executor import host as host_module

    request = AnalyzeRequest(**ANALYZE_PAYLOAD)

    # Pre-populate the bind-mount file at the chmod the producer
    # (``launch_vscode.sh:51``) writes. The real eager-consume helper
    # honors the mode guard and will unlink on success.
    secret_value = "deadbeefcafe9999" * 4  # 64 chars hex.
    secret_path = tmp_path / "_extrace_harness_python_secret"
    secret_path.write_text(secret_value, encoding="utf-8")
    secret_path.chmod(0o600)

    captured_state: dict[str, object] = {}

    def real_consume() -> str | None:
        # Route the production helper through the test tmp_path rather than
        # the default ``settings.project.OUTPUT_DIR`` resolution so the
        # test does not depend on a writable bind-mount target.
        return host_module.consume_harness_python_secret_eager(host_path=secret_path)

    def install_capture(publisher: str, name: str, version: str) -> str:
        # Sample bind-mount file state at the precise moment the orchestration
        # admits the analyzed VSIX. Pre-W13-11 this would see the secret file
        # present (race window open). Post-W13-11 the eager-consume above
        # must have unlinked it.
        captured_state["secret_present_at_install"] = secret_path.exists()
        captured_state["consume_returned"] = secret_value
        # Raise to short-circuit the rest of the orchestration; we have all
        # the invariants we need to assert.
        raise ExecutorError(
            "intentional early exit — invariant captured",
            returncode=1,
            output="",
        )

    executor_control = _make_executor_control()
    executor_control.consume_harness_python_secret.side_effect = real_consume
    executor_control.install_extension.side_effect = install_capture

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            executor_control=executor_control,
        )

    # Order is correct: consume_harness_python_secret was invoked before
    # install_extension (spec'd MagicMock would have failed if not).
    executor_control.consume_harness_python_secret.assert_called_once()
    executor_control.install_extension.assert_called_once()

    assert captured_state.get("secret_present_at_install") is False, (
        "W13-11 (b) defense-in-depth invariant broken: bind-mounted "
        "HMAC secret file was still present on disk at the instant "
        "executor_control.install_extension was invoked. The AST "
        "sequence gate said consume runs before install; this runtime "
        "test says the unlink side effect must have completed by then. "
        "If this asserts, the eager-consume helper succeeded at "
        "reading the secret but failed to unlink, re-opening the "
        "same-UID install -> setup_monitor race window that W13-11 "
        "closed."
    )
    assert captured_state.get("consume_returned") == secret_value, (
        "Sanity guard: the real eager-consume helper must have "
        "returned the secret string we pre-wrote — otherwise the "
        "install_capture side_effect ran before consume completed "
        "and the invariant above is meaningless."
    )


def test_run_analysis_job_marks_failure_and_closes_session() -> None:
    """Background jobs should persist failure details when execution aborts."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=FileNotFoundError("missing report"),
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with("job-1", "missing report", error_code=None)
    session.close.assert_called_once_with()


def test_run_analysis_job_persists_trigger_error_code() -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    error = analysis_service.TriggerPlanError(
        "trigger_apply_failed",
        "Executor did not apply the trigger payload during sandbox automation.",
    )
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=error,
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "Executor did not apply the trigger payload during sandbox automation.",
        error_code="trigger_apply_failed",
    )


def test_run_analysis_job_marks_completion_and_closes_session() -> None:
    """Background jobs should persist the final success payload."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    response = AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message="done",
        install_output="install-ok",
        automation_output="automation-ok",
        report_path="activation_report.json",
    )
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.complete_job"
        ) as mock_complete,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            return_value=response,
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    # ES-5: the worker threads static_report_path into complete_job; it is None
    # here because the static gate did not run (flag OFF -> response.static_report
    # is None), keeping the dynamic-only completion unchanged.
    mock_complete.assert_called_once_with("job-1", response, static_report_path=None)
    session.close.assert_called_once_with()


def test_run_analysis_job_records_static_report_path_when_gate_ran() -> None:
    """ES-5: when the static gate ran (ALLOW/WARN), the worker records the
    deterministic per-job static report name on the completed row so
    GET /analyze/{job_id} can fold the static report into the response.

    The flag-ON signal is ``result.static_report is not None`` — the orchestrator
    folds the gate's StaticAnalysisReport onto the AnalyzeResponse. run_analysis_job
    derives ``static_report_{job_id}.json`` and threads it into complete_job.
    """
    from appcore.contracts.schema_defs.static_analysis_bundle import (
        StaticAnalysisReport,
    )
    from packages.analysis_contracts.static_detection import (
        StaticDetectionReport,
        StaticGateDecision,
        StaticGateOutcome,
    )

    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    static_report = StaticAnalysisReport(
        detection_report=StaticDetectionReport(),
        gate_outcome=StaticGateOutcome(
            decision=StaticGateDecision.WARN,
            warned_by=["extrace.s3.unusual_file_signature"],
        ),
    )
    response = AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message="done",
        install_output="install-ok",
        automation_output="automation-ok",
        report_path="activation_report.json",
        static_report=static_report,
    )
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.complete_job"
        ) as mock_complete,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            return_value=response,
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_complete.assert_called_once_with(
        "job-1", response, static_report_path="static_report_job-1.json"
    )
    session.close.assert_called_once_with()


def test_run_analysis_job_marks_value_error_failure() -> None:
    """ValueError should fail background jobs instead of leaving them running."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=ValueError("bad trigger payload"),
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "bad trigger payload",
        error_code=None,
    )
    session.close.assert_called_once_with()


def test_run_analysis_job_swallows_cancellation_without_calling_fail_job() -> None:
    """AnalysisCancelledError must short-circuit silently — the job row was already
    marked cancelled by the /cancel endpoint, so a second fail_job would clobber it."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-c1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.job_service.complete_job"
        ) as mock_complete,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=analysis_service.AnalysisCancelledError("cancelled"),
        ),
    ):
        analysis_service.run_analysis_job("job-c1", request)

    mock_fail.assert_not_called()
    mock_complete.assert_not_called()
    session.close.assert_called_once_with()


def test_run_analysis_job_skips_fail_job_when_cancelled_during_executor_error() -> None:
    """If the user cancels mid-run, the executor often surfaces an ExecutorError
    when the sandbox reset interrupts it. fail_job must NOT overwrite the
    'cancelled' status set by the /cancel endpoint."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-c2", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.is_job_cancelled",
            return_value=True,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=ExecutorError("sandbox reset interrupted run"),
        ),
    ):
        analysis_service.run_analysis_job("job-c2", request)

    mock_fail.assert_not_called()
    session.close.assert_called_once_with()


def test_run_analysis_job_progress_update_swallows_keyerror_when_job_vanishes() -> None:
    """The background heartbeat keeps emitting after the row could be deleted in
    rare edge cases (e.g. interactive tests). progress_update must not crash the
    automation thread when update_job_step raises KeyError."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    captured_callback: dict[str, object] = {}

    def fake_execute(*_args, **kwargs):
        captured_callback["cb"] = kwargs["progress_callback"]
        # Fire a progress update from the executor side and then short-circuit.
        kwargs["progress_callback"](
            "run_monitoring",
            "running",
            "Scenario 1/2",
            None,
            {"completed": 1, "total": 2},
        )
        raise analysis_service.AnalysisCancelledError("cancelled")

    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-c3", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.update_job_step",
            side_effect=KeyError("job-c3"),
        ) as mock_update_step,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=fake_execute,
        ),
    ):
        # Should NOT raise — KeyError is swallowed inside progress_update.
        analysis_service.run_analysis_job("job-c3", request)

    assert mock_update_step.call_count >= 1
    session.close.assert_called_once_with()


def test_run_analysis_job_marks_type_error_failure_and_reraises() -> None:
    """Unexpected worker bugs should fail the job before the thread crashes."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=TypeError("planner wiring bug"),
        ),
        pytest.raises(TypeError, match="planner wiring bug"),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "planner wiring bug",
        error_code=None,
    )
    session.close.assert_called_once_with()


def test_run_analysis_job_terminal_write_guard_fails_and_reraises_off_taxonomy() -> (
    None
):
    """S2 (W23 B3): an exception OUTSIDE the closed analyze taxonomy must still
    write a terminal failure (releasing the single-active slot) and then
    re-raise, instead of escaping ``run_analysis_job`` with the row stuck
    ``running`` (the worker-no-catch-all wedge). KeyError is in neither
    ANALYZE_RECOVERABLE_ERROR_TYPES nor ANALYZE_PROGRAMMING_ERROR_TYPES.
    """
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.is_job_cancelled",
            return_value=False,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=KeyError("unexpected wedge"),
        ),
        pytest.raises(KeyError),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "'unexpected wedge'",
        error_code="worker_uncaught_error",
    )
    session.close.assert_called_once_with()


def test_run_analysis_job_terminal_write_guard_finalizes_when_cancelled() -> None:
    """S2 (W23 B3): when a cancel is in flight as an off-taxonomy exception hits,
    the terminal-write guard finalizes to `cancelled` (cancel intent is
    authoritative) and re-raises — it must NOT call fail_job."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.is_job_cancelled",
            return_value=True,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.finalize_cancelled_job"
        ) as mock_finalize,
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=KeyError("unexpected wedge"),
        ),
        pytest.raises(KeyError),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_finalize.assert_called_once_with("job-1")
    mock_fail.assert_not_called()
    session.close.assert_called_once_with()


def test_run_analysis_job_starts_and_stops_heartbeat_thread() -> None:
    """S2 (W23 B3): the worker spawns a dedicated per-job heartbeat thread,
    starts it, and stops (joins) it on exit — pinning the heartbeat wiring that
    the stale-running reaper depends on."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    response = AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message="done",
        install_output="install-ok",
        automation_output="automation-ok",
        report_path="activation_report.json",
    )
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch("workflows.marketplace.analysis_service.job_service.complete_job"),
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            return_value=response,
        ),
        patch("workflows.marketplace.analysis_service.threading.Thread") as mock_thread,
    ):
        analysis_service.run_analysis_job("job-hb", request)

    assert mock_thread.call_count == 1
    _, kwargs = mock_thread.call_args
    assert kwargs["name"].startswith("analysis-heartbeat-")
    assert kwargs["args"][0] == "job-hb"
    assert kwargs["daemon"] is True
    mock_thread.return_value.start.assert_called_once()
    mock_thread.return_value.join.assert_called_once()


def test_map_executor_error_for_install_branch() -> None:
    """Install-related executor failures should get a specific HTTP detail."""
    exc = analysis_service.ExecutorError(
        "Install failed",
        returncode=1,
        output="boom",
    )

    mapped = analysis_service.map_executor_error(exc)

    assert mapped.status_code == 502
    assert "install extension" in mapped.detail.lower()
    assert "error_id=" in mapped.detail


def test_map_executor_error_redacts_internal_paths_and_env(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Raw exception text must not surface in HTTP detail; logger keeps it."""
    leaky = analysis_service.ExecutorError(
        "Internal /etc/secrets/db.pem read failed; HOME=/home/operator/.config",
        returncode=1,
        output="POSTGRES_PASSWORD=hunter2",
    )

    with caplog.at_level("WARNING", logger="workflows.marketplace.analysis_service"):
        mapped = analysis_service.map_executor_error(leaky)

    detail = mapped.detail
    assert mapped.status_code == 502
    assert "/etc/" not in detail
    assert "/home/" not in detail
    assert "POSTGRES_PASSWORD" not in detail
    assert "hunter2" not in detail
    assert detail.startswith("Automation failed in sandbox.")
    assert "error_id=" in detail

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "executor_error" in logged
    assert "/etc/secrets/db.pem" in logged
