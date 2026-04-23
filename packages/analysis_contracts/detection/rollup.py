"""Deterministic verdict rollup for detection findings."""

from __future__ import annotations

from packages.analysis_contracts.detection.enums import Confidence, Severity, Verdict
from packages.analysis_contracts.detection.finding import DetectionFinding
from packages.analysis_contracts.detection.report import AutomationHealthStatus


def compute_verdict(
    findings: list[DetectionFinding],
    automation_health: AutomationHealthStatus,
) -> tuple[Verdict, str]:
    """Apply the ADR 0003 verdict table with explicit inconclusive dominance."""

    blockers = automation_health.blockers or automation_health.reasons
    if automation_health.status == "inconclusive":
        blocker_text = ", ".join(blockers) if blockers else "unknown blocker"
        return Verdict.INCONCLUSIVE, f"analysis incomplete: {blocker_text}"

    if any(
        finding.severity == Severity.CRITICAL and finding.confidence == Confidence.HIGH
        for finding in findings
    ):
        return Verdict.MALICIOUS, "critical finding with high confidence"

    high_confident = [
        finding
        for finding in findings
        if finding.severity == Severity.HIGH
        and finding.confidence in {Confidence.HIGH, Confidence.MEDIUM}
    ]
    if len(high_confident) >= 2:
        return Verdict.MALICIOUS, f"{len(high_confident)} high-severity findings"

    medium_count = sum(1 for finding in findings if finding.severity == Severity.MEDIUM)
    if len(high_confident) == 1:
        return Verdict.SUSPICIOUS, "single high-severity finding requires review"
    if medium_count >= 3:
        return Verdict.SUSPICIOUS, f"{medium_count} medium-severity findings"

    if findings and all(
        finding.severity in {Severity.LOW, Severity.INFO} for finding in findings
    ):
        return Verdict.CLEAN_WITH_NOTES, "informational findings only"

    if not findings:
        return Verdict.CLEAN, "no rules fired"

    return Verdict.SUSPICIOUS, "mixed lower-severity findings"


__all__ = ["compute_verdict"]
