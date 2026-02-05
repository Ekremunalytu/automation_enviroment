"""
main.py
=======

FastAPI Application Entry Point
--------------------------------

This is the main entry point for the ExTrace VS Code Extension Security
Analysis & Automation API. It initializes the FastAPI application and
configures all components.

Application Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                         main.py                                 │
    │                    (Application Factory)                        │
    └─────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                      FastAPI Application                        │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │  │   Routers    │  │   Schemas    │  │  Database Session    │   │
    │  │  (core.py)   │  │ (schemas.py) │  │  (Dependency Inj.)   │   │
    │  └──────────────┘  └──────────────┘  └──────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘

Factory Pattern:
    This module uses the Application Factory pattern (create_app).
    Benefits:
    - Multiple instances possible for testing
    - Configuration can be injected
    - Easier to add middleware/routers programmatically

Running the Application:
    Development (with auto-reload):
        uvicorn main:app --reload --host 0.0.0.0 --port 8000

    Production (with workers):
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

    Or directly (development only):
        python main.py

API Documentation:
    After starting the server, visit:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - OpenAPI JSON: http://localhost:8000/openapi.json
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from core.config import settings
from routers.core import router as core_router


def create_app() -> FastAPI:
    """
    Application factory function - creates and configures FastAPI instance.

    This function follows the Factory Pattern, which allows:
    - Creating multiple app instances (useful for testing)
    - Configuring the app based on environment
    - Adding middleware and routers in a controlled manner

    Returns:
        FastAPI: Fully configured application instance

    Configuration Applied:
        - title: Project name from settings (shown in docs)
        - description: API description for documentation
        - version: Semantic version string
        - routers: All API route handlers attached

    Example Usage:
        # Standard usage
        app = create_app()

        # For testing with different settings
        def create_test_app():
            app = create_app()
            # Override dependencies for testing
            return app

    Future Enhancements:
        - Add CORS middleware for frontend integration
        - Add request logging middleware
        - Add exception handlers
        - Add startup/shutdown event handlers
        - Add authentication middleware
    """
    # Create FastAPI instance with metadata
    application = FastAPI(
        title=settings.project.NAME,
        description=settings.project.DESCRIPTION,
        version=settings.project.VERSION,
    )

    # Add middleware
    # GZip compression for large responses (minimum 2KB to avoid overhead on
    # small responses)
    application.add_middleware(GZipMiddleware, minimum_size=2000)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    # The core router contains all extension-related endpoints
    # Prefix and tags can be added here for organization:
    # application.include_router(core_router, prefix="/api/v1", tags=["extensions"])
    application.include_router(core_router)

    return application


# =============================================================================
# Application Instance
# =============================================================================

app = create_app()
"""
Global FastAPI application instance.

This is what uvicorn references when starting the server:
    uvicorn main:app

The instance is created at module import time, which means:
- Configuration is loaded immediately
- Database connections are established
- Routers are registered
- OpenAPI schema is generated
"""


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    """
    Direct execution entry point for development.

    This block only runs when the file is executed directly:
        python main.py

    For production, use uvicorn/gunicorn directly:
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

    Development usage:
        python main.py
        # Server starts at http://0.0.0.0:8000
        # Docs at http://0.0.0.0:8000/docs
    """
    import uvicorn

    # Start development server
    # Note: No --reload here, use uvicorn CLI for auto-reload
    uvicorn.run(
        app,
        host=settings.api.HOST,  # Listen on configured interface
        port=settings.api.PORT,  # Listen on configured port
    )
