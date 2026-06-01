"""Combined static + dynamic analysis bundle schemas (ES-1, ADR 0016).

The static stage produces a ``StaticAnalysisReport`` (detection report +
gate outcome). When the gate ALLOWs/WARNs, the dynamic stage runs and its
``AnalysisBundle`` is attached; when the gate BLOCKs, ``dynamic_bundle`` is
``None`` (the sandbox was skipped — the cheap-reject path).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from appcore.contracts.schema_defs.analysis_bundle import AnalysisBundle
from packages.analysis_contracts.static_detection import (
    StaticDetectionReport,
    StaticGateOutcome,
)


class StaticAnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detection_report: StaticDetectionReport
    gate_outcome: StaticGateOutcome


class CombinedAnalysisBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    static_report: StaticAnalysisReport
    # None when the gate BLOCKED (dynamic stage skipped → rejected_static).
    dynamic_bundle: AnalysisBundle | None = None


__all__ = ["CombinedAnalysisBundle", "StaticAnalysisReport"]
