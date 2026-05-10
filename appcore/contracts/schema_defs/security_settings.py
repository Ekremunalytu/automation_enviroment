"""Security settings API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ThresholdBoundsResponse(BaseModel):
    min_value: int
    max_value: int


class ThresholdsResponse(BaseModel):
    """Current effective thresholds + defaults + bounds for UI rendering."""

    values: dict[str, int]
    defaults: dict[str, int]
    bounds: dict[str, ThresholdBoundsResponse]
    keys: list[str]


class ThresholdsUpdateRequest(BaseModel):
    """Partial update; only supplied keys are written."""

    values: dict[str, int] = Field(default_factory=dict)
    updated_by: str | None = Field(default=None, max_length=128)


__all__ = [
    "ThresholdBoundsResponse",
    "ThresholdsResponse",
    "ThresholdsUpdateRequest",
]
