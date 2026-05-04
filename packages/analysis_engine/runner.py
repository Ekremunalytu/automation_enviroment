"""Detection runner that converts ActivationReport data into DetectionReport."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import datetime as _dt
from typing import Literal

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AutomationHealthStatus,
    Confidence,
    DetectionFinding,
    DetectionReport,
    ExtensionIdentity,
    RuleExecutionRecord,
    RuleExecutionStatus,
    RuleLifecycle,
    Severity,
    Verdict,
    compute_verdict,
)
from packages.analysis_engine.rules.base import DetectionRule
from packages.analysis_engine.rules.registry import get_production_rules

# Python 3.10 executor compatibility: `datetime.UTC` arrived in Python 3.11.
# `getattr` keeps the import site valid on the older runtime.
datetime = _dt.datetime
UTC = getattr(_dt, "UTC", _dt.timezone.utc)  # noqa: UP017

_RULE_EVALUATION_ERRORS = (AttributeError, KeyError, TypeError, ValueError)

AutomationHealthLiteral = Literal["healthy", "degraded", "inconclusive"]


def _normalize_health_status(value: object) -> AutomationHealthLiteral:
    normalized = str(value)
    if normalized == "degraded":
        return "degraded"
    if normalized == "inconclusive":
        return "inconclusive"
    return "healthy"


def _coerce_automation_health(report: ActivationReport) -> AutomationHealthStatus:
    # W10-4: report.automation_health is now a typed AutomationHealth
    # (was dict[str, Any] pre-W10). The detection-side AutomationHealthStatus
    # is a 3-field projection (status/reasons/blockers); copy reasons over
    # and pass them as blockers too because the producer never emits a
    # distinct ``blockers`` list.
    health = report.automation_health
    return AutomationHealthStatus(
        status=_normalize_health_status(health.status),
        reasons=list(health.reasons),
        blockers=list(health.reasons),
    )


def _default_extension_identity(report: ActivationReport) -> ExtensionIdentity:
    expected = report.target_extension_expected or "unknown.unknown"
    publisher, separator, name = expected.partition(".")
    if not separator:
        publisher = "unknown"
        name = expected or "unknown"
    return ExtensionIdentity(publisher=publisher, name=name, version="unknown")


def _cap_finding_for_lifecycle(finding: DetectionFinding) -> DetectionFinding:
    if finding.rule_lifecycle not in {
        RuleLifecycle.DRAFT,
        RuleLifecycle.FIXTURE_VALIDATED,
    }:
        return finding

    severity = finding.severity
    if severity in {Severity.CRITICAL, Severity.HIGH}:
        severity = Severity.MEDIUM
    return finding.model_copy(
        update={
            "severity": severity,
            "confidence": Confidence.LOW,
        }
    )


def _execution_record(
    *,
    rule: DetectionRule,
    status: RuleExecutionStatus,
    finding_ids: list[str] | None = None,
    error_detail: str | None = None,
) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule.rule_id,
        rule_version=rule.rule_version,
        lifecycle=rule.lifecycle,
        status=status,
        finding_ids=finding_ids or [],
        error_detail=error_detail,
    )


def _normalize_findings(
    findings: list[DetectionFinding],
    *,
    rule: DetectionRule,
) -> list[DetectionFinding]:
    normalized: list[DetectionFinding] = []
    for finding in findings:
        normalized_finding = finding.model_copy(
            update={
                "rule_id": rule.rule_id,
                "rule_version": rule.rule_version,
                "rule_lifecycle": rule.lifecycle,
                "adversary_class": finding.adversary_class or rule.adversary_class,
            }
        )
        normalized.append(_cap_finding_for_lifecycle(normalized_finding))
    return normalized


def _degrade_health_for_rule_errors(
    automation_health: AutomationHealthStatus,
    rules_executed: list[RuleExecutionRecord],
) -> AutomationHealthStatus:
    errored_rule_ids = [
        record.rule_id
        for record in rules_executed
        if record.status == RuleExecutionStatus.ERROR
    ]
    if not errored_rule_ids:
        return automation_health

    blocker = "rule_execution_errors: " + ", ".join(sorted(set(errored_rule_ids)))
    merged_reasons = list(automation_health.reasons)
    if blocker not in merged_reasons:
        merged_reasons.append(blocker)
    merged_blockers = list(automation_health.blockers)
    if blocker not in merged_blockers:
        merged_blockers.append(blocker)
    return AutomationHealthStatus(
        status="inconclusive",
        reasons=merged_reasons,
        blockers=merged_blockers,
    )


def _guard_malicious_without_production(
    verdict: Verdict,
    findings: list[DetectionFinding],
    rationale: str,
) -> tuple[Verdict, str]:
    if verdict != Verdict.MALICIOUS:
        return verdict, rationale
    if any(finding.rule_lifecycle == RuleLifecycle.PRODUCTION for finding in findings):
        return verdict, rationale
    return Verdict.SUSPICIOUS, "malicious escalation requires a production rule"


def run_detection(
    activation_report: ActivationReport,
    rules: list[DetectionRule] | None = None,
    *,
    activation_report_ref: str | None = None,
    analyzed_extension: ExtensionIdentity | None = None,
) -> DetectionReport:
    """Run detection rules over an activation report and build a DetectionReport."""

    selected_rules = list(rules) if rules is not None else get_production_rules()
    findings: list[DetectionFinding] = []
    rules_executed: list[RuleExecutionRecord] = []

    for rule in selected_rules:
        try:
            raw_findings = rule.evaluate(activation_report)
        except _RULE_EVALUATION_ERRORS as exc:
            rules_executed.append(
                _execution_record(
                    rule=rule,
                    status=RuleExecutionStatus.ERROR,
                    error_detail=str(exc),
                )
            )
            continue

        normalized_findings = _normalize_findings(raw_findings, rule=rule)
        findings.extend(normalized_findings)
        rules_executed.append(
            _execution_record(
                rule=rule,
                status=(
                    RuleExecutionStatus.FIRED
                    if normalized_findings
                    else RuleExecutionStatus.SILENT
                ),
                finding_ids=[finding.id for finding in normalized_findings],
            )
        )

    automation_health = _coerce_automation_health(activation_report)
    automation_health = _degrade_health_for_rule_errors(
        automation_health, rules_executed
    )
    verdict, rationale = compute_verdict(findings, automation_health)
    verdict, rationale = _guard_malicious_without_production(
        verdict, findings, rationale
    )

    return DetectionReport(
        activation_report_ref=(
            activation_report_ref or activation_report.target_extension_expected
        ),
        analyzed_extension=(
            analyzed_extension or _default_extension_identity(activation_report)
        ),
        findings=findings,
        verdict=verdict,
        verdict_rationale=rationale,
        rules_executed=rules_executed,
        generated_at=datetime.now(UTC),
    )


__all__ = ["run_detection"]
