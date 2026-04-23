"""Error types shared across marketplace analysis helpers."""

from __future__ import annotations


class TriggerPlanError(RuntimeError):
    """Raised when trigger planning fails closed."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


class ActivationReportLoadError(ValueError):
    """Raised when an exported activation report cannot be read safely."""


__all__ = ["ActivationReportLoadError", "TriggerPlanError"]
