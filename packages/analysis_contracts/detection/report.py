"""Detection report DTOs."""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import Literal, cast

from pydantic import Field

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.detection.enums import (
    RuleExecutionStatus,
    RuleLifecycle,
    Verdict,
)
from packages.analysis_contracts.detection.finding import DetectionFinding

_UTC_FALLBACK = timezone.utc  # noqa: UP017
UTC = cast(tzinfo, getattr(datetime, "UTC", _UTC_FALLBACK))


class AutomationHealthStatus(StrictContractModel):
    """Minimal automation health projection used by verdict rollup."""

    status: Literal["healthy", "degraded", "inconclusive"] = "healthy"
    reasons: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class ExtensionIdentity(StrictContractModel):
    """Stable extension identity tuple used by report bundles."""

    publisher: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class RuleExecutionRecord(StrictContractModel):
    """Execution metadata for a detection rule."""

    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    lifecycle: RuleLifecycle
    status: RuleExecutionStatus
    finding_ids: list[str] = Field(default_factory=list)
    error_detail: str | None = None


class DetectionReport(StrictContractModel):
    """Detection findings carried alongside an activation report."""

    schema_version: Literal["1"] = "1"
    activation_report_ref: str = Field(min_length=1)
    analyzed_extension: ExtensionIdentity
    findings: list[DetectionFinding] = Field(default_factory=list)
    verdict: Verdict
    verdict_rationale: str = Field(min_length=1)
    rules_executed: list[RuleExecutionRecord] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


__all__ = [
    "AutomationHealthStatus",
    "DetectionReport",
    "ExtensionIdentity",
    "RuleExecutionRecord",
]
