"""A1 detection rule: credential file read followed by outbound network."""

from __future__ import annotations

import re

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import (
    event_type,
    file_events,
    make_evidence_ref,
    rel_time,
    unknown_outbound_network_events,
)
from packages.analysis_engine.rules.registry import register

_CREDENTIAL_PATH_PATTERN = re.compile(r"(^|/)(\.ssh/|\.aws/|\.config/gh/|\.netrc$)")


class CredentialReadThenNetworkRule:
    rule_id = "extrace.a1.credential_read_then_network"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A1
    severity = Severity.CRITICAL
    description = "Sensitive credential file access followed by outbound network."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        candidate_files = [
            event
            for event in file_events(report)
            if event.operation.strip().lower() == "read"
            and _CREDENTIAL_PATH_PATTERN.search(event.path)
        ]
        candidate_network = [
            event
            for event in unknown_outbound_network_events(report)
            if event_type(event) in {"http_request", "tls_sni"}
        ]

        findings: list[DetectionFinding] = []
        for file_event in candidate_files:
            for network_event in candidate_network:
                if abs(rel_time(network_event) - rel_time(file_event)) > 60:
                    continue
                findings.append(
                    DetectionFinding(
                        rule_id=self.rule_id,
                        rule_version=self.rule_version,
                        rule_lifecycle=self.lifecycle,
                        categories=["attack.T1555", "attack.T1041"],
                        severity=self.severity,
                        confidence=Confidence.HIGH,
                        title="Credential file read followed by outbound request",
                        description=(
                            "The extension read a credential-bearing path and "
                            "contacted a non-benign external host within the "
                            "same activation window."
                        ),
                        evidence=[
                            make_evidence_ref(file_event),
                            make_evidence_ref(network_event),
                        ],
                        adversary_class=self.adversary_class,
                        mitigation_hint=(
                            "Remove the extension and rotate any credentials "
                            "reachable from the affected path."
                        ),
                    )
                )
                break
        return findings


RULE = CredentialReadThenNetworkRule()
register(RULE)

__all__ = ["RULE", "CredentialReadThenNetworkRule"]
