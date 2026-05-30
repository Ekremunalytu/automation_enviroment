"""A3 detection rule: publisher.name impersonates a popular extension."""

from __future__ import annotations

from packages.analysis_contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    EvidenceRef,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.typosquat_match import nearest_popular_match
from packages.analysis_engine.rules._common import event_type, make_evidence_ref
from packages.analysis_engine.rules.registry import register

# Typosquat matching primitives moved to packages.analysis_contracts at ES-3a so
# the hardened static image can share the matcher + allowlist without dragging in
# the dynamic engine. Behaviour is unchanged; the static s2 rule imports the same
# helper. See packages/analysis_contracts/typosquat_match.py.
_nearest_popular_match = nearest_popular_match


def _activation_evidence(report: ActivationReport) -> EvidenceEvent | None:
    for event in report.evidence_events:
        kind = event.kind.strip().lower()
        if kind not in {"extension_host", "activation"}:
            continue
        summary = event.summary.strip().lower()
        if event_type(event) == "activated" or "activated" in summary:
            return event
    return None


class TyposquatRule:
    rule_id = "extrace.a3.typosquat"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A3
    severity = Severity.HIGH
    description = (
        "Extension publisher.name is a small edit away from a popular "
        "marketplace extension, matching the typosquat impersonation pattern."
    )

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        identifier = (report.target_extension_expected or "").strip().lower()
        if not identifier or "." not in identifier:
            return []

        match = _nearest_popular_match(identifier)
        if match is None:
            return []
        popular_id, distance = match

        activation_event = _activation_evidence(report)
        if activation_event is not None:
            evidence = [make_evidence_ref(activation_event)]
        else:
            evidence = [
                EvidenceRef(
                    type="extension_identity",
                    event_id=f"identity:{identifier}",
                    summary=f"target_extension_expected={identifier}",
                )
            ]

        return [
            DetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1036", "extrace.ext.typosquat"],
                severity=self.severity,
                confidence=Confidence.MEDIUM,
                title="Extension identifier impersonates a popular extension",
                description=(
                    f"Identifier {identifier!r} is within Levenshtein distance "
                    f"{distance} of the popular extension {popular_id!r}. This "
                    "matches the A3 impersonation pattern used to trick users "
                    "into installing a lookalike extension."
                ),
                evidence=evidence,
                adversary_class=self.adversary_class,
                mitigation_hint=(
                    "Block the extension, confirm whether users meant to install "
                    f"{popular_id!r}, and escalate to marketplace takedown if "
                    "impersonation is confirmed."
                ),
            )
        ]


RULE = TyposquatRule()
register(RULE)

__all__ = ["RULE", "TyposquatRule"]
