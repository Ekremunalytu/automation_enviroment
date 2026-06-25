"""ES-3b (ADR 0016 §Decision 1): orchestrator static-gate stage unit tests.

Container-free, DB-free coverage for the decision gate, the
``run_static_analysis_stage`` reporter wiring, and the flag-aware
``empty_job_steps`` seam. The end-to-end ``rejected_static`` DB transition is
covered by ``tests/platform/storage/test_static_blocked_job_state.py``.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from appcore.contracts.schema_defs.analysis_jobs import ANALYSIS_JOB_STEP_NAMES
from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
)
from appcore.contracts.schemas import AnalyzeRequest
from executor.static_control import StaticAnalyzerError
from packages.analysis_contracts.detection.enums import (
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticDetectionReport,
    StaticGateDecision,
    StaticGateOutcome,
)
from workflows.marketplace import analysis_service, job_service
from workflows.marketplace.analysis_errors import AnalysisCancelledError
from workflows.marketplace.analysis_execution import (
    StepReporter,
    _run_static_off_thread,
    run_static_analysis_stage,
)
from workflows.marketplace.analysis_service import _apply_static_gate_decision
from workflows.marketplace.static_analysis import StaticAnalysisBlockedError


def _recording_reporter() -> tuple[StepReporter, list[tuple[str, str, str]]]:
    events: list[tuple[str, str, str]] = []

    def _cb(step, status, message, error_code=None, progress=None):
        events.append((step, status, message))

    return StepReporter(_cb), events


def _report(outcome: StaticGateOutcome) -> StaticAnalysisReport:
    return StaticAnalysisReport(
        detection_report=StaticDetectionReport(), gate_outcome=outcome
    )


# ---------------------------------------------------------------------------
# Decision gate
# ---------------------------------------------------------------------------


def test_apply_gate_decision_block_raises_and_persists_bundle(tmp_path: Path) -> None:
    reporter, events = _recording_reporter()
    report = _report(
        StaticGateOutcome(
            decision=StaticGateDecision.BLOCK, blocked_by=["extrace.s2.typosquat"]
        )
    )
    host_report_path = tmp_path / "static_report_job.json"

    with pytest.raises(StaticAnalysisBlockedError) as exc_info:
        _apply_static_gate_decision(reporter, report, host_report_path=host_report_path)

    assert exc_info.value.static_report is report
    assert "extrace.s2.typosquat" in str(exc_info.value)
    # decision_gate emitted `running` but NOT `completed` — the reject CRUD
    # transition finalizes the step.
    gate_statuses = [status for step, status, _ in events if step == "decision_gate"]
    assert gate_statuses == ["running"]

    # The combined bundle (static-only; dynamic skipped) is persisted for the
    # reject path and round-trips as a CombinedAnalysisBundle.
    assert host_report_path.is_file()
    bundle = CombinedAnalysisBundle.model_validate(
        json.loads(host_report_path.read_text(encoding="utf-8"))
    )
    assert bundle.dynamic_bundle is None
    assert bundle.static_report.gate_outcome.decision is StaticGateDecision.BLOCK


def test_apply_gate_decision_warn_completes_and_persists(tmp_path: Path) -> None:
    reporter, events = _recording_reporter()
    report = _report(
        StaticGateOutcome(
            decision=StaticGateDecision.WARN,
            warned_by=["extrace.a2.startup_network_beacon"],
        )
    )
    host_report_path = tmp_path / "static_report_job.json"

    returned = _apply_static_gate_decision(
        reporter, report, host_report_path=host_report_path
    )

    gate_statuses = [status for step, status, _ in events if step == "decision_gate"]
    assert gate_statuses == ["running", "completed"]
    # ES-5: WARN now persists the static-only combined bundle (dynamic_bundle
    # None) so the completion path records static_report_path and the router folds
    # the static report into the response; the report is also returned to the
    # caller for the response surface.
    assert returned is report
    assert host_report_path.is_file()
    bundle = CombinedAnalysisBundle.model_validate(
        json.loads(host_report_path.read_text(encoding="utf-8"))
    )
    assert bundle.dynamic_bundle is None
    assert bundle.static_report.gate_outcome.decision is StaticGateDecision.WARN


def test_apply_gate_decision_allow_completes(tmp_path: Path) -> None:
    reporter, events = _recording_reporter()
    report = _report(
        StaticGateOutcome(decision=StaticGateDecision.ALLOW, allow_reason="clean")
    )
    host_report_path = tmp_path / "static_report_job.json"

    returned = _apply_static_gate_decision(
        reporter, report, host_report_path=host_report_path
    )

    gate_statuses = [status for step, status, _ in events if step == "decision_gate"]
    assert gate_statuses == ["running", "completed"]
    # ES-5: ALLOW returns the report and persists the static-only combined bundle
    # so the completion path can record static_report_path.
    assert returned is report
    assert host_report_path.is_file()
    bundle = CombinedAnalysisBundle.model_validate(
        json.loads(host_report_path.read_text(encoding="utf-8"))
    )
    assert bundle.dynamic_bundle is None
    assert bundle.static_report.gate_outcome.decision is StaticGateDecision.ALLOW


# ---------------------------------------------------------------------------
# run_static_analysis_stage reporter wiring
# ---------------------------------------------------------------------------


def test_run_static_analysis_stage_emits_running_then_completed() -> None:
    reporter, events = _recording_reporter()
    report = _report(
        StaticGateOutcome(decision=StaticGateDecision.ALLOW, allow_reason="clean")
    )

    out = run_static_analysis_stage(reporter, run_static=lambda: report)

    assert out is report
    sa_statuses = [status for step, status, _ in events if step == "static_analysis"]
    assert sa_statuses == ["running", "completed"]


def test_run_static_analysis_stage_failure_emits_failed_and_raises() -> None:
    reporter, events = _recording_reporter()

    def _boom() -> StaticAnalysisReport:
        raise StaticAnalyzerError("rc=2", returncode=2, output="boom stderr")

    with pytest.raises(StaticAnalyzerError):
        run_static_analysis_stage(reporter, run_static=_boom)

    sa_statuses = [status for step, status, _ in events if step == "static_analysis"]
    assert sa_statuses == ["running", "failed"]


def test_run_static_off_thread_cancel_fires_on_cancel_and_raises() -> None:
    """On a cancel signal the coordinator fires ``on_cancel`` (the in-container
    ``pkill`` hook) once, then raises ``AnalysisCancelledError`` on the worker
    frame — mirrors the reset coordinator's ~100ms cancel cadence.
    """
    release = threading.Event()
    on_cancel_calls: list[int] = []

    def _run_static() -> StaticAnalysisReport:
        # Block until the cancel hook releases us (safety-bounded) so the
        # ~100ms poll loop observes the cancel before the runner returns.
        release.wait(2.0)
        return _report(
            StaticGateOutcome(decision=StaticGateDecision.ALLOW, allow_reason="clean")
        )

    def _on_cancel() -> None:
        on_cancel_calls.append(1)
        release.set()

    with pytest.raises(AnalysisCancelledError):
        _run_static_off_thread(
            _run_static, cancel_check=lambda: True, on_cancel=_on_cancel
        )

    assert on_cancel_calls == [1]


def test_run_static_off_thread_reraises_held_exception() -> None:
    """A container / parse failure on the coordinator thread (no cancel) is
    captured and re-raised on the worker frame, never swallowed into a
    missing-report assertion."""
    boom = RuntimeError("static container blew up")

    def _run_static() -> StaticAnalysisReport:
        raise boom

    with pytest.raises(RuntimeError) as excinfo:
        _run_static_off_thread(_run_static, cancel_check=None)
    assert excinfo.value is boom


# ---------------------------------------------------------------------------
# Flag-aware empty_job_steps seam (the documented ES-1 step-Literal regression)
# ---------------------------------------------------------------------------


def test_empty_job_steps_disabled_seeds_static_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(job_service.settings.static_analysis, "ENABLED", False)
    steps = job_service.empty_job_steps()

    assert [s.name for s in steps] == list(ANALYSIS_JOB_STEP_NAMES)
    assert steps[0].name == "static_analysis" and steps[0].status == "skipped"
    assert steps[1].name == "decision_gate" and steps[1].status == "skipped"
    assert all(s.status == "pending" for s in steps[2:])


def test_empty_job_steps_enabled_seeds_static_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(job_service.settings.static_analysis, "ENABLED", True)
    steps = job_service.empty_job_steps()

    assert steps[0].name == "static_analysis" and steps[0].status == "pending"
    assert steps[1].name == "decision_gate" and steps[1].status == "pending"
    assert all(s.status == "pending" for s in steps[2:])


def test_create_job_snapshot_validates_canonical_seven_steps() -> None:
    """create_job_snapshot must build a snapshot that passes `_validate_steps`."""
    snapshot = job_service.create_job_snapshot(
        AnalyzeRequest(publisher="ms-python", name="python", version="2025.0.0")
    )
    assert [s["name"] for s in snapshot["steps"]] == list(ANALYSIS_JOB_STEP_NAMES)


# ---------------------------------------------------------------------------
# _run_static_gate path seam (container vsix_dir + /results vs OUTPUT_DIR)
# ---------------------------------------------------------------------------


class _FakeStaticControl:
    """Stand-in ``StaticAnalyzerControl`` that writes a report to the host path.

    Mirrors the real container: it writes to ``report_path`` on the ``/results``
    mount, which the host reads back under OUTPUT_DIR. The test points OUTPUT_DIR
    at ``tmp_path`` so the fake writes the report there using the basename of the
    container ``report_path``.
    """

    def __init__(
        self, output_dir: Path, findings: list[StaticDetectionFinding]
    ) -> None:
        self._output_dir = output_dir
        self._findings = findings
        self.calls: list[dict[str, object]] = []
        self.cancelled = False

    def run_static_analysis(
        self,
        *,
        vsix_dir: str,
        report_path: str,
        rules_version: str,
        timeout_budget_s: int,
        vsix_sha256: str = "",
    ) -> str:
        self.calls.append(
            {
                "vsix_dir": vsix_dir,
                "report_path": report_path,
                "rules_version": rules_version,
                "timeout_budget_s": timeout_budget_s,
                "vsix_sha256": vsix_sha256,
            }
        )
        host_path = self._output_dir / Path(report_path).name
        host_path.write_text(
            StaticDetectionReport(findings=self._findings).model_dump_json(),
            encoding="utf-8",
        )
        return "static-stdout"

    def cancel(self) -> None:
        self.cancelled = True


def _typosquat_finding() -> StaticDetectionFinding:
    return StaticDetectionFinding(
        rule_id="extrace.s2.typosquat",
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["attack.T1036"],
        severity=Severity.HIGH,
        confidence=Confidence.MEDIUM,
        title="typosquat",
        description="d",
    )


def test_run_static_gate_block_derives_paths_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(analysis_service.settings.project, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(
        analysis_service.settings.static_analysis, "RULES_VERSION", "1.2.3"
    )
    control = _FakeStaticControl(tmp_path, [_typosquat_finding()])
    reporter, _events = _recording_reporter()
    request = AnalyzeRequest(publisher="ms-python", name="python", version="2025.0.0")

    with pytest.raises(StaticAnalysisBlockedError) as exc_info:
        analysis_service._run_static_gate(
            request,
            reporter,
            control,
            static_report_name="static_report_job.json",
        )

    decision = exc_info.value.static_report.gate_outcome.decision
    assert decision is StaticGateDecision.BLOCK
    # Path seam: container vsix_dir on the extensions mount; report on /results.
    call = control.calls[0]
    assert str(call["vsix_dir"]).startswith("/extensions-input/")
    assert call["report_path"] == "/results/static_report_job.json"
    assert call["rules_version"] == "1.2.3"
    # Combined bundle persisted under OUTPUT_DIR for the reject path.
    assert (tmp_path / "static_report_job.json").is_file()


def test_run_static_gate_allow_returns_report_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(analysis_service.settings.project, "OUTPUT_DIR", str(tmp_path))
    control = _FakeStaticControl(tmp_path, [])  # empty findings -> ALLOW
    reporter, events = _recording_reporter()
    request = AnalyzeRequest(publisher="ms-python", name="python", version="2025.0.0")

    # No raise — the dynamic stage proceeds after the gate; ES-5 returns the
    # report so the worker can record static_report_path at completion.
    static_report = analysis_service._run_static_gate(
        request, reporter, control, static_report_name="static_report_job.json"
    )

    assert static_report is not None
    assert static_report.gate_outcome.decision is StaticGateDecision.ALLOW
    statuses = {(step, status) for step, status, _ in events}
    assert ("static_analysis", "completed") in statuses
    assert ("decision_gate", "completed") in statuses
    # ES-5: the ALLOW path also persists the static-only combined bundle under
    # OUTPUT_DIR (overwriting the raw detection report) for the response loader.
    persisted = CombinedAnalysisBundle.model_validate(
        json.loads((tmp_path / "static_report_job.json").read_text(encoding="utf-8"))
    )
    assert persisted.dynamic_bundle is None
    assert persisted.static_report.gate_outcome.decision is StaticGateDecision.ALLOW
