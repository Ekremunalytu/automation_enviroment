from __future__ import annotations

from packages.analysis_contracts.detection import (
    AutomationHealthStatus,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
    Verdict,
    compute_verdict,
)


def _finding(
    *,
    severity: Severity,
    confidence: Confidence,
    categories: list[str] | None = None,
) -> DetectionFinding:
    return DetectionFinding(
        rule_id=f"extrace.rule.{severity.value}.{confidence.value}",
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=categories or ["extrace.host.workspace_exfil"],
        severity=severity,
        confidence=confidence,
        title="Synthetic finding",
        description="Synthetic rollup coverage fixture.",
        evidence=[],
    )


def test_inconclusive_health_dominates_all_findings() -> None:
    verdict, rationale = compute_verdict(
        [_finding(severity=Severity.CRITICAL, confidence=Confidence.HIGH)],
        AutomationHealthStatus(
            status="inconclusive",
            blockers=["target_stream_missing", "executor_timeout"],
        ),
    )

    assert verdict == Verdict.INCONCLUSIVE
    assert "target_stream_missing" in rationale


def test_critical_high_confidence_yields_malicious() -> None:
    verdict, rationale = compute_verdict(
        [_finding(severity=Severity.CRITICAL, confidence=Confidence.HIGH)],
        AutomationHealthStatus(status="healthy"),
    )

    assert verdict == Verdict.MALICIOUS
    assert rationale == "critical finding with high confidence"


def test_two_high_findings_yield_malicious() -> None:
    verdict, rationale = compute_verdict(
        [
            _finding(severity=Severity.HIGH, confidence=Confidence.HIGH),
            _finding(
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                categories=["attack.T1496"],
            ),
        ],
        AutomationHealthStatus(status="healthy"),
    )

    assert verdict == Verdict.MALICIOUS
    assert rationale == "2 high-severity findings"


def test_single_high_finding_yields_suspicious() -> None:
    verdict, rationale = compute_verdict(
        [_finding(severity=Severity.HIGH, confidence=Confidence.MEDIUM)],
        AutomationHealthStatus(status="healthy"),
    )

    assert verdict == Verdict.SUSPICIOUS
    assert "single high-severity finding" in rationale


def test_three_medium_findings_yield_suspicious() -> None:
    verdict, rationale = compute_verdict(
        [
            _finding(severity=Severity.MEDIUM, confidence=Confidence.HIGH),
            _finding(
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                categories=["attack.T1041"],
            ),
            _finding(
                severity=Severity.MEDIUM,
                confidence=Confidence.LOW,
                categories=["attack.T1530"],
            ),
        ],
        AutomationHealthStatus(status="healthy"),
    )

    assert verdict == Verdict.SUSPICIOUS
    assert rationale == "3 medium-severity findings"


def test_low_and_info_only_findings_yield_clean_with_notes() -> None:
    verdict, rationale = compute_verdict(
        [
            _finding(severity=Severity.LOW, confidence=Confidence.LOW),
            _finding(
                severity=Severity.INFO,
                confidence=Confidence.LOW,
                categories=["extrace.ext.startup_ui_prompt"],
            ),
        ],
        AutomationHealthStatus(status="healthy"),
    )

    assert verdict == Verdict.CLEAN_WITH_NOTES
    assert rationale == "informational findings only"


def test_no_findings_yield_clean() -> None:
    verdict, rationale = compute_verdict([], AutomationHealthStatus(status="healthy"))

    assert verdict == Verdict.CLEAN
    assert rationale == "no rules fired"


def test_mixed_lower_severity_findings_fall_back_to_suspicious() -> None:
    verdict, rationale = compute_verdict(
        [
            _finding(severity=Severity.MEDIUM, confidence=Confidence.MEDIUM),
            _finding(severity=Severity.LOW, confidence=Confidence.LOW),
        ],
        AutomationHealthStatus(status="degraded", reasons=["verification_gap_present"]),
    )

    assert verdict == Verdict.SUSPICIOUS
    assert rationale == "mixed lower-severity findings"
