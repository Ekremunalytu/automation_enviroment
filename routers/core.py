"""
routers/core.py
===============

Core API Router - Main HTTP Endpoints
--------------------------------------

This module defines the primary REST API endpoints for the ExTrace
VS Code Extension Security Scanner. It serves as the HTTP interface
layer, handling all incoming requests and responses.

Architecture Position:
    **Router (HTTP/REST)** → Service Layer → CRUD → Database
    
    Routers handle:
    - HTTP request parsing and validation
    - Dependency injection (database sessions)
    - Response serialization (via Pydantic models)
    - HTTP error code mapping

API Design:
    This API follows RESTful conventions with some RPC-style endpoints
    for specific operations like scanning.

Endpoints Summary:
    ┌─────────────────────────────────────────────────────────────────┐
    │ Method │ Endpoint              │ Description                   │
    ├────────┼───────────────────────┼───────────────────────────────┤
    │ GET    │ /                     │ API info and health check     │
    │ GET    │ /health               │ Service health status         │
    │ GET    │ /searchExtension      │ Find extension by name        │
    │ GET    │ /getExtensionsBaseInfo│ List extensions (minimal)     │
    │ GET    │ /getExtensionsAllInfo │ List extensions (full data)   │
    │ POST   │ /createExtension      │ Scan and create extension     │
    └─────────────────────────────────────────────────────────────────┘

Error Handling Strategy:
    - 400 Bad Request: Validation errors (ValueError)
    - 404 Not Found: Extension not found in DB or filesystem
    - 409 Conflict: Duplicate extension (unique constraint)
    - 500 Internal Server Error: Unexpected errors

Authentication:
    Currently: None (single-user isolated sandbox)
    Future: API key or OAuth2 for production deployment

Rate Limiting:
    Currently: None
    Future: Consider implementing for external access
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from schemas.schemas import (
    ExtensionSchema, 
    ScanRequest, 
    SearchRequest, 
    SearchAllExtensionsInfo, 
    SearchAllExtensionsAllInfo
)
from core.deps import get_db
from scanner import service


# =============================================================================
# Router Configuration
# =============================================================================

router = APIRouter(
    tags=["core"]  # Groups endpoints under "core" in Swagger UI
    # prefix="/api/v1"  # Uncomment for API versioning
)


# =============================================================================
# Health & Info Endpoints
# =============================================================================

@router.get("/")
def read_root():
    """
    API Root - Returns basic project information.
    
    This endpoint serves as the API landing page and provides
    basic information about the service for developers.
    
    Returns:
        dict: Project metadata including name, version, and doc links
    
    Response Example:
        {
            "Project": "Extrace",
            "Version": "0.1",
            "Status": "Active",
            "Docs": "/docs"
        }
    
    Use Cases:
        - Quick verification that API is reachable
        - Discovering API documentation location
        - Checking current version deployment
    """
    return {
        "Project": "Extrace",
        "Version": "0.1",
        "Status": "Active",
        "Docs": "/docs"  # Points to auto-generated Swagger UI
    }


@router.get("/health")
def health_check():
    """
    Health Check Endpoint for monitoring systems.
    
    Returns a simple OK status indicating the service is running.
    Used by container orchestrators, load balancers, and monitoring
    systems to verify service availability.
    
    Returns:
        dict: Health status with service name
    
    Response Example:
        {"status": "OK", "service": "Extrace API"}
    
    Monitoring Integration:
        - Docker HEALTHCHECK instruction
        - Kubernetes liveness/readiness probes
        - Load balancer health checks
        - Uptime monitoring services
    
    Future Improvements:
        - Add database connectivity check
        - Add filesystem accessibility check
        - Add memory/CPU metrics
        - Add dependency status (PostgreSQL, etc.)
    """
    return {
        "status": "OK",
        "service": "Extrace API"
    }


# =============================================================================
# Extension Search Endpoints
# =============================================================================

@router.get("/searchExtension", response_model=ExtensionSchema)
def search_extension(
    params: SearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Search for a single extension by exact name.
    
    Looks up an extension in the database by its exact name field.
    Returns complete extension details if found.
    
    Args:
        params: Query parameters containing extension name
                Provided via FastAPI Depends() for validation
        db: Database session provided by dependency injection
    
    Query Parameters:
        name (str): Exact extension name to search for
    
    Returns:
        ExtensionSchema: Complete extension data
    
    Raises:
        HTTPException 400: Invalid search parameters
        HTTPException 404: Extension not found
        HTTPException 500: Internal server error
    
    Example Request:
        GET /searchExtension?name=python
    
    Example Response:
        {
            "name": "python",
            "publisher": "ms-python",
            "engines": {"vscode": "^1.95.0"},
            "description": "Python language support...",
            ...
        }
    
    Note:
        This is an exact-match search. For partial/fuzzy search,
        a future endpoint with different semantics would be needed.
    """
    try:
        # Delegate to service layer for business logic
        result = service.search_extension_by_name(db=db, extension_name=params.name)
        
        if result is None:
            # Extension not found in database
            raise HTTPException(status_code=404, detail="Extension not found")
        
        return result
        
    except ValueError as e:
        # Business logic validation error
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Log unexpected errors for debugging
        print(f"Error in search_extension: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/getExtensionsBaseInfo", response_model=List[SearchAllExtensionsInfo])
