"""Conservative SAP-5 source-map and vendor finding deduplication."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from packages.analysis_contracts.static_detection import (
    StaticArtifactInventoryEntry,
    StaticDetectionFinding,
    StaticEvidenceRef,
    StaticFindingDeduplicationReason,
    StaticFindingDeduplicationRecord,
)
from static_runtime.context import StaticAnalysisContext

MAX_SOURCE_MAP_ENTRIES = 1_024


@dataclass(frozen=True, slots=True)
class FindingDeduplicationResult:
    findings: tuple[StaticDetectionFinding, ...]
    records: tuple[StaticFindingDeduplicationRecord, ...]


def _finding_identity(finding: StaticDetectionFinding) -> tuple[object, ...]:
    return (
        finding.rule_id,
        finding.rule_version,
        finding.rule_lifecycle.value,
        tuple(finding.categories),
        finding.severity.value,
        finding.confidence.value,
        finding.title,
        finding.description,
        finding.adversary_class.value if finding.adversary_class else None,
        finding.mitigation_hint,
    )


def _evidence_shape(evidence: StaticEvidenceRef) -> tuple[object, ...]:
    return (
        evidence.type,
        evidence.line_number,
        evidence.snippet,
        evidence.tool,
        evidence.rule_match_id,
    )


def _canonical_rank(
    finding: StaticDetectionFinding,
    inventory: dict[str, StaticArtifactInventoryEntry],
) -> tuple[object, ...]:
    evidence = finding.evidence[0] if finding.evidence else None
    path = evidence.relative_path if evidence else "~"
    entry = inventory.get(path)
    if entry is None:
        reachability_rank = 5
        artifact_rank = 5
    else:
        reachability_rank = {
            "direct": 0,
            "transitive": 1 if entry.reachability_confidence == "literal" else 2,
            "none": 3,
            "unknown": 4,
        }[entry.entrypoint_reachability]
        artifact_rank = (
            int(entry.role == "source_map") * 4
            + int(entry.is_vendor) * 2
            + int(entry.is_minified)
        )
    return (
        reachability_rank,
        artifact_rank,
        finding.rule_id,
        finding.rule_version,
        path,
        evidence.line_number if evidence and evidence.line_number else 0,
        evidence.snippet if evidence and evidence.snippet else "",
    )


def _read_bytes(
    root: Path,
    relative_path: str,
    *,
    max_file_bytes: int,
    cache: dict[str, bytes | None],
) -> bytes | None:
    if relative_path in cache:
        return cache[relative_path]
    path = root / relative_path
    try:
        if path.is_symlink() or path.stat().st_size > max_file_bytes:
            cache[relative_path] = None
        else:
            cache[relative_path] = path.read_bytes()
    except OSError:
        cache[relative_path] = None
    return cache[relative_path]


def _source_map_contents(
    root: Path,
    relative_path: str,
    *,
    max_file_bytes: int,
    byte_cache: dict[str, bytes | None],
    source_map_cache: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if relative_path in source_map_cache:
        return source_map_cache[relative_path]
    raw = _read_bytes(
        root,
        relative_path,
        max_file_bytes=max_file_bytes,
        cache=byte_cache,
    )
    if raw is None:
        return ()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, dict):
        return ()
    contents = payload.get("sourcesContent")
    if not isinstance(contents, list) or len(contents) > MAX_SOURCE_MAP_ENTRIES:
        return ()
    strings = tuple(item for item in contents if isinstance(item, str))
    if sum(len(item.encode("utf-8")) for item in strings) > max_file_bytes:
        return ()
    source_map_cache[relative_path] = strings
    return strings


def _same_vendor_evidence(
    canonical: StaticDetectionFinding,
    duplicate: StaticDetectionFinding,
    *,
    root: Path,
    inventory: dict[str, StaticArtifactInventoryEntry],
    max_file_bytes: int,
    byte_cache: dict[str, bytes | None],
) -> bool:
    if len(canonical.evidence) != len(duplicate.evidence) or not duplicate.evidence:
        return False
    duplicate_entries = [
        inventory.get(evidence.relative_path) for evidence in duplicate.evidence
    ]
    if not all(
        entry is not None and (entry.is_vendor or entry.is_minified)
        for entry in duplicate_entries
    ):
        return False
    for canonical_evidence, duplicate_evidence in zip(
        canonical.evidence, duplicate.evidence, strict=True
    ):
        if _evidence_shape(canonical_evidence) != _evidence_shape(duplicate_evidence):
            return False
        canonical_bytes = _read_bytes(
            root,
            canonical_evidence.relative_path,
            max_file_bytes=max_file_bytes,
            cache=byte_cache,
        )
        duplicate_bytes = _read_bytes(
            root,
            duplicate_evidence.relative_path,
            max_file_bytes=max_file_bytes,
            cache=byte_cache,
        )
        if canonical_bytes is None or canonical_bytes != duplicate_bytes:
            return False
    return True


def _same_source_map_evidence(
    canonical: StaticDetectionFinding,
    duplicate: StaticDetectionFinding,
    *,
    root: Path,
    inventory: dict[str, StaticArtifactInventoryEntry],
    max_file_bytes: int,
    byte_cache: dict[str, bytes | None],
    source_map_cache: dict[str, tuple[str, ...]],
) -> bool:
    if len(canonical.evidence) != len(duplicate.evidence) or not duplicate.evidence:
        return False
    for canonical_evidence, duplicate_evidence in zip(
        canonical.evidence, duplicate.evidence, strict=True
    ):
        duplicate_entry = inventory.get(duplicate_evidence.relative_path)
        canonical_entry = inventory.get(canonical_evidence.relative_path)
        if (
            duplicate_entry is None
            or duplicate_entry.role != "source_map"
            or canonical_entry is None
            or canonical_entry.role == "source_map"
            or canonical_evidence.type != duplicate_evidence.type
            or canonical_evidence.tool != duplicate_evidence.tool
            or canonical_evidence.rule_match_id != duplicate_evidence.rule_match_id
        ):
            return False
        canonical_bytes = _read_bytes(
            root,
            canonical_evidence.relative_path,
            max_file_bytes=max_file_bytes,
            cache=byte_cache,
        )
        if canonical_bytes is None:
            return False
        try:
            canonical_text = canonical_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return False
        contents = _source_map_contents(
            root,
            duplicate_evidence.relative_path,
            max_file_bytes=max_file_bytes,
            byte_cache=byte_cache,
            source_map_cache=source_map_cache,
        )
        if canonical_text not in contents:
            return False
        snippet = canonical_evidence.snippet or ""
        duplicate_snippet = duplicate_evidence.snippet or ""
        escaped = json.dumps(snippet, ensure_ascii=False)[1:-1]
        if not snippet or (
            snippet not in canonical_text
            or (snippet not in duplicate_snippet and escaped not in duplicate_snippet)
        ):
            return False
    return True


def _fingerprint(
    canonical: StaticDetectionFinding,
    duplicate: StaticDetectionFinding,
    reason: StaticFindingDeduplicationReason,
) -> str:
    payload = {
        "rule_id": canonical.rule_id,
        "rule_version": canonical.rule_version,
        "reason": reason,
        "canonical": [
            evidence.model_dump(mode="json") for evidence in canonical.evidence
        ],
        "duplicate": [
            evidence.model_dump(mode="json") for evidence in duplicate.evidence
        ],
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def deduplicate_findings(
    context: StaticAnalysisContext,
    *,
    findings: list[StaticDetectionFinding],
    artifact_inventory: tuple[StaticArtifactInventoryEntry, ...],
    max_file_bytes: int,
) -> FindingDeduplicationResult:
    """Suppress only exact, provenance-backed vendor or source-map echoes."""

    inventory = {entry.relative_path: entry for entry in artifact_inventory}
    ordered = sorted(findings, key=lambda item: _canonical_rank(item, inventory))
    retained: list[StaticDetectionFinding] = []
    records: list[StaticFindingDeduplicationRecord] = []
    byte_cache: dict[str, bytes | None] = {}
    source_map_cache: dict[str, tuple[str, ...]] = {}

    for candidate in ordered:
        duplicate_of: StaticDetectionFinding | None = None
        reason: StaticFindingDeduplicationReason | None = None
        for canonical in retained:
            if _finding_identity(canonical) != _finding_identity(candidate):
                continue
            if _same_vendor_evidence(
                canonical,
                candidate,
                root=context.vsix_dir,
                inventory=inventory,
                max_file_bytes=max_file_bytes,
                byte_cache=byte_cache,
            ):
                duplicate_of = canonical
                reason = "vendor_echo"
                break
            if _same_source_map_evidence(
                canonical,
                candidate,
                root=context.vsix_dir,
                inventory=inventory,
                max_file_bytes=max_file_bytes,
                byte_cache=byte_cache,
                source_map_cache=source_map_cache,
            ):
                duplicate_of = canonical
                reason = "source_map_echo"
                break
        if duplicate_of is None or reason is None:
            retained.append(candidate)
            continue
        canonical_evidence = duplicate_of.evidence[0]
        duplicate_evidence = candidate.evidence[0]
        records.append(
            StaticFindingDeduplicationRecord(
                rule_id=candidate.rule_id,
                rule_version=candidate.rule_version,
                reason=reason,
                canonical_path=canonical_evidence.relative_path,
                canonical_line_number=canonical_evidence.line_number,
                duplicate_path=duplicate_evidence.relative_path,
                duplicate_line_number=duplicate_evidence.line_number,
                evidence_fingerprint=_fingerprint(duplicate_of, candidate, reason),
            )
        )

    return FindingDeduplicationResult(
        findings=tuple(retained),
        records=tuple(
            sorted(
                records,
                key=lambda item: (
                    item.rule_id,
                    item.canonical_path,
                    item.duplicate_path,
                    item.evidence_fingerprint,
                ),
            )
        ),
    )


__all__ = [
    "MAX_SOURCE_MAP_ENTRIES",
    "FindingDeduplicationResult",
    "deduplicate_findings",
]
