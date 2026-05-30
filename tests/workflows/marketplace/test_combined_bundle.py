"""``build_combined_bundle`` tests (ES-3b core, ADR 0016).

Focused on the BLOCK / cheap-reject path where ``dynamic_bundle`` is ``None``
(the sandbox was skipped). The dynamic-attached path is a one-line, Pydantic-
validated passthrough exercised end-to-end by the later orchestrator stage.
"""

from __future__ import annotations

from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
)
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
    build_combined_bundle,
    evaluate_static_gate,
)


def _blocked_static_report() -> StaticAnalysisReport:
    report = StaticDetectionReport(
        findings=[
            StaticDetectionFinding(
                rule_id="extrace.s2.typosquat",
                rule_version="1.0.0",
                rule_lifecycle=RuleLifecycle.PRODUCTION,
                categories=["attack.T1036"],
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                title="typosquat",
                description="impersonates a popular extension",
            )
        ]
    )
    return StaticAnalysisReport(
        detection_report=report, gate_outcome=evaluate_static_gate(report)
    )


def test_combined_bundle_defaults_dynamic_to_none() -> None:
    static_report = _blocked_static_report()

    bundle = build_combined_bundle(static_report)

    assert isinstance(bundle, CombinedAnalysisBundle)
    assert bundle.dynamic_bundle is None
    assert bundle.static_report == static_report
    # The cheap-reject bundle preserves the BLOCK cause for the report/UI/log.
    assert bundle.static_report.gate_outcome.decision is StaticGateDecision.BLOCK
    assert bundle.static_report.gate_outcome.blocked_by == ["extrace.s2.typosquat"]


def test_combined_bundle_explicit_none_dynamic() -> None:
    static_report = _blocked_static_report()

    bundle = build_combined_bundle(static_report, None)

    assert bundle.dynamic_bundle is None
    assert bundle.static_report == static_report