def get_extensions_base_info(db: Session = Depends(get_db)):
    """
    List all extensions with minimal information.
    
    Returns a lightweight list of all extensions suitable for
    gallery views, search results, or selection dropdowns.
    
    Only includes essential fields:
        - id: Database reference
        - name: Extension identifier
        - publisher: Publisher name
        - description: Brief description
        - icon: Icon URL for thumbnails
    
    Args:
        db: Database session from dependency injection
    
    Returns:
        List[SearchAllExtensionsInfo]: Array of extension summaries
    
    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 404: No extensions found (empty database)
        HTTPException 500: Internal server error
    
    Example Request:
        GET /getExtensionsBaseInfo
    
    Example Response:
        [
            {
                "id": 1,
                "name": "python",
                "publisher": "ms-python",
                "description": "Python support...",
                "icon": "https://..."
            },
            ...
        ]
    
    Performance:
        Optimized for large datasets by excluding heavy fields
        like engines, badges, and markdown content.
    """
    try:
        result = service.get_all_extensions_basic(db)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        print(f"Error in get_extensions_base_info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/getExtensionsAllInfo", response_model=List[SearchAllExtensionsAllInfo])
def get_extensions_all_info(db: Session = Depends(get_db)):
    """
    List all extensions with complete information.
    
    Returns full details for all extensions in the database.
    Use sparingly for large datasets due to payload size.
    
    Includes all ExtensionSchema fields plus:
        - id: Database primary key
    
    Args:
        db: Database session from dependency injection
    
    Returns:
        List[SearchAllExtensionsAllInfo]: Array of complete extension data
    
    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 404: No extensions found
        HTTPException 500: Internal server error
    
    Example Request:
        GET /getExtensionsAllInfo
    
    Example Response:
        [
            {
                "id": 1,
                "name": "python",
                "publisher": "ms-python",
                "engines": {"vscode": "^1.95.0"},
                "license": "MIT",
                "displayName": "Python",
                "description": "...",
                "categories": [...],
                ...
            },
            ...
        ]
    
    Use Cases:
        - Data export/backup
        - Full comparison analysis
        - Administrative reporting
    
    Warning:
        Returns large payloads. For production, consider:
        - Pagination implementation
        - Field selection parameters
        - Caching layer
    """
    try:
        result = service.get_all_extensions_all(db)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        print(f"Error in get_extensions_all_info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# =============================================================================
# Extension Creation Endpoints
# =============================================================================

@router.post("/createExtension", response_model=ExtensionSchema)
def create_extension(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Scan and create a new extension in the database.
    
    This is the main "ingestion" endpoint that:
    1. Searches the extensions/ directory for the named extension
    2. Parses and validates its package.json
    3. Persists the metadata to the PostgreSQL database
    
    Args:
        request: Request body containing extension name to scan
        db: Database session from dependency injection
    
    Request Body:
        {
            "name": "extension-name"
        }
    
    Returns:
        ExtensionSchema: Created extension data with all fields
    
    Raises:
        HTTPException 404: Extension not found in filesystem
        HTTPException 409: Extension already exists in database
        HTTPException 500: Internal server error
    
    Example Request:
        POST /createExtension
        Content-Type: application/json
        {"name": "python"}
    
    Example Response:
        {
            "name": "python",
            "publisher": "ms-python",
            "engines": {"vscode": "^1.95.0"},
            ...
        }
    
    Workflow:
        Request → Scan extensions/ → Parse JSON → Validate → Insert DB
    
    Error Scenarios:
        - Extension name not found → 404
        - Duplicate publisher+name → 409
        - Invalid package.json → 500 (validation error)
        - Database connection error → 500
    """
    try:
        # Service layer handles filesystem scan + validation + DB insert
        result = service.create_extension_by_name(db, request.name)
        
        if result is None:
            # Extension not found in extensions/ directory
            raise HTTPException(status_code=404, detail="Extension not found")
        
        return result
        
    except ValueError as e:
        # Duplicate extension - unique constraint violation
        # Re-raised as 409 Conflict per HTTP semantics
        raise HTTPException(status_code=409, detail=str(e))
        
    except Exception as e:
        # Log and wrap unexpected errors
        print(f"Error in create_extension: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
