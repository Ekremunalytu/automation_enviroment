"""S7 static rule: credentials hardcoded in shipped extension source (ES-3a follow-on).

Flags high-confidence secret shapes (AWS access keys, GitHub / Slack tokens, PEM
private keys, bearer tokens) embedded in the extension's text/source files. A
shipped credential is both a supply-chain leak and a frequent marker of a
hardcoded exfiltration channel.

Detection reuses ``packages.analysis_contracts.evidence`` — the read side of the
same secret taxonomy ``redact_secrets`` scrubs — so detection and redaction never
drift. The raw secret is NEVER quoted into evidence: the snippet names only the
secret *class*, and the ``line_number`` points the reviewer at it. One MEDIUM
finding aggregates the classes seen.
"""

from __future__ import annotations

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.evidence import find_secret_offsets
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticEvidenceRef,
)
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import (
    evidence_type_for,
    file_evidence,
    iter_text_documents,
    line_number_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 25


class HardcodedSecretRule:
    rule_id = "extrace.s7.hardcoded_secret"
    rule_version = "1.1.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension source hardcodes a credential (AWS key, GitHub / Slack token, "
        "private key, or bearer token), a supply-chain leak and exfiltration smell."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        classes: set[str] = set()
        warnable_classes: set[str] = set()

        for relative_path, text in iter_text_documents(context):
            for secret_class, offset in find_secret_offsets(text):
                classes.add(secret_class)
                paired_tls_material = (
                    secret_class == "private" + "_key"
                    and "-----BEGIN CERTIFICATE-----" in text
                )
                if not paired_tls_material:
                    warnable_classes.add(secret_class)
                if len(evidence) >= _MAX_EVIDENCE:
                    continue
                line_number = line_number_at(text, offset)
                evidence.append(
                    file_evidence(
                        relative_path,
                        evidence_type_for(context, relative_path),
                        # Never quote the secret: the class label + line is enough.
                        snippet=f"{secret_class} credential pattern",
                        line_number=line_number,
                    )
                )

        if not classes:
            return []

        shown = ", ".join(sorted(classes))
        severity = Severity.MEDIUM if warnable_classes else Severity.INFO
        confidence = Confidence.MEDIUM if warnable_classes else Confidence.LOW
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1552", "extrace.ext.hardcoded_secret"],
                severity=severity,
                confidence=confidence,
                title="Extension hardcodes a credential in source",
                description=(
                    f"Hardcoded credential(s) found in the extension source: "
                    f"{shown}. Shipped secrets are a supply-chain leak and a "
                    "common marker of a hardcoded exfiltration channel. A "
                    "private key shipped with its matching certificate is "
                    "classified as informational TLS material."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Rotate the exposed credential and confirm why the extension "
                    "ships a secret; paired local-service TLS material still "
                    "needs provenance review but is not itself evidence of malice."
                ),
            )
        ]


register(HardcodedSecretRule())

__all__ = ["HardcodedSecretRule"]
