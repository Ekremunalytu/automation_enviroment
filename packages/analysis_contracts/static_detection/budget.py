"""Shared static-analysis timeout budget bounds."""

from __future__ import annotations

STATIC_ANALYSIS_MIN_TIMEOUT_BUDGET_S = 5
STATIC_ANALYSIS_DEFAULT_TIMEOUT_BUDGET_S = 600
STATIC_ANALYSIS_MAX_TIMEOUT_BUDGET_S = 600
STATIC_ANALYZER_EXEC_GRACE_S = 5


def validate_static_analysis_timeout_budget(value: int) -> int:
    """Return a bounded timeout budget or raise with one canonical message."""
    if not (
        STATIC_ANALYSIS_MIN_TIMEOUT_BUDGET_S
        <= value
        <= STATIC_ANALYSIS_MAX_TIMEOUT_BUDGET_S
    ):
        raise ValueError(
            "static analysis timeout budget must be between "
            f"{STATIC_ANALYSIS_MIN_TIMEOUT_BUDGET_S} and "
            f"{STATIC_ANALYSIS_MAX_TIMEOUT_BUDGET_S} seconds"
        )
    return value


def parse_static_analysis_timeout_budget(value: str) -> int:
    """Parse the shared CLI/env representation and enforce the same bounds."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError("static analysis timeout budget must be an integer") from exc
    return validate_static_analysis_timeout_budget(parsed)


__all__ = [
    "STATIC_ANALYSIS_DEFAULT_TIMEOUT_BUDGET_S",
    "STATIC_ANALYSIS_MAX_TIMEOUT_BUDGET_S",
    "STATIC_ANALYSIS_MIN_TIMEOUT_BUDGET_S",
    "STATIC_ANALYZER_EXEC_GRACE_S",
    "parse_static_analysis_timeout_budget",
    "validate_static_analysis_timeout_budget",
]
