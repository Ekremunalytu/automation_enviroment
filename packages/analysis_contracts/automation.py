"""Typed automation_health projection (W10-4).

The executor's ``build_automation_health`` (
``executor/flows/playwright/health_summary.py``) emits a 14-field dict that
captures whether the automation harness reached the target extension and
why. Pre-W10-4 the contract carried this as ``dict[str, Any]``; this
module pins it as a Pydantic model so contract drift surfaces at
ingest time instead of through downstream rollup mismatches.

Field coverage matches the producer faithfully — all fields are
optional with safe defaults so legacy payloads (and the
``skip_automation`` execution mode that emits a 5-field subset) still
validate.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from packages.analysis_contracts.contracts import StrictContractModel

AutomationHealthStatusLiteral = Literal["healthy", "degraded", "inconclusive"]


class AutomationHealth(StrictContractModel):
    """Typed projection of ``ActivationReport.automation_health``."""

    status: AutomationHealthStatusLiteral = "inconclusive"
    reasons: list[str] = Field(default_factory=list)
    trigger_requested: bool = False
    trigger_loaded: bool = False
    trigger_applied: bool = False
    extension_host_log_present: bool = False
    extension_host_log_found: bool = False
    extension_host_output_present: bool = False
    target_stream_present: bool = False
    target_activation_count: int = 0
    failed_scenarios: list[str] = Field(default_factory=list)
    extra_trigger_failures: list[str] = Field(default_factory=list)
    extra_trigger_failure_count: int = 0
    skipped_scenarios: list[str] = Field(default_factory=list)
