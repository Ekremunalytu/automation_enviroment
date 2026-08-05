"""Bounded SAP-5 reachability provenance contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.static_detection.artifact import (
    StaticArtifactReachabilityEdgeKind,
    _normalize_relative_path,
)

StaticReachabilityLimitReason = Literal[
    "node_cap",
    "edge_cap",
    "byte_cap",
    "depth_cap",
    "read_error",
    "parse_error",
]


class StaticReachabilityUnresolvedReference(StrictContractModel):
    """One bounded import/loader expression that could not resolve locally."""

    source_path: str
    line_number: int = Field(ge=1)
    edge_kind: StaticArtifactReachabilityEdgeKind
    expression: str = Field(min_length=1, max_length=200)

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, value: str) -> str:
        return _normalize_relative_path(value)


class StaticReachabilitySummary(StrictContractModel):
    """Deterministic aggregate evidence for one bounded module graph."""

    roots: list[str] = Field(default_factory=list, max_length=32)
    nodes_reached: int = Field(default=0, ge=0)
    edges_resolved: int = Field(default=0, ge=0)
    bytes_read: int = Field(default=0, ge=0)
    unresolved_count: int = Field(default=0, ge=0)
    unresolved_references: list[StaticReachabilityUnresolvedReference] = Field(
        default_factory=list, max_length=20
    )
    limit_reasons: list[StaticReachabilityLimitReason] = Field(
        default_factory=list, max_length=6
    )

    @field_validator("roots")
    @classmethod
    def validate_roots(cls, value: list[str]) -> list[str]:
        return sorted({_normalize_relative_path(path) for path in value})

    @field_validator("limit_reasons")
    @classmethod
    def normalize_limit_reasons(
        cls, value: list[StaticReachabilityLimitReason]
    ) -> list[StaticReachabilityLimitReason]:
        return sorted(set(value))


__all__ = [
    "StaticReachabilityLimitReason",
    "StaticReachabilitySummary",
    "StaticReachabilityUnresolvedReference",
]
