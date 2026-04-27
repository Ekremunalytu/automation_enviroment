"""Demo-only detection rule for the runnable T1 canary extension."""

from __future__ import annotations

from packages.analysis_contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import make_evidence_ref
from packages.analysis_engine.rules.registry import register

_DEMO_EXTENSION_ID = "extrace.t1-demo-runnable-canary"
_DEMO_COMMAND_EVENT = "onCommand:extraceDemo.runSafeSimulation"


def _target_demo_activation(report: ActivationReport) -> EvidenceEvent | None:
    for event in report.evidence_events:
        if event.extension_id != _DEMO_EXTENSION_ID:
            continue
        if event.activation_event == _DEMO_COMMAND_EVENT:
            return event
        if _DEMO_EXTENSION_ID in event.summary and _DEMO_COMMAND_EVENT in event.summary:
            return event
    return None


def _verified_demo_attempt(report: ActivationReport) -> bool:
    for attempt in report.event_attempts:
        if attempt.event_value != "extraceDemo.runSafeSimulation":
            continue
        if attempt.status in {"verified", "target_log_seen", "activation_seen"}:
            return True
    return False


class DemoRunnableCanaryRule:
    rule_id = "extrace.demo.runnable_canary"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A1
    severity = Severity.CRITICAL
    description = "Controlled runnable demo canary was explicitly triggered."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        if report.target_extension_expected != _DEMO_EXTENSION_ID:
            return []

        activation_event = _target_demo_activation(report)
        if activation_event is None or not _verified_demo_attempt(report):
            return []

        return [
            DetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["extrace.ext.demo_canary"],
                severity=self.severity,
                confidence=Confidence.HIGH,
                title="Runnable malicious-behavior demo canary executed",
                description=(
                    "The controlled ExTrace demo extension was triggered through "
                    "its explicit simulation command. This is a demo-only canary "
                    "finding, not evidence of a real external attack."
                ),
                evidence=[make_evidence_ref(activation_event)],
                adversary_class=self.adversary_class,
                mitigation_hint=(
                    "Use this finding only to verify demo/report plumbing; do "
                    "not treat the fixture as a real-world malicious sample."
                ),
            )
        ]


RULE = DemoRunnableCanaryRule()
register(RULE)

__all__ = ["RULE", "DemoRunnableCanaryRule"]
