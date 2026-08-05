"""Deterministic SAP-5 finding-deduplication provenance contracts."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.static_detection.artifact import (
    _normalize_relative_path,
)

StaticFindingDeduplicationReason = Literal["vendor_echo", "source_map_echo"]
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class StaticFindingDeduplicationRecord(StrictContractModel):
    """One exact duplicate finding suppressed in favor of canonical evidence."""

    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    reason: StaticFindingDeduplicationReason
    canonical_path: str
    canonical_line_number: int | None = Field(default=None, ge=1)
    duplicate_path: str
    duplicate_line_number: int | None = Field(default=None, ge=1)
    evidence_fingerprint: str

    @field_validator("canonical_path", "duplicate_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _normalize_relative_path(value)

    @field_validator("evidence_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("evidence_fingerprint must be lowercase SHA-256")
        return value


__all__ = [
    "StaticFindingDeduplicationReason",
    "StaticFindingDeduplicationRecord",
]
