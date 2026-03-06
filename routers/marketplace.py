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

from core.config import settings
from core.deps import get_db
from crud.crud import get_extension_activation_events, get_extension_contributes_all
from scanner import marketplace as marketplace_scanner
from scanner.executor import (
    ExecutorError,
    install_extension_in_executor,
    reload_vscode_window,
    run_playwright_automation,
)
from scanner.service import create_extension_by_name
from scanner.triggers import select_scenarios, write_trigger_file
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
def analyze_extension(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """
    Install a downloaded extension in the executor sandbox
    and run Playwright automation with smart trigger selection.

    Flow:
        1. Verify that the .vsix file exists on disk.
        2. Install the extension in the executor container via
           ``code --install-extension``.
        3. Fetch activation events and contributes from DB to select
           relevant scenarios.
        4. Run the Playwright automation entrypoint with trigger data.

    Args:
        request: Publisher, name, version, and optional scenario.
        db: Database session (injected).

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

    # Step 1.5: Reload VS Code so the newly installed extension activates
    try:
        reload_output = reload_vscode_window()
        logger.info("VS Code reloaded: %s", reload_output.strip())
    except ExecutorError as exc:
        logger.warning("VS Code reload failed (non-fatal): %s", exc)

    # Step 2: Build trigger payload from DB data (best-effort)
    trigger_container_path: str | None = None
    if not request.scenario:
        try:
            activation_events = get_extension_activation_events(
                db,
                extension_name=request.name,
                extension_publisher=request.publisher,
                extension_version=request.version,
            )
            contributes = get_extension_contributes_all(
                db,
                extension_name=request.name,
                extension_publisher=request.publisher,
                extension_version=request.version,
            )

            if activation_events:
                events_data = [
                    {"event_type": e.event_type, "event_value": e.event_value}
                    for e in activation_events
                ]
                custom_editors = contributes.customEditors if contributes else None
                publisher_name = f"{request.publisher}.{request.name}"

                # Gather contributes.commands for dynamic invocation
                commands_data = None
                if contributes and contributes.commands:
                    commands_data = [
                        {"title": c.title, "command_id": c.command_id}
                        for c in contributes.commands
                    ]

                payload = select_scenarios(
                    events_data,
                    custom_editors,
                    publisher_name,
                    contributes_commands=commands_data,
                )
                trigger_container_path = write_trigger_file(
                    request.publisher,
                    request.name,
                    request.version,
                    payload,
                    output_dir=settings.project.OUTPUT_DIR,
                )
                logger.info(
                    "Smart triggers: %d scenarios for %s.%s",
                    len(payload.selected_scenarios),
                    request.publisher,
                    request.name,
                )
        except Exception:
            logger.warning(
                "Failed to build trigger payload for %s.%s, falling back to default",
                request.publisher,
                request.name,
                exc_info=True,
            )

    # Step 3: Run Playwright automation
    report_name = (
        f"activation_report_{request.publisher}.{request.name}-{request.version}.json"
    )
    report_container_path = f"/results/{report_name}"

    try:
        automation_output = run_playwright_automation(
            report_path=report_container_path,
            scenario=request.scenario,
            trigger_container_path=trigger_container_path,
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
