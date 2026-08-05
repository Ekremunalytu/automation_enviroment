"""Framework-free ADR 0016 static gate policy shared by product and evaluator."""

from __future__ import annotations

from packages.analysis_contracts.detection.enums import Severity
from packages.analysis_contracts.static_detection.gate import (
    StaticGateDecision,
    StaticGateOutcome,
)
from packages.analysis_contracts.static_detection.report import StaticDetectionReport

_PROMOTED_HIGH_BLOCKERS: frozenset[str] = frozenset({"extrace.s2.typosquat"})
_WARN_SEVERITIES: frozenset[Severity] = frozenset(
    {Severity.HIGH, Severity.MEDIUM, Severity.LOW}
)
_ALLOW_REASON_CLEAN = "No blocking or warnable static findings."


def _is_blocking(severity: Severity, rule_id: str) -> bool:
    if severity is Severity.CRITICAL:
        return True
    return severity is Severity.HIGH and rule_id in _PROMOTED_HIGH_BLOCKERS


def _dedupe(rule_ids: list[str]) -> list[str]:
    return sorted(set(rule_ids))


def _inconclusive_reasons(report: StaticDetectionReport) -> list[str]:
    reasons = set(report.coverage.coverage_reasons)
    for tool_record in report.tool_executions:
        reasons.update(tool_record.coverage.coverage_reasons)
        if tool_record.status == "timeout":
            reasons.add("tool_timeout")
        elif tool_record.status == "error":
            reasons.add("tool_error")
        elif (
            tool_record.status == "partial"
            and not tool_record.coverage.coverage_reasons
        ):
            reasons.add(
                "parser_error" if tool_record.errored_rule_ids else "budget_stop"
            )
    if report.partial and not reasons:
        reasons.add("parser_error")
    return sorted(reasons)


def evaluate_static_gate(report: StaticDetectionReport) -> StaticGateOutcome:
    """Apply BLOCK > INCONCLUSIVE > WARN > ALLOW to one schema-valid report."""

    blocked_by = _dedupe(
        [
            finding.rule_id
            for finding in report.findings
            if _is_blocking(finding.severity, finding.rule_id)
        ]
    )
    if blocked_by:
        return StaticGateOutcome(
            decision=StaticGateDecision.BLOCK,
            blocked_by=blocked_by,
        )

    warned_by = _dedupe(
        [
            finding.rule_id
            for finding in report.findings
            if finding.severity in _WARN_SEVERITIES
        ]
    )
    inconclusive_reasons = _inconclusive_reasons(report)
    if inconclusive_reasons:
        return StaticGateOutcome(
            decision=StaticGateDecision.INCONCLUSIVE,
            warned_by=warned_by,
            inconclusive_reasons=inconclusive_reasons,
        )
    if warned_by:
        return StaticGateOutcome(
            decision=StaticGateDecision.WARN,
            warned_by=warned_by,
        )
    return StaticGateOutcome(
        decision=StaticGateDecision.ALLOW,
        allow_reason=_ALLOW_REASON_CLEAN,
    )


__all__ = ["_PROMOTED_HIGH_BLOCKERS", "evaluate_static_gate"]
