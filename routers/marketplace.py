"""
routers/marketplace.py
======================

VS Code Marketplace API Router
-------------------------------

Endpoints:
    GET  /api/marketplace/search   - Search the VS Code Marketplace
    POST /api/marketplace/download - Download, extract, and register a VSIX
"""

import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.deps import get_db
from scanner import marketplace as marketplace_scanner
from scanner.executor import (
    ExecutorError,
    install_extension_in_executor,
    run_playwright_automation,
)
from scanner.service import create_extension_by_name
from schemas.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    MarketplaceDownloadRequest,
    MarketplaceDownloadResponse,
    MarketplaceExtension,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["marketplace"])


@router.get("/marketplace/search", response_model=list[MarketplaceExtension])
def search_marketplace(query: str, page_size: int = 10) -> list[dict]:
    """
    Search the VS Code Marketplace for extensions.

    Args:
        query: Search term (required, non-empty).
        page_size: Number of results to return (1-100, default 10).

    Returns:
        List of matching extensions with metadata.

    Raises:
        400: Empty query string.
        502: Upstream Marketplace API unavailable.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")

    page_size = max(1, min(page_size, 100))

    try:
        results = marketplace_scanner.search_marketplace(query.strip(), page_size)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Marketplace API unavailable: {exc}",
        ) from exc

    return results


@router.post("/marketplace/download", response_model=MarketplaceDownloadResponse)
def download_marketplace_extension(
    request: MarketplaceDownloadRequest,
    db: Session = Depends(get_db),
) -> MarketplaceDownloadResponse:
    """
    Download a VS Code extension from the Marketplace and register it in the database.

    Flow:
        1. Download the VSIX package and extract it to the extensions/ directory.
        2. Call create_extension_by_name() to parse package.json and persist to DB.

    Args:
        request: Publisher, name, and version of the extension to download.

    Returns:
        Download status, extracted directory path, and database ID.

    Raises:
        409: Extension already exists in the database.
        500: Extension extracted but package.json could not be found or parsed.
        502: Network or upstream Marketplace error.
    """
    try:
        ext_dir: Path = marketplace_scanner.download_and_extract_vsix(
            request.publisher, request.name, request.version
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download extension: {exc}",
        ) from exc

    try:
        extension = create_extension_by_name(db, request.name)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Extension already registered: {exc}",
        ) from exc

    if extension is None:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Extension extracted to {ext_dir} but package.json "
                "was not found or could not be parsed."
            ),
        )

    return MarketplaceDownloadResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        extension_dir=str(ext_dir),
        db_id=extension.id,
        message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            "downloaded and analyzed successfully."
        ),
    )


@router.post("/marketplace/analyze", response_model=AnalyzeResponse)
def analyze_extension(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Install a downloaded extension in the executor sandbox
    and run Playwright automation.

    Flow:
        1. Verify that the .vsix file exists on disk.
        2. Install the extension in the executor container via
           ``code --install-extension``.
        3. Run the Playwright automation entrypoint.

    Args:
        request: Publisher, name, version, and optional scenario.

    Returns:
        Analysis status with install/automation output and report path.

    Raises:
        404: .vsix file not found (extension not downloaded yet).
        502: Executor command failed.
    """
    vsix_path = marketplace_scanner.get_vsix_path(
        request.publisher, request.name, request.version
    )

    if not vsix_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"VSIX file not found: {vsix_path.name}. "
                "Download the extension first via /api/marketplace/download."
            ),
        )

    # Step 1: Install extension in executor container
    try:
        install_output = install_extension_in_executor(
            request.publisher, request.name, request.version
        )
    except ExecutorError as exc:
        logger.error("Extension install failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to install extension in executor: {exc}",
        ) from exc

    # Step 2: Run Playwright automation
    report_name = (
        f"activation_report_{request.publisher}.{request.name}-{request.version}.json"
    )
    report_container_path = f"/results/{report_name}"

    try:
        automation_output = run_playwright_automation(
            report_path=report_container_path,
            scenario=request.scenario,
        )
    except ExecutorError as exc:
        logger.error("Playwright automation failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Automation failed: {exc}",
        ) from exc

    return AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            "installed and analyzed successfully."
        ),
        install_output=install_output,
        automation_output=automation_output,
        report_path=report_name,
    )
