"""S6 static rule: source-level obfuscation indicators (ES-3a follow-on).

Data-shape heuristics that complement Semgrep's API-call rules: Semgrep flags the
``eval`` / ``Function`` call; this flags the *payload shape* feeding it and the
packing tricks that hide behaviour from static review:

* decode-then-execute — ``eval(atob(...))`` / ``Function(Buffer.from(..., 'base64'))``;
* long ``String.fromCharCode(...)`` argument chains;
* oversized inline base64 string literals;
* dense ``\\xNN`` hex-escape runs.

Each present indicator contributes a reason + first-match evidence; one MEDIUM
finding aggregates them. node_modules-style vendored bundles are not special-
cased here (the s3 size rule and Semgrep's excludes cover that axis); the intent
is to surface hand-rolled obfuscation in first-party extension code.
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
    line_number_at,
    snippet_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 25

# ``eval(`` / ``Function(`` / ``new Function(`` wrapping a decoder call.
_DECODE_EXEC_RE = re.compile(
    r"(?:eval|Function)\s*\(\s*"
    r"(?:atob|unescape|decodeURIComponent|Buffer\s*\.\s*from)\s*\(",
    re.IGNORECASE,
)
# String.fromCharCode with a long (>= 8) numeric/hex argument list.
_FROMCHARCODE_RE = re.compile(
    r"String\s*\.\s*fromCharCode\s*\(\s*"
    r"(?:0x[0-9a-f]+|\d+)\s*(?:,\s*(?:0x[0-9a-f]+|\d+)\s*){7,}\)",
    re.IGNORECASE,
)
# An inline base64 string literal of >= 200 chars (single/double quote or backtick).
_BASE64_BLOB_RE = re.compile(r"['\"`][A-Za-z0-9+/]{200,}={0,2}['\"`]")
# A dense run of >= 20 consecutive \xNN escapes.
_HEX_ESCAPE_RUN_RE = re.compile(r"(?:\\x[0-9a-fA-F]{2}){20,}")

_INDICATORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("decode-then-execute (eval/Function over a decoder)", _DECODE_EXEC_RE),
    ("long String.fromCharCode chain", _FROMCHARCODE_RE),
    ("oversized inline base64 blob", _BASE64_BLOB_RE),
    ("dense \\xNN hex-escape run", _HEX_ESCAPE_RUN_RE),
)


class ObfuscationIndicatorsRule:
    rule_id = "extrace.s6.obfuscation_indicators"
    rule_version = "1.1.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension source shows packing / obfuscation indicators (decode-then-"
        "execute, char-code chains, large base64 blobs, or hex-escape runs)."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        reasons: set[str] = set()
        strong_reasons: set[str] = set()

        for relative_path, text in iter_text_documents(context):
            for reason, pattern in _INDICATORS:
                match = pattern.search(text)
                if match is None:
                    continue
                reasons.add(reason)
                if pattern in {_DECODE_EXEC_RE, _FROMCHARCODE_RE}:
                    strong_reasons.add(reason)
                if len(evidence) >= _MAX_EVIDENCE:
                    continue
                line_number = line_number_at(text, match.start())
                evidence.append(
                    file_evidence(
                        relative_path,
                        evidence_type_for(context, relative_path),
                        snippet=snippet_at(text, match.start()) or reason,
                        line_number=line_number,
                    )
                )

        if not reasons:
            return []

        severity = Severity.MEDIUM if strong_reasons else Severity.INFO
        confidence = (
            Confidence.HIGH
            if "decode-then-execute (eval/Function over a decoder)" in strong_reasons
            else Confidence.MEDIUM
            if strong_reasons
            else Confidence.LOW
        )

        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1027", "extrace.ext.obfuscation"],
                severity=severity,
                confidence=confidence,
                title="Extension source shows obfuscation indicators",
                description=(
                    "Obfuscation / packing indicators found in the extension "
                    f"source: {'; '.join(sorted(reasons))}. Decode/execute or "
                    "long generated char-code chains are warnable; standalone "
                    "base64/hex data is informational because normal bundles "
                    "also contain these shapes."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "De-obfuscate and inspect the flagged code; decode-then-execute "
                    "and packed payloads are used to smuggle behaviour past review."
                ),
            )
        ]


register(ObfuscationIndicatorsRule())

__all__ = ["ObfuscationIndicatorsRule"]
