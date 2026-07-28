"""Operator-tunable executor preference schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, StrictBool


class ExecutorPreferencesResponse(BaseModel):
    """Current effective executor preferences."""

    dynamic_analysis_enabled: bool


class ExecutorPreferencesUpdateRequest(BaseModel):
    """Update the operator-controlled dynamic analysis preference."""

    dynamic_analysis_enabled: StrictBool
    updated_by: str | None = Field(default=None, max_length=128)


__all__ = [
    "ExecutorPreferencesResponse",
    "ExecutorPreferencesUpdateRequest",
]
