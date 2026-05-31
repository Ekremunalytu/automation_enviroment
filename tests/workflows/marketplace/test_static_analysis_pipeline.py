"""``run_static_analysis`` runner tests (ES-3b core, ADR 0016).

Exercises the container-runner glue with a recording fake control and a
pre-written report file — no Docker, no orchestrator, no shared-contract or
DB surface touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from appcore.contracts.schema_defs.static_analysis_bundle import StaticAnalysisReport
from packages.analysis_contracts.detection.enums import (
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticDetectionReport,
    StaticGateDecision,
)
from workflows.marketplace.static_analysis import (
    StaticReportError,
    run_static_analysis,
)


class _RecordingControl:
    """Stand-in for ``StaticAnalyzerControl`` that records the exec kwargs."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run_static_analysis(
        self,
        *,
        vsix_dir: str,
        report_path: str,
        rules_version: str,
        timeout_budget_s: int,
    ) -> str:
        self.calls.append(
            {
                "vsix_dir": vsix_dir,
                "report_path": report_path,
                "rules_version": rules_version,
                "timeout_budget_s": timeout_budget_s,
            }
        )
        return "static-stdout"


def _finding(*, rule_id: str, severity: Severity) -> StaticDetectionFinding:
    return StaticDetectionFinding(
        rule_id=rule_id,
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["attack.T1036"],
        severity=severity,
        confidence=Confidence.MEDIUM,
        title="t",
        description="d",
    )


def _write_report(path: Path, report: StaticDetectionReport) -> None:
    path.write_text(report.model_dump_json(), encoding="utf-8")


def test_run_static_analysis_parses_report_and_evaluates_gate(tmp_path: Path) -> None:
    host_report = tmp_path / "static_report_job.json"
    written = StaticDetectionReport(
        findings=[
            _finding(rule_id="extrace.s1.generic_publisher", severity=Severity.LOW)
        ]
    )
    _write_report(host_report, written)
    control = _RecordingControl()

    result = run_static_analysis(
        vsix_dir="/extensions-input/job",
        report_path="/results/static_report_job.json",
        host_report_path=host_report,
        rules_version="1.2.3",
        timeout_budget_s=30,
        control=control,
    )

    assert isinstance(result, StaticAnalysisReport)
    assert [f.rule_id for f in result.detection_report.findings] == [
        "extrace.s1.generic_publisher"
    ]
    # LOW-only -> WARN, naming the finding's rule id.
    assert result.gate_outcome.decision is StaticGateDecision.WARN
    assert result.gate_outcome.warned_by == ["extrace.s1.generic_publisher"]


def test_run_static_analysis_forwards_exec_kwargs(tmp_path: Path) -> None:
    host_report = tmp_path / "static_report_job.json"
    _write_report(host_report, StaticDetectionReport())
    control = _RecordingControl()

    run_static_analysis(
        vsix_dir="/extensions-input/job",
        report_path="/results/static_report_job.json",
        host_report_path=host_report,
        rules_version="9.9.9",
        timeout_budget_s=45,
        control=control,
    )

    assert control.calls == [
        {
            "vsix_dir": "/extensions-input/job",
            "report_path": "/results/static_report_job.json",
            "rules_version": "9.9.9",
            "timeout_budget_s": 45,
        }
    ]


def test_run_static_analysis_block_path(tmp_path: Path) -> None:
    host_report = tmp_path / "static_report_job.json"
    _write_report(
        host_report,
        StaticDetectionReport(
            findings=[_finding(rule_id="extrace.s2.typosquat", severity=Severity.HIGH)]
        ),
    )

    result = run_static_analysis(
        vsix_dir="/extensions-input/job",
        report_path="/results/static_report_job.json",
        host_report_path=host_report,
        rules_version="1.0.0",
        timeout_budget_s=30,
        control=_RecordingControl(),
    )

    assert result.gate_outcome.decision is StaticGateDecision.BLOCK
    assert result.gate_outcome.blocked_by == ["extrace.s2.typosquat"]


def test_run_static_analysis_empty_report_allows(tmp_path: Path) -> None:
    host_report = tmp_path / "static_report_job.json"
    _write_report(host_report, StaticDetectionReport())

    result = run_static_analysis(
        vsix_dir="/extensions-input/job",
        report_path="/results/static_report_job.json",
        host_report_path=host_report,
        rules_version="1.0.0",
        timeout_budget_s=30,
        control=_RecordingControl(),
    )

    assert result.gate_outcome.decision is StaticGateDecision.ALLOW


def test_run_static_analysis_malformed_report_fails_closed(tmp_path: Path) -> None:
    """A truncated / garbage report body raises a typed ``StaticReportError``
    (fail closed) — never a silent ALLOW from an unreadable report."""
    host_report = tmp_path / "static_report_job.json"
    host_report.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(StaticReportError):
        run_static_analysis(
            vsix_dir="/extensions-input/job",
            report_path="/results/static_report_job.json",
            host_report_path=host_report,
            rules_version="1.0.0",
            timeout_budget_s=30,
            control=_RecordingControl(),
        )


def test_run_static_analysis_schema_invalid_report_fails_closed(
    tmp_path: Path,
) -> None:
    """A well-formed-JSON but schema-invalid report (here the superseded
    ``schema_version: '1'``) also fails closed — this doubles as the v2-bump
    migration guard: an old-schema report is rejected, not silently accepted."""
    host_report = tmp_path / "static_report_job.json"
    host_report.write_text('{"schema_version": "1"}', encoding="utf-8")

    with pytest.raises(StaticReportError):
        run_static_analysis(
            vsix_dir="/extensions-input/job",
            report_path="/results/static_report_job.json",
            host_report_path=host_report,
            rules_version="1.0.0",
            timeout_budget_s=30,
            control=_RecordingControl(),
        )
