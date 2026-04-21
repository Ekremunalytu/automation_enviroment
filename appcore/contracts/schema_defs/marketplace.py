"""Marketplace and analysis schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

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


class MarketplaceDownloadResponse(BaseModel):
    status: str
    publisher: str
    name: str
    version: str
    extension_dir: str
    db_id: int | None = None
    message: str


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


class AnalyzeJobStep(BaseModel):
    name: str
    status: str
    message: str
    error_code: str | None = None


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


__all__ = [
    "AnalyzeJobStatusResponse",
    "AnalyzeJobStep",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "MarketplaceDownloadRequest",
    "MarketplaceDownloadResponse",
    "MarketplaceExtension",
]
