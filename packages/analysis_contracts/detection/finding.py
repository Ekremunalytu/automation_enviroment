"""Detection finding DTOs."""

from __future__ import annotations

import re

from pydantic import ConfigDict, Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.detection._ulid import generate_ulid
from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)

_CATEGORY_PATTERNS = (
    re.compile(r"^attack\.T\d+(?:\.\d+)?$"),
    re.compile(r"^extrace\.ext\.[a-z_]+$"),
    re.compile(r"^extrace\.host\.[a-z_]+$"),
)


class EvidenceRef(StrictContractModel):
    """Reference to an ActivationReport evidence event."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=200)


class DetectionFinding(StrictContractModel):
    """Authoritative detection finding payload."""

    id: str = Field(default_factory=generate_ulid, min_length=26, max_length=26)
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    rule_lifecycle: RuleLifecycle
    categories: list[str] = Field(min_length=1)
    severity: Severity
    confidence: Confidence
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    adversary_class: AdversaryClass | None = None
    mitigation_hint: str | None = None

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, value: list[str]) -> list[str]:
        for category in value:
            if any(pattern.match(category) for pattern in _CATEGORY_PATTERNS):
                continue
            msg = (
                "Detection categories must use attack.T####, extrace.ext.*, "
                "or extrace.host.* namespaces."
            )
            raise ValueError(msg)
        return value


__all__ = ["DetectionFinding", "EvidenceRef"]
