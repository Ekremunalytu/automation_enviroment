"""A4 detection rule: workspace file access followed by exfiltration."""

from __future__ import annotations

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import (
    event_method,
    event_type,
    file_events,
    make_evidence_ref,
    rel_time,
    unknown_outbound_network_events,
)
from packages.analysis_engine.rules.registry import register


class WorkspaceExfilRule:
    rule_id = "extrace.a4.workspace_exfil"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A4
    severity = Severity.HIGH
    description = "Workspace file reads followed by outbound exfiltration."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        workspace_reads = [
            event
            for event in file_events(report)
            if event.operation.strip().lower() == "read"
            and event.path.startswith("/workspace/")
        ]
        outbound_events = [
            event
            for event in unknown_outbound_network_events(report)
            if event_type(event) == "tls_sni" or event_method(event) == "POST"
        ]

        findings: list[DetectionFinding] = []
        for file_event in workspace_reads:
            for network_event in outbound_events:
                if 0 <= rel_time(network_event) - rel_time(file_event) <= 30:
                    findings.append(
                        DetectionFinding(
                            rule_id=self.rule_id,
                            rule_version=self.rule_version,
                            rule_lifecycle=self.lifecycle,
                            categories=["attack.T1041", "extrace.host.workspace_exfil"],
                            severity=self.severity,
                            confidence=Confidence.MEDIUM,
                            title="Workspace file read followed by outbound transfer",
                            description=(
                                "The extension read data from the workspace and "
                                "contacted a non-benign external host soon after."
                            ),
                            evidence=[
                                make_evidence_ref(file_event),
                                make_evidence_ref(network_event),
                            ],
                            adversary_class=self.adversary_class,
                            mitigation_hint=(
                                "Review workspace access scope and block the "
                                "observed outbound destination."
                            ),
                        )
                    )
                    break
        return findings


RULE = WorkspaceExfilRule()
register(RULE)

__all__ = ["RULE", "WorkspaceExfilRule"]
