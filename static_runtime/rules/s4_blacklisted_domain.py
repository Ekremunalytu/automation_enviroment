"""S4 static rule: extension references a blacklisted domain (blacklist_domains).

The static leg of the ``blacklist_domains`` feature. Scans the decompressed
extension's text/source files (the manifest included) for any hardcoded
reference to a domain on the operator denylist
(``packages.analysis_contracts.data.blacklist_domains.txt``). A hit is a strong
indicator of C2 / malware-staging / exfiltration wired straight into the source.

Counterpart of the dynamic ``extrace.a7.blacklisted_domain`` rule, which checks
the same denylist against hosts *observed* in live traffic. Both share the
single matcher in ``packages.analysis_contracts.domain_indicators`` so the static
image needs no dynamic-engine import.

Emits at most one finding carrying up to ``_MAX_EVIDENCE`` refs; when more files
match, the total is reported in the description rather than silently truncated.
Severity HIGH → the gate raises a WARN (it is deliberately not a promoted
blocker, so the dynamic stage still runs and the warning rides along).
"""

from __future__ import annotations

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.domain_indicators import find_in_text
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticEvidenceRef,
)
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import (
    evidence_type_for,
    file_evidence,
    iter_text_documents,
    line_at,
    line_number_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 25


class BlacklistedDomainRule:
    rule_id = "extrace.s4.blacklisted_domain"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.HIGH
    description = (
        "Extension source or manifest references a domain on the operator "
        "blacklist (a known C2 / malware-staging / exfiltration endpoint)."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        matched_domains: set[str] = set()
        total_hits = 0

        for relative_path, text in iter_text_documents(context):
            domains = find_in_text(text)
            if not domains:
                continue
            lowered = text.lower()
            for domain in domains:
                matched_domains.add(domain)
                total_hits += 1
                if len(evidence) >= _MAX_EVIDENCE:
                    continue
                index = lowered.find(domain)
                line_number = line_number_at(text, index) if index >= 0 else None
                snippet = line_at(text, line_number) if line_number else domain
                evidence.append(
                    file_evidence(
                        relative_path,
                        evidence_type_for(context, relative_path),
                        snippet=snippet or domain,
                        line_number=line_number,
                    )
                )

        if not matched_domains:
            return []

        shown = ", ".join(sorted(matched_domains))
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1071", "extrace.ext.blacklisted_domain"],
                severity=self.severity,
                confidence=Confidence.HIGH,
                title="Extension references a blacklisted domain",
                description=(
                    f"{total_hits} reference(s) to blacklisted domain(s) found in "
                    f"the extension: {shown}. These domains are on the operator "
                    "denylist of known-malicious endpoints."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Treat the extension as malicious pending review; a hardcoded "
                    "reference to a known-bad domain is a strong indicator of "
                    "command-and-control or data exfiltration."
                ),
            )
        ]


register(BlacklistedDomainRule())

__all__ = ["BlacklistedDomainRule"]
