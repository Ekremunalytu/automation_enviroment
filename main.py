"""FastAPI application entry point for ExTrace."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.exc import SQLAlchemyError

from appcore.api.config import settings
from appcore.api.health_router import router as health_router
from appcore.logging import (
    install_extrace_log_context_filter,
    set_executor_fingerprint_provider,
)
from executor.runtime_fingerprint import executor_fingerprint_short
from workflows.activation_reports.router import router as activation_reports_router
from workflows.extension_catalog.router import router as extension_catalog_router
from workflows.marketplace.job_service import recover_interrupted_jobs
from workflows.marketplace.router import router as marketplace_router
from workflows.security_settings.router import router as security_settings_router


def validate_runtime_settings() -> None:
    """Fail fast when runtime settings violate marketplace job guarantees."""
    if settings.api.WORKERS != 1:
        raise RuntimeError(
            "ExTrace requires API_WORKERS=1 because marketplace analysis jobs "
            "are managed as a single-worker sandbox queue."
        )


def should_recover_interrupted_jobs() -> bool:
    """Allow tooling to build the app without touching job storage."""
    return os.getenv("EXTRACE_SKIP_JOB_RECOVERY", "").lower() not in {
        "1",
        "true",
        "yes",
    }


def create_app(*, recover_jobs: bool = True) -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    validate_runtime_settings()
    # W14-5: install the `extrace.*` LogContextFilter early so every log
    # record emitted across the app lifetime carries the W14-5 structured
    # field contract (run_id, executor_fingerprint). Idempotent.
    install_extrace_log_context_filter()
    # W14-5 sub-commit 3: wire the executor runtime fingerprint provider
    # into the appcore.logging filter chain. The provider is registered
    # at app boot so every subsequent log record carries the short
    # commit SHA without per-call wiring.
    set_executor_fingerprint_provider(executor_fingerprint_short)
    application = FastAPI(
        title=settings.project.NAME,
        description=settings.project.DESCRIPTION,
        version=settings.project.VERSION,
        debug=settings.api.DEBUG,
        docs_url=settings.api.DOCS_URL,
        redoc_url=settings.api.REDOC_URL,
        openapi_url=settings.api.OPENAPI_URL,
    )

    # Middleware
    application.add_middleware(
        GZipMiddleware,
        minimum_size=settings.api.GZIP_MINIMUM_SIZE,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_allow_origins,
        allow_credentials=settings.api.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.api.cors_allow_methods,
        allow_headers=settings.api.cors_allow_headers,
    )

    # Routers
    application.include_router(extension_catalog_router)
    application.include_router(activation_reports_router)
    application.include_router(marketplace_router)
    application.include_router(security_settings_router)
    application.include_router(health_router)

    if recover_jobs:
        try:
            recover_interrupted_jobs()
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Marketplace analysis job storage is unavailable; run migrations "
                "and verify DB connectivity before starting the API."
            ) from exc
    return application


app = create_app(recover_jobs=should_recover_interrupted_jobs())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api.HOST,
        port=settings.api.PORT,
        workers=1 if settings.api.DEBUG else settings.api.WORKERS,
        reload=settings.api.DEBUG,
    )
