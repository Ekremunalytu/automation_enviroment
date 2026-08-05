"""Bounded artifact-inventory contracts for static analysis reports."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel

StaticArtifactRole = Literal[
    "manifest",
    "first_party_runtime",
    "dependency_runtime",
    "documentation",
    "license",
    "test",
    "asset",
    "source_map",
    "configuration",
    "native",
    "wasm",
    "archive",
    "unknown",
]
StaticArtifactFormat = Literal[
    "text",
    "png",
    "jpeg",
    "gif",
    "webp",
    "font",
    "sqlite",
    "zip",
    "gzip",
    "7z",
    "rar",
    "tar",
    "pe",
    "elf",
    "mach_o",
    "wasm",
    "opaque_binary",
    "unknown",
]
StaticArtifactDisposition = Literal["deep_scan", "inventory_only", "skipped"]
StaticArtifactEntrypointReachability = Literal[
    "direct", "transitive", "none", "unknown"
]
StaticArtifactReachabilityEdgeKind = Literal[
    "manifest",
    "import",
    "export",
    "require",
    "dynamic_import",
    "require_resolve",
    "source_map",
    "path_loader",
    "native_loader",
]
StaticArtifactReachabilityConfidence = Literal["literal", "heuristic"]
StaticArtifactDispositionReason = Literal[
    "first_party_runtime",
    "direct_manifest_entrypoint",
    "transitive_entrypoint_reachable",
    "heuristic_loader_reachable",
    "inhouse_finding_evidence",
    "format_extension_mismatch",
    "dependency_inventory_only",
    "vendor_inventory_only",
    "minified_inventory_only",
    "non_runtime_artifact",
    "unsupported_format",
    "target_too_large",
    "read_error",
    "deep_scan_target_cap",
]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _normalize_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if (
        not normalized
        or len(normalized) > 1024
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or ".." in normalized.split("/")
        or any(ord(char) < 32 for char in normalized)
    ):
        raise ValueError("artifact inventory path must be safe and relative")
    canonical = PurePosixPath(normalized).as_posix()
    if canonical in {"", "."}:
        raise ValueError("artifact inventory path must name a file")
    return canonical


class StaticArtifactInventoryEntry(StrictContractModel):
    """One deterministic, content-bounded record for a discovered VSIX file."""

    relative_path: str
    role: StaticArtifactRole
    format: StaticArtifactFormat
    size_bytes: int = Field(ge=0)
    header_sha256: str | None = None
    header_bytes_read: int = Field(default=0, ge=0, le=512)
    extension_header_match: bool | None = None
    dependency_owner: str | None = Field(default=None, max_length=214)
    is_vendor: bool = False
    is_minified: bool = False
    entrypoint_reachability: StaticArtifactEntrypointReachability = "unknown"
    reachability_parent: str | None = None
    reachability_edge_kind: StaticArtifactReachabilityEdgeKind | None = None
    reachability_confidence: StaticArtifactReachabilityConfidence | None = None
    disposition: StaticArtifactDisposition
    disposition_reasons: list[StaticArtifactDispositionReason] = Field(
        min_length=1, max_length=8
    )

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _normalize_relative_path(value)

    @field_validator("reachability_parent")
    @classmethod
    def validate_reachability_parent(cls, value: str | None) -> str | None:
        return None if value is None else _normalize_relative_path(value)

    @field_validator("header_sha256")
    @classmethod
    def validate_header_sha256(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256_RE.fullmatch(value):
            raise ValueError("header_sha256 must be lowercase SHA-256")
        return value

    @field_validator("dependency_owner")
    @classmethod
    def validate_dependency_owner(cls, value: str | None) -> str | None:
        if value is None:
            return None
        owner = value.strip()
        if not owner or any(ord(char) < 32 for char in owner):
            raise ValueError("dependency_owner must be bounded printable text")
        return owner

    @field_validator("disposition_reasons")
    @classmethod
    def normalize_reasons(
        cls, value: list[StaticArtifactDispositionReason]
    ) -> list[StaticArtifactDispositionReason]:
        return sorted(set(value))


__all__ = [
    "StaticArtifactDisposition",
    "StaticArtifactDispositionReason",
    "StaticArtifactEntrypointReachability",
    "StaticArtifactFormat",
    "StaticArtifactInventoryEntry",
    "StaticArtifactReachabilityConfidence",
    "StaticArtifactReachabilityEdgeKind",
    "StaticArtifactRole",
]
