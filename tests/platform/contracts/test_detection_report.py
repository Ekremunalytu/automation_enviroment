from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    DetectionReport,
    EvidenceRef,
    ExtensionIdentity,
    RuleExecutionRecord,
    RuleExecutionStatus,
    RuleLifecycle,
    Severity,
    Verdict,
)


def test_detection_report_round_trip_serialization() -> None:
    finding = DetectionFinding(
        rule_id="extrace.a1.credential_read_then_network",
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["attack.T1555", "attack.T1041"],
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        title="Credential read followed by outbound HTTPS",
        description="The extension read a sensitive credential file, then sent data out.",
        evidence=[
            EvidenceRef(
                type="filesystem_read",
                event_id="file-0001",
                summary="Read ~/.ssh/id_rsa",
                path="~/.ssh/id_rsa",
            ),
            EvidenceRef(
                type="network_request",
                event_id="network-0002",
                summary="POST to collector",
                host="collector.example.invalid",
                method="POST",
            ),
        ],
        adversary_class=AdversaryClass.A1,
        mitigation_hint="Review outbound network destinations and remove the extension.",
    )
    report = DetectionReport(
        activation_report_ref="activation_report_extrace.fixture.json",
        analyzed_extension=ExtensionIdentity(
            publisher="extrace",
            name="fixture-malicious",
            version="0.0.1",
        ),
        findings=[finding],
        verdict=Verdict.MALICIOUS,
        verdict_rationale="critical finding with high confidence",
        rules_executed=[
            RuleExecutionRecord(
                rule_id=finding.rule_id,
                rule_version=finding.rule_version,
                lifecycle=RuleLifecycle.PRODUCTION,
                status=RuleExecutionStatus.FIRED,
                finding_ids=[finding.id],
            )
        ],
        generated_at=datetime(2026, 4, 20, 10, 0, tzinfo=UTC),
    )

    payload = report.model_dump(mode="json")
    parsed = DetectionReport.model_validate(payload)

    assert parsed == report
    assert payload["schema_version"] == "1"
    assert payload["findings"][0]["id"]
    assert payload["rules_executed"][0]["status"] == "fired"


def test_detection_categories_use_approved_namespaces_only() -> None:
    with pytest.raises(ValidationError) as exc:
        DetectionFinding(
            rule_id="extrace.invalid.rule",
            rule_version="1.0.0",
            rule_lifecycle=RuleLifecycle.PRODUCTION,
            categories=["custom.namespace.bad"],
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            title="Bad category",
            description="This should fail validation.",
            evidence=[],
        )

    assert "Detection categories must use" in str(exc.value)


def test_detection_finding_generates_ulid_by_default() -> None:
    finding = DetectionFinding(
        rule_id="extrace.ext.info_only",
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.DRAFT,
        categories=["extrace.ext.startup_ui_prompt"],
        severity=Severity.INFO,
        confidence=Confidence.LOW,
        title="Info finding",
        description="No malicious behavior observed.",
        evidence=[],
    )

    assert len(finding.id) == 26
    assert finding.id.isupper()


def test_detection_enums_preserve_string_semantics() -> None:
    assert str(Severity.CRITICAL) == "critical"
    assert Severity.CRITICAL == "critical"
    assert str(Verdict.MALICIOUS) == "malicious"
