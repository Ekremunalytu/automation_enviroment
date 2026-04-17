"""Activation report response schemas exposed by the API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from packages.analysis_contracts import ActivationReport


class ActivationReportMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str


class ActivationReportResponse(ActivationReport):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    metadata: ActivationReportMetadata | None = Field(default=None, alias="_metadata")


__all__ = ["ActivationReportMetadata", "ActivationReportResponse"]
