"""A2 detection rule: bursty beaconing immediately after activation."""

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
    activation_time,
    event_type,
    make_evidence_ref,
    rel_time,
    unknown_outbound_network_events,
)
from packages.analysis_engine.rules.registry import register


class StartupNetworkBeaconRule:
    rule_id = "extrace.a2.startup_network_beacon"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A2
    severity = Severity.HIGH
    description = "Repeated startup-time beaconing consistent with miner staging."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        activated_at = activation_time(report)
        if activated_at is None:
            return []

        outbound_tls_events = [
            event
            for event in unknown_outbound_network_events(report)
            if event_type(event) == "tls_sni"
            and 0 <= rel_time(event) - activated_at <= 10
        ]
        outbound_tls_events.sort(key=rel_time)
        early_burst = [
            event
            for event in outbound_tls_events
            if 0 <= rel_time(event) - activated_at <= 3
        ]
        if len(early_burst) < 2 or len(outbound_tls_events) < 4:
            return []

        deltas = [
            rel_time(outbound_tls_events[index + 1])
            - rel_time(outbound_tls_events[index])
            for index in range(len(outbound_tls_events) - 1)
        ]
        short_delta_count = sum(1 for delta in deltas if delta < 5)
        if short_delta_count < 3:
            return []

        return [
            DetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1496", "extrace.host.startup_beacon"],
                severity=self.severity,
                confidence=Confidence.MEDIUM,
                title="Startup-time outbound beacon burst",
                description=(
                    "The extension opened repeated outbound TLS sessions "
                    "immediately after activation, matching a beaconing cadence "
                    "associated with miner bootstrap activity."
                ),
                evidence=[
                    make_evidence_ref(event) for event in outbound_tls_events[:4]
                ],
                adversary_class=self.adversary_class,
                mitigation_hint=(
                    "Inspect post-install startup behavior and block repeated "
                    "connections to the external host."
                ),
            )
        ]


RULE = StartupNetworkBeaconRule()
register(RULE)

__all__ = ["RULE", "StartupNetworkBeaconRule"]
