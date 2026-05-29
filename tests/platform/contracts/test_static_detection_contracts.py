"""ES-1 static-detection contract invariants (ADR 0016 §Decision 3, schema-first).

Pins the 10 schema-landing invariants so the ES-2..ES-5 tool runners map
INTO a stable contract rather than reshaping it:

1. field-set parity with the dynamic ``DetectionFinding``
2. ADR 0003 enum reuse BY IDENTITY (not parallel clones)
3. ``StaticEvidenceRef`` shape
4. v2 tool Literal pre-ship (yara / trivy slots land at ES-1)
5. ``StaticDetectionReport`` wrapper composition
6. severity-counts <-> ``Severity`` tier parity
7. gate decision three-way (allow / warn / block)
8. ``StaticGateOutcome`` shape + allow_reason-None-on-block invariant
9. ``StaticToolExecutionRecord`` shape (db_freshness_days optional, v2 Trivy)
10. ``CombinedAnalysisBundle`` composition (dynamic bundle optional on BLOCK)
"""

from __future__ import annotations

from typing import get_args

import pytest
from pydantic import ValidationError

from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
)
from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.detection.finding import DetectionFinding
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticDetectionReport,
    StaticEvidenceRef,
    StaticGateDecision,
    StaticGateOutcome,
    StaticSeverityCounts,
    StaticToolExecutionRecord,
)


def _valid_finding(**overrides: object) -> StaticDetectionFinding:
    payload: dict[str, object] = {
        "rule_id": "extrace.s1.activation_wildcard",
        "rule_version": "1.0.0",
        "rule_lifecycle": RuleLifecycle.PRODUCTION,
        "categories": ["extrace.ext.activation_wildcard"],
        "severity": Severity.MEDIUM,
        "confidence": Confidence.HIGH,
        "title": "activationEvents wildcard",
        "description": "Manifest declares activationEvents: ['*'].",
    }
    payload.update(overrides)
    return StaticDetectionFinding(**payload)


def test_finding_field_set_parity_with_dynamic() -> None:
    """StaticDetectionFinding must mirror DetectionFinding's field names."""
    assert set(StaticDetectionFinding.model_fields) == set(
        DetectionFinding.model_fields
    ), "StaticDetectionFinding drifted from the dynamic DetectionFinding field set."


def test_enums_reused_by_identity_not_cloned() -> None:
    """The severity/confidence/lifecycle enums are the SAME objects as dynamic."""
    assert StaticDetectionFinding.model_fields["severity"].annotation is Severity
    assert StaticDetectionFinding.model_fields["confidence"].annotation is Confidence
    assert (
        StaticDetectionFinding.model_fields["rule_lifecycle"].annotation
        is RuleLifecycle
    )
    assert AdversaryClass in get_args(
        StaticDetectionFinding.model_fields["adversary_class"].annotation
    )


def test_static_evidence_ref_shape() -> None:
    """StaticEvidenceRef carries the artifact-location fields + v2 evidence types."""
    assert set(StaticEvidenceRef.model_fields) == {
        "type",
        "relative_path",
        "line_number",
        "snippet",
        "tool",
        "rule_match_id",
    }
    evidence_types = set(get_args(StaticEvidenceRef.model_fields["type"].annotation))
    assert {"manifest", "source_file", "binary_file"} <= evidence_types
    # v2 pre-ship — lands at ES-1 even though the MVP does not emit these.
    assert {"lockfile", "dependency"} <= evidence_types


def test_finding_rejects_non_namespaced_category() -> None:
    """Categories must use the attack.T#### / extrace.ext.* / extrace.host.* taxonomy."""
    with pytest.raises(ValidationError):
        _valid_finding(categories=["totally-made-up"])
    # MITRE technique + host namespace both accepted.
    _valid_finding(categories=["attack.T1059", "extrace.host.embedded_binary"])


def test_tool_execution_record_v2_slots_preshipped() -> None:
    """The tool Literal pre-ships the v2 yara/trivy slots alongside MVP tools."""
    tools = set(get_args(StaticToolExecutionRecord.model_fields["tool"].annotation))
    assert tools == {"inhouse", "semgrep", "yara", "trivy"}
    # db_freshness_days is optional (None for tools without a CVE DB; v2 Trivy).
    record = StaticToolExecutionRecord(
        tool="inhouse",
        version="1.0.0",
        rules_loaded=6,
        findings_emitted=1,
        duration_ms=4,
    )
    assert record.db_freshness_days is None
    assert (
        StaticToolExecutionRecord(
            tool="trivy",
            version="0.50.0",
            rules_loaded=0,
            findings_emitted=0,
            duration_ms=10,
            db_freshness_days=2,
        ).db_freshness_days
        == 2
    )


def test_severity_counts_parity_with_severity_enum() -> None:
    """StaticSeverityCounts has exactly one field per Severity tier."""
    assert set(StaticSeverityCounts.model_fields) == {s.value for s in Severity}
    assert StaticSeverityCounts().critical == 0  # defaults to zero


def test_detection_report_wrapper_composition() -> None:
    """StaticDetectionReport composes findings + tool_executions + severity_counts."""
    report = StaticDetectionReport(
        findings=[_valid_finding()],
        tool_executions=[
            StaticToolExecutionRecord(
                tool="inhouse",
                version="1.0.0",
                rules_loaded=6,
                findings_emitted=1,
                duration_ms=3,
            )
        ],
        severity_counts=StaticSeverityCounts(medium=1),
    )
    assert report.schema_version == "1"
    assert len(report.findings) == 1
    assert report.severity_counts.medium == 1
    assert report.generated_at is not None


def test_gate_decision_is_three_way() -> None:
    assert {d.value for d in StaticGateDecision} == {"allow", "warn", "block"}


def test_gate_outcome_shape_and_allow_reason_invariant() -> None:
    """allow_reason may only be set on ALLOW; WARN/BLOCK must leave it None."""
    blocked = StaticGateOutcome(
        decision=StaticGateDecision.BLOCK, blocked_by=["01J0000000000000000000000A"]
    )
    assert blocked.allow_reason is None
    assert blocked.decided_at is not None
    StaticGateOutcome(decision=StaticGateDecision.ALLOW, allow_reason="no findings")
    with pytest.raises(ValidationError):
        StaticGateOutcome(decision=StaticGateDecision.BLOCK, allow_reason="nope")


def test_combined_bundle_composition_dynamic_optional() -> None:
    """CombinedAnalysisBundle pairs a static report with an optional dynamic bundle."""
    assert set(StaticAnalysisReport.model_fields) == {
        "detection_report",
        "gate_outcome",
    }
    assert set(CombinedAnalysisBundle.model_fields) == {
        "static_report",
        "dynamic_bundle",
    }
    bundle = CombinedAnalysisBundle(
        static_report=StaticAnalysisReport(
            detection_report=StaticDetectionReport(),
            gate_outcome=StaticGateOutcome(decision=StaticGateDecision.BLOCK),
        )
    )
    # BLOCK path → dynamic stage skipped → dynamic_bundle is None.
    assert bundle.dynamic_bundle is None
