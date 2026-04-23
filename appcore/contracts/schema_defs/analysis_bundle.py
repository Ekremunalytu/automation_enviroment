"""Combined activation+detection bundle schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from packages.analysis_contracts import ActivationReport, DetectionReport


class AnalysisBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activation_report: ActivationReport
    detection_report: DetectionReport


__all__ = ["AnalysisBundle"]
