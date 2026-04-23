"""A3 detection rule: publisher.name impersonates a popular extension."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from packages.analysis_contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    EvidenceRef,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import event_type, make_evidence_ref
from packages.analysis_engine.rules.registry import register

_POPULAR_EXTENSION_PATH = (
    Path(__file__).resolve().parents[1] / "allowlists" / "popular_extensions.txt"
)
_MAX_TYPOSQUAT_DISTANCE = 2


@lru_cache(maxsize=1)
def _popular_extensions() -> frozenset[str]:
    lines = _POPULAR_EXTENSION_PATH.read_text(encoding="utf-8").splitlines()
    values = {line.strip().lower() for line in lines if line.strip()}
    return frozenset(values)


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            substitution_cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def _nearest_popular_match(identifier: str) -> tuple[str, int] | None:
    """Return the closest popular extension within the typosquat bound."""

    best: tuple[str, int] | None = None
    for candidate in _popular_extensions():
        distance = _levenshtein(identifier, candidate)
        if distance == 0:
            return None
        if distance > _MAX_TYPOSQUAT_DISTANCE:
            continue
        if best is None or distance < best[1]:
            best = (candidate, distance)
    return best


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
