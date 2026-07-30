"""Read-only appliance health contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SystemMetric(BaseModel):
    """One measured or runtime-derived service fact."""

    label: str
    value: str


class SystemServiceHealth(BaseModel):
    """Current health snapshot for one appliance service."""

    id: str
    name: str
    health: Literal["ok", "degraded", "down", "unknown"]
    status: str
    detail: str
    source: str
    metrics: list[SystemMetric]
    observations: list[str]


class SystemInventoryItem(BaseModel):
    """Runtime inventory fact observed from the API container."""

    label: str
    value: str


class SystemHealthResponse(BaseModel):
    """Aggregate, read-only health snapshot for the local appliance."""

    observed_at: datetime
    services: list[SystemServiceHealth]
    inventory: list[SystemInventoryItem]


__all__ = [
    "SystemHealthResponse",
    "SystemInventoryItem",
    "SystemMetric",
    "SystemServiceHealth",
]
