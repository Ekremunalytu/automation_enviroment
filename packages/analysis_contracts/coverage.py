"""Typed coverage_summary projection (W10-4).

Coverage summaries originate in two stages:

1. The planner emits the first six fields (``covered``/``partial``/
   ``missing`` counts plus the matching capability lists) via
   ``packages.analysis_planner.coverage._summarize_coverage_matrix``.
2. The executor's ``reconcile_coverage_verification`` enriches each
   track's summary with ``attempted``/``verified`` counts and the
   matching capability lists.

Pre-W10-4 the contract carried this as ``dict[str, Any]``; this module
pins it as a Pydantic model so contract drift surfaces at ingest time
instead of through downstream rollup mismatches. All fields default to
empty so a planner-only payload (no executor reconciliation yet)
validates cleanly.
"""

from __future__ import annotations

from pydantic import Field

from packages.analysis_contracts.contracts import StrictContractModel


class CoverageSummary(StrictContractModel):
    """Typed projection of ``ActivationReport.coverage_summary`` and
    ``TriggerPayload.coverage_summary``."""

    covered: int = 0
    partial: int = 0
    missing: int = 0
    covered_capabilities: list[str] = Field(default_factory=list)
    partial_capabilities: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    attempted: int = 0
    verified: int = 0
    attempted_capabilities: list[str] = Field(default_factory=list)
    verified_capabilities: list[str] = Field(default_factory=list)
