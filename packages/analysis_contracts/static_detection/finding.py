"""Static-detection finding DTOs (ES-1, ADR 0016).

Mirrors the dynamic ``DetectionFinding`` field set by identity-reusing the
ADR 0003 enums (``Severity`` / ``Confidence`` / ``RuleLifecycle`` /
``AdversaryClass``) rather than cloning them, per ADR 0005 + ADR 0016
§Decision 3 (schema-first).
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.detection._ulid import generate_ulid
from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)

# Mirror of the dynamic DetectionFinding category namespaces
# (packages/analysis_contracts/detection/finding.py). Static findings reuse
# the same attack.T#### / extrace.ext.* / extrace.host.* taxonomy so the UI
# and verdict rollup treat both finding streams uniformly.
_CATEGORY_PATTERNS = (
    re.compile(r"^attack\.T\d+(?:\.\d+)?$"),
    re.compile(r"^extrace\.ext\.[a-z_]+$"),
    re.compile(r"^extrace\.host\.[a-z_]+$"),
)

# v2 evidence types (lockfile, dependency) are pre-shipped onto the Literal
# at ES-1 even though the MVP emits only manifest / source_file / binary_file.
# Zero runtime cost; avoids a forced schema migration when YARA / Trivy enroll.
StaticEvidenceType = Literal[
    "manifest",
    "source_file",
    "binary_file",
    "lockfile",
    "dependency",
]


class StaticEvidenceRef(StrictContractModel):
    """Reference to a static artifact location backing a finding."""

    type: StaticEvidenceType
    relative_path: str = Field(min_length=1)
    line_number: int | None = Field(default=None, ge=1)
    snippet: str | None = Field(default=None, max_length=400)
    tool: str = Field(min_length=1)
    rule_match_id: str | None = None


class StaticDetectionFinding(StrictContractModel):
    """Static-analysis finding; field-set parity with ``DetectionFinding``."""

    id: str = Field(default_factory=generate_ulid, min_length=26, max_length=26)
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    rule_lifecycle: RuleLifecycle
    categories: list[str] = Field(min_length=1)
    severity: Severity
    confidence: Confidence
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence: list[StaticEvidenceRef] = Field(default_factory=list)
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


__all__ = ["StaticDetectionFinding", "StaticEvidenceRef", "StaticEvidenceType"]
