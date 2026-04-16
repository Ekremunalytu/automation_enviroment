"""Marketplace workflow router."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from appcore.api.config import settings as app_settings
from appcore.api.deps import get_db
from appcore.contracts.schemas import (
    AnalyzeJobStatusResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    MarketplaceDownloadRequest,
    MarketplaceDownloadResponse,
    MarketplaceExtension,
)
from executor.host import ExecutorError
from workflows.extension_catalog.manifest_reader import PackageJsonReadError
from workflows.extension_catalog.service import (
    ExtensionManifestMismatchError,
    create_extension_from_directory,
    search_extension_by_name,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace import job_service
from workflows.marketplace.analysis_service import (
    TriggerPlanError,
    ensure_vsix_exists,
    execute_analysis_request,
    map_executor_error,
    run_analysis_job,
)
from workflows.marketplace.job_service import ActiveAnalysisJobError

settings = app_settings

router = APIRouter(prefix="/api", tags=["marketplace"])


def _package_json_error_detail(exc: PackageJsonReadError) -> str:
    if exc.reason == "missing":
        detail = f"Downloaded extension package.json is missing: {exc.path}"
    elif exc.reason == "invalid_json":
        detail = f"Downloaded extension package.json contains invalid JSON: {exc.path}"
    else:
        detail = f"Downloaded extension package.json could not be read: {exc.path}"

    if exc.detail:
        return f"{detail}: {exc.detail}"
    return detail


@router.get("/marketplace/search", response_model=list[MarketplaceExtension])
def search_marketplace(query: str, page_size: int = 10) -> list[dict]:
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")

    page_size = max(1, min(page_size, 100))
    try:
        return marketplace_client.search_marketplace(query.strip(), page_size)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Marketplace API unavailable: {exc}",
        ) from exc


@router.post("/marketplace/download", response_model=MarketplaceDownloadResponse)
def download_marketplace_extension(
    request: MarketplaceDownloadRequest,
    db: Session = Depends(get_db),
) -> MarketplaceDownloadResponse:
    ext_dir: Path | None = None
    try:
        ext_dir = marketplace_client.download_and_extract_vsix(
            request.publisher, request.name, request.version
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download extension: {exc}",
        ) from exc
    except PackageJsonReadError as exc:
        raise HTTPException(
            status_code=500,
            detail=_package_json_error_detail(exc),
        ) from exc

    try:
        extension = create_extension_from_directory(
            db,
            ext_dir,
            expected_name=request.name,
            expected_publisher=request.publisher,
            expected_version=request.version,
        )
    except ExtensionManifestMismatchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except PackageJsonReadError as exc:
        raise HTTPException(
            status_code=500,
            detail=_package_json_error_detail(exc),
        ) from exc
    except ValueError as exc:
        existing_extension = search_extension_by_name(
            db,
            request.name,
            extension_publisher=request.publisher,
            extension_version=request.version,
        )
        if existing_extension is None:
            raise HTTPException(
                status_code=409,
                detail=f"Extension already registered: {exc}",
            ) from exc

        return MarketplaceDownloadResponse(
            status="success",
            publisher=request.publisher,
            name=request.name,
            version=request.version,
            extension_dir=str(ext_dir),
            db_id=existing_extension.id,
            message=(
                f"Extension {request.publisher}.{request.name}@{request.version} "
                "is already downloaded and ready to analyze."
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


@router.post(
    "/marketplace/analyze/start",
    response_model=AnalyzeJobStatusResponse,
    status_code=202,
)
def start_analysis_job(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        ensure_vsix_exists(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        job = job_service.reserve_job(request, db=db)
    except ActiveAnalysisJobError as exc:
        active_job = exc.active_job
        raise HTTPException(
            status_code=409,
            detail=(
                "Another sandbox analysis is already in progress. "
                "Wait for job "
                f"{active_job['job_id']} to finish before starting a new run."
            ),
        ) from exc

    worker = threading.Thread(
        daemon=False,
        name=f"analysis-{job['job_id'][:8]}",
        target=run_analysis_job,
        args=(job["job_id"], request.model_copy(deep=True)),
    )
    worker.start()
    return job_service.get_job_snapshot(job["job_id"], db=db)


@router.get("/marketplace/analyze/{job_id}", response_model=AnalyzeJobStatusResponse)
def get_analysis_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return job_service.get_job_snapshot(job_id, db=db)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis job not found: {job_id}",
        ) from exc


@router.post("/marketplace/analyze", response_model=AnalyzeResponse)
def analyze_extension(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    try:
        return execute_analysis_request(request, db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TriggerPlanError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ExecutorError as exc:
        raise map_executor_error(exc) from exc
