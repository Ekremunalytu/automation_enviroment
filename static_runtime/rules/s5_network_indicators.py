"""S5 static rule: suspicious hardcoded network endpoints (ES-3a follow-on).

Generic network-IoC heuristics over the extension source, complementary to the
blacklist (s4) and to Semgrep's API-call rules:

* a routable IPv4 literal endpoint (``http://203.0.113.4`` / ``198.51.100.7:8443``)
  — a real extension talks to named services, so a hardcoded public-IP target is
  a classic C2 / staging shape;
* a cleartext ``http://`` URL to an external host — exfiltration and payload
  fetches frequently skip TLS.

Loopback / private / link-local / reserved IPs (``ipaddress.is_global`` is the
truth source, so RFC 5737 documentation ranges are excluded) and reserved test
TLDs (``.example`` / ``.test`` / ``.invalid`` / ``.local`` / ``localhost``) are
ignored to keep the rule high-signal. One MEDIUM finding aggregates the hits.
"""

from __future__ import annotations

import ipaddress
import re

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
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

# A dotted-quad inside a URL or as an explicit host:port connect target.
_IP_ENDPOINT_RE = re.compile(
    r"\b(?:https?://)?(\d{1,3}(?:\.\d{1,3}){3})(?::\d{2,5})?\b"
)
# A cleartext http:// URL host (captured up to the first path/port/quote char).
_CLEARTEXT_HTTP_RE = re.compile(r"\bhttp://([a-z0-9.\-]+\.[a-z]{2,})", re.IGNORECASE)

# Host suffixes intrinsically not worth flagging (reserved / loopback names).
_IGNORED_HOST_SUFFIXES = (
    ".example",
    ".test",
    ".invalid",
    ".local",
    ".localhost",
)
_IGNORED_HOSTS = frozenset({"localhost"})


def _is_routable_ipv4(candidate: str) -> bool:
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return isinstance(address, ipaddress.IPv4Address) and address.is_global


def _is_flaggable_http_host(host: str) -> bool:
    lowered = host.lower()
    if lowered in _IGNORED_HOSTS:
        return False
    if any(lowered == suffix.lstrip(".") for suffix in _IGNORED_HOST_SUFFIXES):
        return False
    if any(lowered.endswith(suffix) for suffix in _IGNORED_HOST_SUFFIXES):
        return False
    # A bare IPv4 host is covered by the IP-endpoint pass; skip it here.
    return not _is_routable_ipv4(lowered)


class SuspiciousNetworkEndpointRule:
    rule_id = "extrace.s5.suspicious_network_endpoint"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension source hardcodes a suspicious network endpoint (a routable "
        "public-IP literal and/or a cleartext http:// external host)."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        reasons: set[str] = set()
        total_hits = 0

        for relative_path, text in iter_text_documents(context):
            for match in _IP_ENDPOINT_RE.finditer(text):
                if not _is_routable_ipv4(match.group(1)):
                    continue
                reasons.add("routable IPv4 endpoint")
                total_hits += 1
                self._add_evidence(
                    evidence, context, relative_path, text, match.start()
                )
            for match in _CLEARTEXT_HTTP_RE.finditer(text):
                if not _is_flaggable_http_host(match.group(1)):
                    continue
                reasons.add("cleartext http:// external host")
                total_hits += 1
                self._add_evidence(
                    evidence, context, relative_path, text, match.start()
                )

        if not reasons:
            return []

        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1071", "extrace.ext.network_indicator"],
                severity=self.severity,
                confidence=Confidence.LOW,
                title="Extension hardcodes a suspicious network endpoint",
                description=(
                    f"{total_hits} suspicious network endpoint(s) found in the "
                    f"extension source. Signals: {'; '.join(sorted(reasons))}. "
                    "Hardcoded public-IP targets and cleartext transports are "
                    "common shapes for command-and-control and exfiltration."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Confirm why the extension contacts a raw IP or an unencrypted "
                    "endpoint; legitimate extensions use named services over TLS."
                ),
            )
        ]

    @staticmethod
    def _add_evidence(
        evidence: list[StaticEvidenceRef],
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        index: int,
    ) -> None:
        if len(evidence) >= _MAX_EVIDENCE:
            return
        line_number = line_number_at(text, index)
        evidence.append(
            file_evidence(
                relative_path,
                evidence_type_for(context, relative_path),
                snippet=line_at(text, line_number) or "network endpoint",
                line_number=line_number,
            )
        )


register(SuspiciousNetworkEndpointRule())

__all__ = ["SuspiciousNetworkEndpointRule"]
