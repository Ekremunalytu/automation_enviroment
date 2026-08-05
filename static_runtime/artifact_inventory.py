"""Deterministic SAP-4 artifact inventory and bounded deep-target selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from packages.analysis_contracts.static_detection import (
    StaticArtifactDisposition,
    StaticArtifactDispositionReason,
    StaticArtifactInventoryEntry,
    StaticDetectionFinding,
)
from static_runtime.artifacts import (
    DEEP_SCAN_SOURCE_SUFFIXES,
    classify_artifact,
    dependency_owner,
    is_minified_path,
    is_vendor_path,
)
from static_runtime.context import StaticAnalysisContext

MAX_EXTRA_DEEP_SCAN_TARGETS = 256


@dataclass(frozen=True, slots=True)
class ArtifactInventoryResult:
    entries: tuple[StaticArtifactInventoryEntry, ...]
    extra_deep_scan_targets: tuple[str, ...]
    target_cap_reached: bool


def _inhouse_evidence_paths(
    findings: list[StaticDetectionFinding],
) -> frozenset[str]:
    return frozenset(
        evidence.relative_path
        for finding in findings
        for evidence in finding.evidence
        if evidence.tool == "inhouse"
    )


def _inventory_only_reason(
    *, dependency: str | None, vendor: bool, minified: bool, runtime_supported: bool
) -> StaticArtifactDispositionReason:
    if dependency is not None:
        return "dependency_inventory_only"
    if vendor:
        return "vendor_inventory_only"
    if minified:
        return "minified_inventory_only"
    if not runtime_supported:
        return "unsupported_format"
    return "non_runtime_artifact"


def build_artifact_inventory(
    context: StaticAnalysisContext,
    *,
    findings: list[StaticDetectionFinding],
    max_target_bytes: int,
) -> ArtifactInventoryResult:
    """Classify every retained file and select bounded extra Semgrep targets."""

    evidence_paths = _inhouse_evidence_paths(findings)
    entrypoints = frozenset(context.resolved_entrypoints())
    manifest_parsed = context.manifest_status == "parsed"
    entries: list[StaticArtifactInventoryEntry] = []
    absolute_paths: dict[str, Path] = {}

    for relative_path, absolute_path, size in context.iter_file_records():
        classification = classify_artifact(relative_path, absolute_path)
        owner = dependency_owner(relative_path)
        minified = is_minified_path(relative_path)
        vendor = is_vendor_path(relative_path)
        direct_entrypoint = relative_path in entrypoints
        runtime_supported = classification.suffix in DEEP_SCAN_SOURCE_SUFFIXES
        disposition: StaticArtifactDisposition
        reasons: list[StaticArtifactDispositionReason]

        if classification.read_error:
            disposition = "skipped"
            reasons = ["read_error"]
        elif size > max_target_bytes:
            disposition = "skipped"
            reasons = ["target_too_large"]
        else:
            deep_reasons: list[StaticArtifactDispositionReason] = []
            if direct_entrypoint:
                deep_reasons.append("direct_manifest_entrypoint")
            if (
                classification.role == "first_party_runtime"
                and runtime_supported
                and not vendor
                and not minified
            ):
                deep_reasons.append("first_party_runtime")
            if relative_path in evidence_paths and (
                owner is not None or vendor or minified
            ):
                deep_reasons.append("inhouse_finding_evidence")
            if classification.extension_header_match is False:
                deep_reasons.append("format_extension_mismatch")
            if deep_reasons:
                disposition = "deep_scan"
                reasons = deep_reasons
            else:
                disposition = "inventory_only"
                reasons = [
                    _inventory_only_reason(
                        dependency=owner,
                        vendor=vendor,
                        minified=minified,
                        runtime_supported=runtime_supported,
                    )
                ]

        entries.append(
            StaticArtifactInventoryEntry(
                relative_path=relative_path,
                role=classification.role,
                format=classification.format,
                size_bytes=size,
                header_sha256=classification.header_sha256,
                header_bytes_read=classification.header_bytes_read,
                extension_header_match=classification.extension_header_match,
                dependency_owner=owner,
                is_vendor=vendor,
                is_minified=minified,
                entrypoint_reachability=(
                    "direct"
                    if direct_entrypoint
                    else "none"
                    if manifest_parsed
                    else "unknown"
                ),
                disposition=disposition,
                disposition_reasons=reasons,
            )
        )
        absolute_paths[relative_path] = absolute_path

    extra_candidates = [
        entry
        for entry in entries
        if entry.disposition == "deep_scan"
        and (entry.dependency_owner is not None or entry.is_vendor or entry.is_minified)
        and Path(entry.relative_path).suffix.lower() in DEEP_SCAN_SOURCE_SUFFIXES
    ]
    extra_candidates.sort(
        key=lambda entry: (
            "direct_manifest_entrypoint" not in entry.disposition_reasons,
            "inhouse_finding_evidence" not in entry.disposition_reasons,
            "format_extension_mismatch" not in entry.disposition_reasons,
            entry.relative_path,
        )
    )
    selected_paths = {
        entry.relative_path for entry in extra_candidates[:MAX_EXTRA_DEEP_SCAN_TARGETS]
    }
    capped_paths = {
        entry.relative_path for entry in extra_candidates[MAX_EXTRA_DEEP_SCAN_TARGETS:]
    }
    if capped_paths:
        entries = [
            entry.model_copy(
                update={
                    "disposition": "skipped",
                    "disposition_reasons": sorted(
                        {*entry.disposition_reasons, "deep_scan_target_cap"}
                    ),
                }
            )
            if entry.relative_path in capped_paths
            else entry
            for entry in entries
        ]

    return ArtifactInventoryResult(
        entries=tuple(sorted(entries, key=lambda entry: entry.relative_path)),
        extra_deep_scan_targets=tuple(
            str(absolute_paths[path].absolute()) for path in sorted(selected_paths)
        ),
        target_cap_reached=bool(capped_paths),
    )


__all__ = [
    "MAX_EXTRA_DEEP_SCAN_TARGETS",
    "ArtifactInventoryResult",
    "build_artifact_inventory",
]
