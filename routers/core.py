"""Core API router — extension CRUD and query endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.config import settings
from core.deps import get_db
from scanner import service
from schemas.schemas import (
    ExtensionActivationEventsSchema,
    ExtensionCapabilitiesSchema,
    ExtensionContributesCommandsSchema,
    ExtensionContributesSchema,
    ExtensionDetailSchema,
    ExtensionScriptsSchema,
    ScanRequest,
    SearchAllExtensionsInfo,
    SearchRequest,
)

# =============================================================================
# Router Configuration
# =============================================================================

router = APIRouter(tags=["core"])


@router.get("/")
def read_root():
    """API root — returns project info and doc links."""
    return {
        "Project": settings.project.NAME,
        "Version": settings.project.VERSION,
        "Status": settings.project.STATUS,
        "Docs": settings.api.DOCS_URL,
    }


@router.get("/health")
def health_check():
    """Health check for monitoring and orchestrators."""
    return {"status": settings.api.HEALTH_STATUS, "service": settings.project.NAME}


# =============================================================================
# Extension Search Endpoints
# =============================================================================


@router.get("/searchExtension", response_model=ExtensionDetailSchema)
def search_extension(params: SearchRequest = Depends(), db: Session = Depends(get_db)):
    """Search for a single extension by exact name (+ optional publisher/version)."""
    try:
        result = service.search_extension_by_name(
            db=db,
            extension_name=params.name,
            extension_publisher=params.publisher,
            extension_version=params.version,
        )

        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")

        return result

    except HTTPException as http_exc:
        raise http_exc

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/getExtensionsBaseInfo", response_model=list[SearchAllExtensionsInfo])
def get_extensions_base_info(db: Session = Depends(get_db)):
    """List all extensions with minimal fields (id, name, publisher, etc.)."""
    try:
        result = service.get_all_extensions_basic(db)

        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/getExtensionsAllInfo", response_model=list[ExtensionDetailSchema])
def get_extensions_all_info(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int | None = Query(default=None, ge=1, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """List all extensions with full detail. Supports skip/limit pagination."""
    try:
        result = service.get_all_extensions_all(db, skip=skip, limit=limit)

        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.post("/createExtension", response_model=ExtensionDetailSchema)
def create_extension(request: ScanRequest, db: Session = Depends(get_db)):
    """Scan extensions/ for matching name, parse package.json, persist to DB."""
    try:
        result = service.create_extension_by_name(db, request.name)

        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")

        return result

    except HTTPException as http_exc:
        raise http_exc

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.delete("/deleteExtension", response_model=dict)
def delete_extension(params: SearchRequest = Depends(), db: Session = Depends(get_db)):
    """Delete an extension. Provide publisher+version for unambiguous deletion."""
    try:
        deleted = service.delete_extension_by_name(
            db, params.name, params.publisher, params.version
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Extension not found")

        return {"message": f"Extension '{params.name}' deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/getExtensionScripts", response_model=list[ExtensionScriptsSchema])
def get_extension_scripts(
    params: SearchRequest = Depends(), db: Session = Depends(get_db)
):
    """Retrieve npm scripts defined in an extension's package.json."""
    try:
        result = service.get_extension_scripts(
            db,
            extension_name=params.name,
            extension_publisher=params.publisher,
            extension_version=params.version,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")

        return result
    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/getExtensionActivationEvents",
    response_model=list[ExtensionActivationEventsSchema],
)
def get_extension_activation_events(
    params: SearchRequest = Depends(), db: Session = Depends(get_db)
):
    """Retrieve activation events for an extension."""
    try:
        result = service.get_extension_activation_events(
            db,
            extension_name=params.name,
            extension_publisher=params.publisher,
            extension_version=params.version,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/getExtensionCapabilities",
    response_model=ExtensionCapabilitiesSchema,
)
def get_extension_capabilities(
    params: SearchRequest = Depends(), db: Session = Depends(get_db)
):
    """Retrieve capability declarations for an extension."""
    try:
        result = service.get_extension_capabilites(
            db,
            extension_name=params.name,
            extension_publisher=params.publisher,
            extension_version=params.version,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/getExtensionContributesAll", response_model=ExtensionContributesSchema)
def get_extension_contributes_all(
    params: SearchRequest = Depends(), db: Session = Depends(get_db)
):
    try:
        result = service.get_extension_contributes_all(
            db,
            extension_name=params.name,
            extension_publisher=params.publisher,
            extension_version=params.version,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/getExtensionContributesCommands",
    response_model=list[ExtensionContributesCommandsSchema],
)
def get_extension_contributes_commands(
    params: SearchRequest = Depends(), db: Session = Depends(get_db)
):
    try:
        result = service.get_extension_contributes_commands(
            db,
            extension_name=params.name,
            extension_publisher=params.publisher,
            extension_version=params.version,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
