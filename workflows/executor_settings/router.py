"""HTTP surface for operator-tunable executor preferences."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from appcore.api.deps import get_db
from appcore.contracts.schemas import (
    ExecutorPreferencesResponse,
    ExecutorPreferencesUpdateRequest,
)
from appcore.logging import get_extrace_logger
from workflows.executor_settings.service import (
    load_dynamic_analysis_enabled,
    save_dynamic_analysis_enabled,
)

logger = get_extrace_logger("extrace.workflows.executor_settings.router")

router = APIRouter(prefix="/api/settings/executor", tags=["executor-settings"])


@router.get("/preferences", response_model=ExecutorPreferencesResponse)
def get_executor_preferences(
    db: Session = Depends(get_db),
) -> ExecutorPreferencesResponse:
    return ExecutorPreferencesResponse(
        dynamic_analysis_enabled=load_dynamic_analysis_enabled(db)
    )


@router.put("/preferences", response_model=ExecutorPreferencesResponse)
def update_executor_preferences(
    payload: Annotated[ExecutorPreferencesUpdateRequest, Body()],
    db: Session = Depends(get_db),
) -> ExecutorPreferencesResponse:
    enabled = save_dynamic_analysis_enabled(
        db,
        enabled=payload.dynamic_analysis_enabled,
        updated_by=payload.updated_by,
    )
    logger.info(
        "executor_preference_updated dynamic_analysis_enabled=%s updated_by=%r",
        enabled,
        payload.updated_by,
    )
    return ExecutorPreferencesResponse(dynamic_analysis_enabled=enabled)


__all__ = ["router"]
