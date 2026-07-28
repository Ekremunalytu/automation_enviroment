"""Read-only appliance health API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from appcore.api.deps import get_db
from appcore.contracts.schemas import SystemHealthResponse
from workflows.system_health.service import build_system_health

router = APIRouter(prefix="/api/system", tags=["system-health"])


@router.get("/health", response_model=SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)) -> SystemHealthResponse:
    return build_system_health(db)


__all__ = ["router"]
