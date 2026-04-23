from __future__ import annotations

from typing import Any

import pytest

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    ExtensionIdentity,
    RuleLifecycle,
    Severity,
    Verdict,
)
from packages.analysis_engine.runner import run_detection


class _SilentRule:
    rule_id = "extrace.test.silent"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class = None
    severity = Severity.LOW
    description = "Never fires."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        return []


class _FiringRule:
    rule_id = "extrace.test.fire"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class = AdversaryClass.A4
    severity = Severity.HIGH
    description = "Always fires."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        return [
            DetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1041"],
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                title="Synthetic firing rule",
                description="Synthetic production finding for runner coverage.",
                evidence=[],
                adversary_class=self.adversary_class,
            )
        ]


class _FailingRule:
    rule_id = "extrace.test.error"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class = None
    severity = Severity.LOW
    description = "Raises a narrow handled error."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        raise ValueError("synthetic evaluation failure")


class _DraftEscalationRule:
    rule_id = "extrace.test.draft"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.DRAFT
    adversary_class = AdversaryClass.A1
    severity = Severity.CRITICAL
    description = "Should be capped by lifecycle rules."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        return [
            DetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1555"],
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                title="Draft high-confidence finding",
                description="This finding should be downgraded by the runner.",
                evidence=[],
                adversary_class=self.adversary_class,
            )
        ]


def _activation_report(**overrides: Any) -> ActivationReport:
    payload: dict[str, Any] = {
        "report_version": 2,
        "target_extension_expected": "extrace.fixture-chat",
        "automation_health": {"status": "healthy", "reasons": []},
        "verdict": {},
        "summary": {},
        "scenario_traces": [],
        "evidence_events": [],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
    }
    payload.update(overrides)
    return ActivationReport.model_validate(payload)


def test_rule_runner_builds_detection_report() -> None:
    report = run_detection(
        _activation_report(),
        rules=[_FiringRule(), _SilentRule()],
        activation_report_ref="activation_report_fixture.json",
        analyzed_extension=ExtensionIdentity(
            publisher="extrace",
            name="fixture-chat",
            version="0.0.1",
        ),
    )

    assert report.activation_report_ref == "activation_report_fixture.json"
    assert report.analyzed_extension.version == "0.0.1"
    assert report.verdict == Verdict.SUSPICIOUS
    assert len(report.findings) == 1
    assert [item.status for item in report.rules_executed] == ["fired", "silent"]


def test_error_in_rule_forces_inconclusive_verdict() -> None:
    report = run_detection(
        _activation_report(),
        rules=[_FailingRule(), _FiringRule()],
    )

    assert report.verdict == Verdict.INCONCLUSIVE
    assert "rule_execution_errors" in report.verdict_rationale
    assert len(report.findings) == 1
    assert report.rules_executed[0].status == "error"
    assert report.rules_executed[0].error_detail == "synthetic evaluation failure"
    assert report.rules_executed[1].status == "fired"


def test_draft_rules_are_capped_to_low_confidence_and_non_malicious() -> None:
    report = run_detection(
        _activation_report(),
        rules=[_DraftEscalationRule()],
    )

    assert report.verdict == Verdict.SUSPICIOUS
    assert report.findings[0].severity == Severity.MEDIUM
    assert report.findings[0].confidence == Confidence.LOW


def test_all_rules_error_cannot_produce_clean_verdict() -> None:
    report = run_detection(
        _activation_report(),
        rules=[_FailingRule()],
    )

    assert report.verdict == Verdict.INCONCLUSIVE
    assert report.findings == []
    assert all(item.status == "error" for item in report.rules_executed)
    assert "extrace.test.error" in report.verdict_rationale


def test_unexpected_rule_errors_are_re_raised() -> None:
    class _UnexpectedRule:
        rule_id = "extrace.test.runtime_error"
        rule_version = "1.0.0"
        lifecycle = RuleLifecycle.PRODUCTION
        adversary_class = None
        severity = Severity.LOW
        description = "Raises an unexpected runtime error."

        def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
            raise RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        run_detection(_activation_report(), rules=[_UnexpectedRule()])
