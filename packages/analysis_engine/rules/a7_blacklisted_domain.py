"""A7 detection rule: outbound connection to a blacklisted domain (blacklist_domains).

The live-traffic leg of the ``blacklist_domains`` feature. Every outbound network
event's observed ``host`` is checked against the operator denylist
(``packages.analysis_contracts.data.blacklist_domains.txt``) via the shared
``domain_indicators.match_host`` matcher — the same curated list the static
``extrace.s4.blacklisted_domain`` rule scans the source for. Where s4 catches a
hardcoded reference, a7 catches the connection actually happening at runtime.

Severity HIGH so the verdict rollup surfaces it as a strong warning; it is not a
gate blocker (the static gate owns block-and-warn — this rule rides the dynamic
verdict path like the other a-rules).
"""

from __future__ import annotations

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    EvidenceRef,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.domain_indicators import match_host
from packages.analysis_engine.rules._common import (
    make_evidence_ref,
    outbound_network_events,
)
from packages.analysis_engine.rules.registry import register

# Cap the evidence refs a single finding carries; the count of distinct
# blacklisted hosts is still reported in the description when more match.
_MAX_EVIDENCE = 5


class BlacklistedDomainRule:
    rule_id = "extrace.a7.blacklisted_domain"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A7
    severity = Severity.HIGH
    description = (
        "The extension opened an outbound connection to a domain on the operator "
        "blacklist (a known C2 / malware-staging / exfiltration endpoint)."
    )

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        evidence: list[EvidenceRef] = []
        matched: dict[str, str] = {}  # observed host -> blacklisted domain
        for event in outbound_network_events(report):
            domain = match_host(event.host)
            if domain is None:
                continue
            matched.setdefault(event.host, domain)
            if len(evidence) < _MAX_EVIDENCE:
                evidence.append(make_evidence_ref(event))

        if not matched:
            return []

        domains = ", ".join(sorted(set(matched.values())))
        hosts = ", ".join(sorted(matched))
        return [
            DetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1071", "extrace.host.blacklisted_domain"],
                severity=self.severity,
                confidence=Confidence.HIGH,
                title="Outbound connection to a blacklisted domain",
                description=(
                    f"The extension contacted blacklisted domain(s) {domains} "
                    f"(observed host(s): {hosts}). These domains are on the "
                    "operator denylist of known-malicious endpoints."
                ),
                evidence=evidence,
                adversary_class=self.adversary_class,
                mitigation_hint=(
                    "Block the connection and treat the extension as malicious; "
                    "contact with a known-bad domain is a direct command-and-"
                    "control / exfiltration signal."
                ),
            )
        ]


RULE = BlacklistedDomainRule()
register(RULE)

__all__ = ["RULE", "BlacklistedDomainRule"]
