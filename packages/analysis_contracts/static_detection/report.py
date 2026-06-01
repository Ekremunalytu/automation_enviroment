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
    # ES-4 execution observability: a tool that errored, timed out, or broke its
    # budget early must be distinguishable from a clean pass, so a silent failure
    # never reads as a clean ALLOW. ``error_count`` / ``errored_rule_ids`` capture
    # per-rule degradation (a swallowed in-house rule error, a Semgrep per-file
    # parse error) without failing the whole pass.
    status: Literal["ok", "partial", "error", "timeout"] = "ok"
    error_count: int = Field(default=0, ge=0)
    errored_rule_ids: list[str] = Field(default_factory=list)
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

    schema_version: Literal["2"] = "2"
    findings: list[StaticDetectionFinding] = Field(default_factory=list)
    tool_executions: list[StaticToolExecutionRecord] = Field(default_factory=list)
    severity_counts: StaticSeverityCounts = Field(default_factory=StaticSeverityCounts)
    # ES-4: True when any tool ran only partially — the in-house budget tripped
    # early, or a Semgrep error/timeout left source unscanned — so a consumer
    # knows the report's coverage is incomplete rather than confidently clean.
    partial: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


__all__ = [
    "StaticDetectionReport",
    "StaticSeverityCounts",
    "StaticTool",
    "StaticToolExecutionRecord",
]
