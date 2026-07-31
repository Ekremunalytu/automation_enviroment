"""Static decision-gate DTOs (ADR 0016 §Decision 1 and SMF honesty amendment)."""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import Annotated, cast

from pydantic import Field, model_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.detection.enums import ContractStrEnum

_UTC_FALLBACK = timezone.utc  # noqa: UP017
UTC = cast(tzinfo, getattr(datetime, "UTC", _UTC_FALLBACK))
BoundedInconclusiveReason = Annotated[str, Field(min_length=1, max_length=160)]


class StaticGateDecision(ContractStrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    INCONCLUSIVE = "inconclusive"


class StaticGateOutcome(StrictContractModel):
    """Outcome of the static decision gate over a StaticDetectionReport."""

    decision: StaticGateDecision
    blocked_by: list[str] = Field(default_factory=list)
    warned_by: list[str] = Field(default_factory=list)
    inconclusive_reasons: list[BoundedInconclusiveReason] = Field(
        default_factory=list, max_length=64
    )
    allow_reason: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_allow_reason(self) -> StaticGateOutcome:
        blocking = self.decision is not StaticGateDecision.ALLOW
        if blocking and self.allow_reason is not None:
            raise ValueError(
                "allow_reason must be None on WARN/BLOCK/INCONCLUSIVE outcomes."
            )
        return self

    @model_validator(mode="after")
    def validate_decision_consistency(self) -> StaticGateOutcome:
        """Every decision must carry a machine-readable cause.

        A terminal ``rejected_static`` job is only reachable through a BLOCK, so
        a BLOCK with no ``blocked_by`` would leave the rejection unexplained on
        the report / UI / log surfaces (observability hard rule). Symmetrically a
        WARN must name what it warned on, and an ALLOW must not smuggle
        blocker/warner ids that no downstream consumer would act on.
        """
        if self.decision is StaticGateDecision.BLOCK and not self.blocked_by:
            raise ValueError("BLOCK outcome must list at least one blocked_by id.")
        if self.decision is StaticGateDecision.WARN and not self.warned_by:
            raise ValueError("WARN outcome must list at least one warned_by id.")
        if (
            self.decision is StaticGateDecision.INCONCLUSIVE
            and not self.inconclusive_reasons
        ):
            raise ValueError(
                "INCONCLUSIVE outcome must list at least one inconclusive reason."
            )
        if self.decision is StaticGateDecision.ALLOW and (
            self.blocked_by or self.warned_by or self.inconclusive_reasons
        ):
            raise ValueError(
                "ALLOW outcome must have empty blocked_by, warned_by, and "
                "inconclusive_reasons."
            )
        if self.decision is StaticGateDecision.BLOCK and self.inconclusive_reasons:
            raise ValueError("BLOCK outcome must not carry inconclusive reasons.")
        if self.decision is StaticGateDecision.WARN and self.inconclusive_reasons:
            raise ValueError("WARN outcome must not carry inconclusive reasons.")
        if self.decision is StaticGateDecision.INCONCLUSIVE and self.blocked_by:
            raise ValueError("INCONCLUSIVE outcome must not carry blocked_by ids.")
        return self


__all__ = ["StaticGateDecision", "StaticGateOutcome"]
