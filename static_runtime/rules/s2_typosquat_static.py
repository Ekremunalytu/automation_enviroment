"""S2 static rule: manifest identity impersonates a popular extension (ES-3a).

Static counterpart of the dynamic ``extrace.a3.typosquat`` rule. Where the
dynamic rule reads ``target_extension_expected`` off an ActivationReport, this
reads ``publisher`` + ``name`` straight off the manifest and reuses the shared
``packages.analysis_contracts.typosquat_match`` matcher (single allowlist, no
dynamic-engine import). This is the sole HIGH severity finding promoted to a
gate BLOCK at ES-3b (``_PROMOTED_HIGH_BLOCKERS``).
"""

from __future__ import annotations

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import StaticDetectionFinding
from packages.analysis_contracts.typosquat_match import nearest_popular_match
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import manifest_evidence, manifest_string
from static_runtime.rules.registry import register


class StaticTyposquatRule:
    rule_id = "extrace.s2.typosquat"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A3
    severity = Severity.HIGH
    description = (
        "Extension publisher.name is a small edit away from a popular "
        "marketplace extension, matching the typosquat impersonation pattern."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        if context.manifest_relative_path is None:
            return []
        publisher = manifest_string(context.manifest, "publisher")
        name = manifest_string(context.manifest, "name")
        if not publisher or not name:
            return []
        identifier = f"{publisher}.{name}".lower()

        match = nearest_popular_match(identifier)
        if match is None:
            return []
        popular_id, distance = match

        return [
            StaticDetectionFinding(
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
                    "matches the typosquat impersonation pattern used to trick "
                    "users into installing a lookalike extension."
                ),
                evidence=[
                    manifest_evidence(
                        context, f'"publisher": "{publisher}", "name": "{name}"'
                    )
                ],
                adversary_class=self.adversary_class,
                mitigation_hint=(
                    "Block the extension, confirm whether users meant to install "
                    f"{popular_id!r}, and escalate to marketplace takedown if "
                    "impersonation is confirmed."
                ),
            )
        ]


register(StaticTyposquatRule())

__all__ = ["StaticTyposquatRule"]
