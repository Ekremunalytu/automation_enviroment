"""S12 static rule: invisible Unicode / PUA source-hiding runs.

GlassWorm-style source steganography uses invisible Unicode, variation
selectors, or Private Use Area codepoints to hide logic in source bytes. A
single codepoint can be accidental, but a contiguous run is a high-confidence
defense-evasion signal, so this rule scans the original packaged bytes instead
of a normalized or rendered source copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    is_text_document,
    line_number_at,
)
from static_runtime.rules.registry import register

_MAX_SCAN_BYTES = 1024 * 1024
_MAX_EVIDENCE = 25
_RUN_THRESHOLD = 3

_INVISIBLE_RANGES: tuple[tuple[int, int], ...] = (
    (0x00AD, 0x00AD),
    (0x180E, 0x180E),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x2064),
    (0x2066, 0x2069),
    (0xFE00, 0xFE0F),
    (0xFEFF, 0xFEFF),
    (0xE000, 0xF8FF),
    (0xE0000, 0xE007F),
    (0xE0100, 0xE01EF),
    (0xF0000, 0xFFFFD),
    (0x100000, 0x10FFFD),
)


@dataclass(frozen=True, slots=True)
class _UnicodeScan:
    total_hits: int
    max_run: int
    first_index: int | None
    first_codepoints: tuple[str, ...]


def _is_invisible_or_pua(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _INVISIBLE_RANGES)


def _read_source_bytes(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            raw = handle.read(_MAX_SCAN_BYTES)
    except OSError:
        return ""
    return raw.decode("utf-8", "replace")


def _scan_text(text: str) -> _UnicodeScan:
    total_hits = 0
    current_run = 0
    max_run = 0
    first_index: int | None = None
    first_codepoints: list[str] = []

    for index, character in enumerate(text):
        if not _is_invisible_or_pua(character):
            current_run = 0
            continue

        total_hits += 1
        current_run += 1
        max_run = max(max_run, current_run)
        if first_index is None:
            first_index = index
        if len(first_codepoints) < 8:
            first_codepoints.append(f"U+{ord(character):04X}")

    return _UnicodeScan(
        total_hits=total_hits,
        max_run=max_run,
        first_index=first_index,
        first_codepoints=tuple(first_codepoints),
    )


class InvisibleUnicodeRunRule:
    rule_id = "extrace.s12.invisible_unicode_run"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.CRITICAL
    description = (
        "Extension source contains invisible Unicode / PUA codepoints; contiguous "
        "runs are a source-hiding technique used by malicious VS Code extensions."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        files_with_hits = 0
        total_hits = 0
        max_run = 0

        for relative_path, absolute_path in context.iter_files():
            if not is_text_document(relative_path):
                continue
            text = _read_source_bytes(absolute_path)
            if not text:
                continue
            scan = _scan_text(text)
            if scan.total_hits == 0:
                continue

            files_with_hits += 1
            total_hits += scan.total_hits
            max_run = max(max_run, scan.max_run)
            if len(evidence) >= _MAX_EVIDENCE:
                continue

            line_number = (
                line_number_at(text, scan.first_index)
                if scan.first_index is not None
                else None
            )
            codepoints = ", ".join(scan.first_codepoints)
            evidence.append(
                file_evidence(
                    relative_path,
                    evidence_type_for(context, relative_path),
                    snippet=(
                        f"{scan.total_hits} suspicious codepoint(s); "
                        f"max contiguous run={scan.max_run}; sample={codepoints}"
                    ),
                    line_number=line_number,
                )
            )

        if total_hits == 0:
            return []

        uc2 = max_run >= _RUN_THRESHOLD
        severity = Severity.CRITICAL if uc2 else Severity.LOW
        confidence = Confidence.HIGH if uc2 else Confidence.MEDIUM
        title = (
            "Source contains an invisible Unicode run"
            if uc2
            else "Source contains suspicious invisible Unicode"
        )
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1027", "extrace.ext.source_steganography"],
                severity=severity,
                confidence=confidence,
                title=title,
                description=(
                    f"{total_hits} invisible Unicode / PUA codepoint(s) found "
                    f"across {files_with_hits} text/source file(s); maximum "
                    f"contiguous run is {max_run}. Runs of {_RUN_THRESHOLD}+ "
                    "codepoints are treated as malicious source hiding because "
                    "normal JS/TS source should not contain invisible payload "
                    "streams."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Inspect the original packaged bytes and reject source that "
                    "hides logic in invisible Unicode or PUA codepoint runs."
                ),
            )
        ]


register(InvisibleUnicodeRunRule())

__all__ = ["InvisibleUnicodeRunRule"]
