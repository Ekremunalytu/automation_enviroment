"""FastAPI application entry point for ExTrace."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from core.config import settings
from routers.activations import router as activations_router
from routers.core import router as core_router
from routers.marketplace import router as marketplace_router


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
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
    application.include_router(core_router)
    application.include_router(activations_router)
    application.include_router(marketplace_router)

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api.HOST,
        port=settings.api.PORT,
        workers=1 if settings.api.DEBUG else settings.api.WORKERS,
        reload=settings.api.DEBUG,
    )
