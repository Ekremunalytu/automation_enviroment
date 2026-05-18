"""Dedicated /api/health route — W15-5 I2 close (codex-2026-05-10-I2-ui-health-proxy).

Mounted with prefix=/api so the UI healthcheck flows through the nginx
/api/* reverse-proxy block. The legacy root /health route on
``extension_catalog_router`` is intentionally preserved for external
monitoring back-compat.
"""

from fastapi import APIRouter

from appcore.api.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check served via the /api/* reverse-proxy surface."""
    return {"status": settings.api.HEALTH_STATUS, "service": settings.project.NAME}
