"""Static decision-gate DTOs (ES-1, ADR 0016 §Decision 1: block-and-warn)."""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import cast

from pydantic import Field, model_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.detection.enums import ContractStrEnum

_UTC_FALLBACK = timezone.utc  # noqa: UP017
UTC = cast(tzinfo, getattr(datetime, "UTC", _UTC_FALLBACK))


class StaticGateDecision(ContractStrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


class StaticGateOutcome(StrictContractModel):
    """Outcome of the static decision gate over a StaticDetectionReport."""

    decision: StaticGateDecision
    blocked_by: list[str] = Field(default_factory=list)
    warned_by: list[str] = Field(default_factory=list)
    allow_reason: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_allow_reason(self) -> StaticGateOutcome:
        blocking = self.decision is not StaticGateDecision.ALLOW
        if blocking and self.allow_reason is not None:
            raise ValueError("allow_reason must be None on WARN/BLOCK outcomes.")
        return self


__all__ = ["StaticGateDecision", "StaticGateOutcome"]
