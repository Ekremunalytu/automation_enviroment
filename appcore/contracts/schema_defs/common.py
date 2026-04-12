"""Shared schema enums and primitives."""

from __future__ import annotations

from enum import StrEnum


class CapabilitySupportState(StrEnum):
    """Maps to the PostgreSQL enum 'capability_support_state'."""

    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    LIMITED = "limited"


__all__ = ["CapabilitySupportState"]
