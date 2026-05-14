"""HTTP surface for operator-tunable security settings.

Endpoints:
- ``GET /api/settings/security/thresholds`` — current effective thresholds
  plus the canonical defaults and validation bounds (so the UI can render
  hint text and clamp input fields without duplicating the table).
- ``PUT /api/settings/security/thresholds`` — partial update; validates
  every supplied key against ``THRESHOLD_BOUNDS`` before any DB write.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from appcore.api.deps import get_db
from appcore.contracts.schemas import (
    ThresholdBoundsResponse,
    ThresholdsResponse,
    ThresholdsUpdateRequest,
)
from appcore.logging import get_extrace_logger
from workflows.security_settings.defaults import (
    THRESHOLD_BOUNDS,
    VSIX_THRESHOLD_DEFAULTS,
    VSIX_THRESHOLD_KEYS,
)
from workflows.security_settings.service import (
    SecuritySettingValidationError,
    load_vsix_thresholds,
    save_vsix_thresholds,
)

logger = get_extrace_logger("extrace.workflows.security_settings.router")

router = APIRouter(prefix="/api/settings/security", tags=["security-settings"])


def _build_response(values: dict[str, int]) -> ThresholdsResponse:
    return ThresholdsResponse(
        values=values,
        defaults=dict(VSIX_THRESHOLD_DEFAULTS),
        bounds={
            key: ThresholdBoundsResponse(
                min_value=bounds.min_value, max_value=bounds.max_value
            )
            for key, bounds in THRESHOLD_BOUNDS.items()
        },
        keys=list(VSIX_THRESHOLD_KEYS),
    )


@router.get("/thresholds", response_model=ThresholdsResponse)
def get_security_thresholds(
    db: Session = Depends(get_db),
) -> ThresholdsResponse:
    return _build_response(load_vsix_thresholds(db))


@router.put("/thresholds", response_model=ThresholdsResponse)
def update_security_thresholds(
    payload: Annotated[ThresholdsUpdateRequest, Body()],
    db: Session = Depends(get_db),
) -> ThresholdsResponse:
    try:
        merged = save_vsix_thresholds(
            db, values=payload.values, updated_by=payload.updated_by
        )
    except SecuritySettingValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_threshold_value",
                "key": exc.key,
                "value": exc.value,
                "reason": exc.reason,
            },
        ) from exc

    logger.info(
        "security_threshold_updated keys=%s updated_by=%r",
        list(payload.values.keys()),
        payload.updated_by,
    )
    return _build_response(merged)


__all__ = ["router"]
