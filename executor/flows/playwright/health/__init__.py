"""Helpers for automation and log health computation."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from .reconciliation import (
    reconcile_coverage_verification,
    reconcile_event_attempts,
)
from .summary import (
    automation_reason_to_text,
    build_automation_health,
    build_log_health,
    build_run_quality,
    count_target_activations,
    derive_verified_capabilities,
    is_background_activation,
    summarize_event_attempts_for_report,
)

__all__ = [
    "automation_reason_to_text",
    "build_automation_health",
    "build_log_health",
    "build_run_quality",
    "count_target_activations",
    "derive_verified_capabilities",
    "is_background_activation",
    "reconcile_coverage_verification",
    "reconcile_event_attempts",
    "summarize_event_attempts_for_report",
]
