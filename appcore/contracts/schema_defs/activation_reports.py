"""Activation report response schemas exposed by the API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from appcore.contracts.schema_defs.static_analysis_bundle import StaticAnalysisReport
from packages.analysis_contracts import ActivationReport


class ActivationReportMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str


class ActivationReportResponse(ActivationReport):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    metadata: ActivationReportMetadata | None = Field(default=None, alias="_metadata")


class StaticReportArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    modified: float
    static_report: StaticAnalysisReport


__all__ = [
    "ActivationReportMetadata",
    "ActivationReportResponse",
    "StaticReportArtifactResponse",
]
