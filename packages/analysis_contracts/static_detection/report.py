"""Static-detection report DTOs (ES-1, ADR 0016)."""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import Literal, cast

from pydantic import Field

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.static_detection.finding import StaticDetectionFinding

_UTC_FALLBACK = timezone.utc  # noqa: UP017
UTC = cast(tzinfo, getattr(datetime, "UTC", _UTC_FALLBACK))

# v2 tool slots (yara, trivy) pre-shipped onto the Literal at ES-1; the MVP
# emits inhouse + semgrep only. Defensive posture per ADR 0016 §Decision 4.
StaticTool = Literal["inhouse", "semgrep", "yara", "trivy"]


class StaticToolExecutionRecord(StrictContractModel):
    """Per-tool execution metadata for one static analysis pass."""

    tool: StaticTool
    version: str = Field(min_length=1)
    rules_loaded: int = Field(ge=0)
    findings_emitted: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    # v2 Trivy: CVE-DB freshness audit trail; None for tools without a DB.
    db_freshness_days: int | None = Field(default=None, ge=0)


class StaticSeverityCounts(StrictContractModel):
    """One non-negative count per Severity tier (parity with the Severity enum)."""

    critical: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    low: int = Field(default=0, ge=0)
    info: int = Field(default=0, ge=0)


class StaticDetectionReport(StrictContractModel):
    """Static findings + per-tool execution records + severity rollup."""

    schema_version: Literal["1"] = "1"
    findings: list[StaticDetectionFinding] = Field(default_factory=list)
    tool_executions: list[StaticToolExecutionRecord] = Field(default_factory=list)
    severity_counts: StaticSeverityCounts = Field(default_factory=StaticSeverityCounts)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


__all__ = [
    "StaticDetectionReport",
    "StaticSeverityCounts",
    "StaticTool",
    "StaticToolExecutionRecord",
]
