"""S9 static rule: cryptocurrency address-pattern awareness in source.

General (not sample-specific) capability detector: fires whenever an extension's
source "knows" how to recognise a crypto-wallet address — a Base58 (BTC legacy),
``0x`` + 40-hex (Ethereum), or bech32 / SegWit (``bc1``) address regex. That
awareness is the precondition for the crypto-clipper / wallet-hijack class
(``apollyon`` ``extractCryptoAddresses`` -> ``replaceCryptoAddresses`` ->
``applyEdit``): a clipper must first *find* an address before it can swap it.

This is a **capability indicator, not a verdict**. A genuine blockchain / wallet
/ Solidity extension legitimately ships these patterns, so the finding is MEDIUM
(WARN, never BLOCK): it surfaces "why does this extension understand wallet
addresses?" for review and escalation, it does not by itself call the extension
malicious. The escalation to HIGH lives in the (future) co-occurrence rule
(address scan + clipboard / file-write / network) and the dynamic clipper rule —
see ``documents/detection-design/apollyon-detection-spec.md`` (signal S2 / S6).

High-fidelity tell: the Base58 alphabet ranges exclude the visually-ambiguous
``0 O I l``, so the char-class fragments ``a-km-z`` / ``A-HJ-NP-Z`` appear almost
nowhere outside a Bitcoin-address regex. ``0x`` is required before the 40-hex
class so a bare ``[a-f0-9]{40}`` (a SHA-1 regex) does not false-positive.
"""

from __future__ import annotations

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

# The Base58 char-class fragments are the highest-fidelity sub-signal (the ranges
# that skip 0/O/I/l), so a hit on this family raises the finding's confidence.
_BASE58_LABEL = "Bitcoin Base58 address pattern"

# Each entry is (sub-signal label, compiled pattern that matches the *regex
# source text* — brackets/braces are escaped because we search for the literal
# char-class as it appears in the extension's JS/TS, not as an active regex).
_CRYPTO_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Base58 alphabet ranges (exclude 0/O/I/l). Matches both common orderings,
    # e.g. ``[a-km-zA-HJ-NP-Z1-9]`` and ``[1-9A-HJ-NP-Za-km-z]``.
    (_BASE58_LABEL, re.compile(r"a-km-z|A-HJ-NP-Z")),
    # Ethereum: ``0x`` + 40 hex. The ``0x`` prefix (optionally a capture paren)
    # disambiguates from a 40-char SHA-1 hex regex. Tolerates either hex
    # char-class ordering inside the brackets.
    (
        "Ethereum address pattern",
        re.compile(r"0[xX]\(?\[[0-9a-fA-F-]+\]\{40\}"),
    ),
    # bech32 / native SegWit awareness: a ``bc1`` prefix immediately starting a
    # regex char-class. (apollyon's own regex misses bech32 — we do not.)
    ("Bech32/SegWit address pattern", re.compile(r"bc1\[")),
)


class CryptoAddressScanRule:
    rule_id = "extrace.s9.crypto_address_scan"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension source contains cryptocurrency address patterns (Base58 / "
        "Ethereum / bech32), the address-recognition capability a crypto-clipper "
        "needs before it can hijack a wallet address."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        signals: set[str] = set()
        total_hits = 0

        for relative_path, text in iter_text_documents(context):
            for label, pattern in _CRYPTO_PATTERNS:
                for match in pattern.finditer(text):
                    signals.add(label)
                    total_hits += 1
                    self._add_evidence(
                        evidence, context, relative_path, text, match.start()
                    )

        if not signals:
            return []

        # The Base58 fragment is near-unique to crypto, so a hit there is HIGH
        # confidence; the broader hex/bech32 patterns alone stay MEDIUM.
        confidence = Confidence.HIGH if _BASE58_LABEL in signals else Confidence.MEDIUM
        listed = ", ".join(sorted(signals))
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1565", "extrace.ext.crypto_address_scan"],
                severity=self.severity,
                confidence=confidence,
                title="Extension source recognises cryptocurrency wallet addresses",
                description=(
                    f"{total_hits} cryptocurrency address pattern(s) found in the "
                    f"extension source. Pattern(s): {listed}. Address-format "
                    "awareness is a capability indicator: benign for a genuine "
                    "blockchain / wallet tool, but the precondition for a "
                    "crypto-clipper that scans for and rewrites wallet addresses. "
                    "Review against the extension's stated purpose and escalate if "
                    "it co-occurs with clipboard, file-write, or network access."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Confirm the extension is genuinely a crypto / blockchain "
                    "tool; address-pattern recognition combined with clipboard or "
                    "workspace-write access is the crypto-clipper signature."
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
                snippet=line_at(text, line_number) or "crypto address pattern",
                line_number=line_number,
            )
        )


register(CryptoAddressScanRule())

__all__ = ["CryptoAddressScanRule"]
