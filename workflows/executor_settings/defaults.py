"""Canonical keys and defaults for operator-tunable executor preferences."""

from typing import Final

DYNAMIC_ANALYSIS_ENABLED_KEY: Final[str] = "dynamic_analysis_enabled"
DYNAMIC_ANALYSIS_ENABLED_DEFAULT: Final[bool] = False


__all__ = [
    "DYNAMIC_ANALYSIS_ENABLED_DEFAULT",
    "DYNAMIC_ANALYSIS_ENABLED_KEY",
]
