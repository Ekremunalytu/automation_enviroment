"""Marketplace and analysis schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from appcore.contracts.schema_defs.static_analysis_bundle import StaticAnalysisReport
from packages.analysis_contracts import DetectionReport


class MarketplaceExtension(BaseModel):
    model_config = ConfigDict(extra="ignore")

    publisher: str
    name: str
    version: str
    displayName: str
    description: str
    installs: int
    rating: float


class MarketplaceDownloadRequest(BaseModel):
    publisher: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)


class VsixExtractionMetrics(BaseModel):
    """Observed VSIX extraction metrics, surfaced post-download.

    The UI compares ``file_count`` / ``uncompressed_size`` /
    ``compression_ratio`` against the operator-set thresholds (returned
    by ``GET /api/settings/security/thresholds``) to highlight
    extensions whose footprint approaches the configured limits.
    Renders as the "VSIX Integrity" panel on the Reports page.
    """

    file_count: int = Field(ge=0)
    uncompressed_size: int = Field(ge=0)
    compressed_size: int = Field(ge=0)
    compression_ratio: float = Field(ge=0)
    rejected_entry_count: int = Field(ge=0)


class VsixThresholdBreachDetail(BaseModel):
    """Structured 422 detail for VSIX extraction threshold breaches."""

    error: Literal["vsix_threshold_breach"]
    breach_kind: Literal["entry_count", "uncompressed_size", "compression_ratio"]
    threshold_name: str
    threshold_value: int
    observed_value: int | float
    message: str
    publisher: str
    name: str
    version: str


class MarketplaceDownloadResponse(BaseModel):
    status: str
    publisher: str
    name: str
    version: str
    extension_dir: str
    db_id: int | None = None
    message: str
    # ``None`` when the extension was already extracted on disk and the
    # download path was a no-op idempotent return (no fresh metrics to
    # measure). Populated on every fresh extraction.
    vsix_metrics: VsixExtractionMetrics | None = None


class AnalyzeRequest(BaseModel):
    publisher: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    scenario: str | None = None
    analysis_profile: str | None = Field(default=None, min_length=1)


class AnalyzeResponse(BaseModel):
    status: str
    publisher: str
    name: str
    version: str
    message: str
    install_output: str | None = None
    automation_output: str | None = None
    report_path: str | None = None
    # ES-5 (ADR 0016): the static pre-check result, folded in by the orchestrator
    # when the gate ran (ALLOW/WARN). ``None`` when the static stage is disabled
    # (flag OFF) so the dynamic-only response shape is unchanged.
    static_report: StaticAnalysisReport | None = None


class AnalyzeJobStepProgress(BaseModel):
    completed: int = Field(ge=0)
    total: int = Field(ge=0)


class AnalyzeJobStep(BaseModel):
    name: str
    status: str
    message: str
    error_code: str | None = None
    progress: AnalyzeJobStepProgress | None = None


class AnalyzeJobStatusResponse(BaseModel):
    job_id: str
    status: str
    publisher: str
    name: str
    version: str
    scenario: str | None = None
    current_step: str | None = None
    message: str
    steps: list[AnalyzeJobStep] = Field(default_factory=list)
    report_path: str | None = None
    install_output: str | None = None
    automation_output: str | None = None
    error_detail: str | None = None
    error_code: str | None = None
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
    updated_at: float
    detection_report: DetectionReport | None = None
    report_error: str | None = None
    # ES-5 (ADR 0016): the persisted static-report path (mirrors ``report_path``;
    # set on the ALLOW/WARN completion and the BLOCK ``rejected_static`` reject)
    # and the loaded static report the router folds in from it (mirrors
    # ``detection_report``). Both ``None`` for jobs that ran no static pre-check.
    static_report_path: str | None = None
    static_report: StaticAnalysisReport | None = None


__all__ = [
    "AnalyzeJobStatusResponse",
    "AnalyzeJobStep",
    "AnalyzeJobStepProgress",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "MarketplaceDownloadRequest",
    "MarketplaceDownloadResponse",
    "MarketplaceExtension",
    "VsixExtractionMetrics",
    "VsixThresholdBreachDetail",
]
