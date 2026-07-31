"""Static-detection report DTOs (ES-1, ADR 0016)."""

from __future__ import annotations

import re
from datetime import datetime, timezone, tzinfo
from typing import Literal, cast

from pydantic import Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.static_detection.finding import StaticDetectionFinding

_UTC_FALLBACK = timezone.utc  # noqa: UP017
UTC = cast(tzinfo, getattr(datetime, "UTC", _UTC_FALLBACK))

# v2 tool slots (yara, trivy) pre-shipped onto the Literal at ES-1; the MVP
# emits inhouse + semgrep only. Defensive posture per ADR 0016 §Decision 4.
StaticTool = Literal["inhouse", "semgrep", "yara", "trivy"]
StaticCoverageReason = Literal[
    "file_cap",
    "target_too_large",
    "text_truncated",
    "undecodable",
    "unsupported_suffix",
    "parser_error",
    "manifest_missing",
    "manifest_malformed",
    "manifest_too_large",
    "critical_entrypoint_missing",
    "critical_entrypoint_unparsed",
    "rule_timeout",
    "tool_timeout",
    "tool_error",
    "finding_cap",
    "budget_stop",
    "excluded_inventory_only",
]
StaticManifestStatus = Literal[
    "parsed",
    "missing",
    "malformed",
    "too_large",
    "unreadable",
    "non_object",
]


def _normalize_relative_path(value: str, *, label: str) -> str:
    normalized = value.replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or ".." in normalized.split("/")
        or any(ord(char) < 32 for char in normalized)
    ):
        raise ValueError(f"{label} must be safe and relative")
    return normalized


class StaticScanCoverage(StrictContractModel):
    """Bounded, additive accounting for what a static pass did and did not inspect."""

    files_discovered: int = Field(default=0, ge=0)
    files_selected: int = Field(default=0, ge=0)
    files_eligible: int = Field(default=0, ge=0)
    files_scanned: int = Field(default=0, ge=0)
    files_parsed: int = Field(default=0, ge=0)
    files_skipped_by_reason: dict[str, int] = Field(default_factory=dict)
    skipped_paths_by_reason: dict[str, list[str]] = Field(default_factory=dict)
    bytes_considered: int = Field(default=0, ge=0)
    bytes_read: int = Field(default=0, ge=0)
    manifest_status: StaticManifestStatus = "missing"
    critical_entrypoints: list[str] = Field(default_factory=list, max_length=32)
    critical_entrypoints_parsed: list[str] = Field(default_factory=list, max_length=32)
    file_cap_reached: bool = False
    finding_cap_reached: bool = False
    unsupported_formats: dict[str, int] = Field(default_factory=dict)
    coverage_reasons: list[StaticCoverageReason] = Field(
        default_factory=list, max_length=64
    )

    @field_validator(
        "files_skipped_by_reason",
        "unsupported_formats",
    )
    @classmethod
    def validate_bounded_count_maps(cls, value: dict[str, int]) -> dict[str, int]:
        if len(value) > 64:
            raise ValueError("coverage count maps are limited to 64 keys")
        for key, count in value.items():
            if not key or len(key) > 80 or count < 0:
                raise ValueError("coverage count maps require bounded keys and counts")
        return dict(sorted(value.items()))

    @field_validator("skipped_paths_by_reason")
    @classmethod
    def validate_bounded_path_details(
        cls, value: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        if len(value) > 64:
            raise ValueError("coverage path detail maps are limited to 64 keys")
        normalized: dict[str, list[str]] = {}
        for reason, paths in value.items():
            if not reason or len(reason) > 80 or len(paths) > 20:
                raise ValueError("coverage path details must be bounded")
            normalized_paths: list[str] = []
            for path in paths:
                normalized_paths.append(
                    _normalize_relative_path(
                        path,
                        label="coverage detail paths",
                    )
                )
            normalized[reason] = sorted(set(normalized_paths))
        return dict(sorted(normalized.items()))

    @field_validator(
        "critical_entrypoints",
        "critical_entrypoints_parsed",
    )
    @classmethod
    def validate_relative_paths(cls, value: list[str]) -> list[str]:
        return sorted(
            {
                _normalize_relative_path(
                    path,
                    label="coverage entrypoint paths",
                )
                for path in value
            }
        )

    @field_validator("coverage_reasons")
    @classmethod
    def dedupe_reasons(
        cls, value: list[StaticCoverageReason]
    ) -> list[StaticCoverageReason]:
        return sorted(set(value))


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
    coverage: StaticScanCoverage = Field(default_factory=StaticScanCoverage)
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
    coverage: StaticScanCoverage = Field(default_factory=StaticScanCoverage)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # W26 / Stream 3 (B5 `[GOAL vsix-content-sha256-provenance]`): SHA-256 of the
    # analyzed .vsix archive (canonical 64-char lowercase), threaded into the
    # hardened static container via the additive ``--vsix-sha256`` flag (ADR 0016
    # amendment) and stamped by the runner. Lets the static report be bound to
    # the same bytes the dynamic report carries; the orchestrator asserts they
    # agree. Default-empty so legacy reports validate; schema_version stays "2"
    # (additive-optional, no strict version-match validator on this contract).
    vsix_sha256: str = ""


__all__ = [
    "StaticCoverageReason",
    "StaticDetectionReport",
    "StaticManifestStatus",
    "StaticScanCoverage",
    "StaticSeverityCounts",
    "StaticTool",
    "StaticToolExecutionRecord",
]
