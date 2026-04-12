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
from workflows.extension_catalog.service import (
    ExtensionManifestMismatchError,
    create_extension_from_directory,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace.analysis_service import (
    ensure_vsix_exists,
    execute_analysis_request,
    map_executor_error,
    run_analysis_job,
)
from workflows.marketplace.job_store import (
    _ANALYSIS_JOBS,
    create_job_snapshot,
    fail_job,
    get_job_snapshot,
    load_persisted_job,
    store_job,
    update_job,
    update_job_step,
)
from workflows.marketplace.trigger_service import build_trigger_payload

_ANALYSIS_JOBS = _ANALYSIS_JOBS
_build_trigger_payload = build_trigger_payload
_create_job_snapshot = create_job_snapshot
_ensure_vsix_exists = ensure_vsix_exists
_execute_analysis_request = execute_analysis_request
_fail_job = fail_job
_get_job_snapshot = get_job_snapshot
_load_persisted_job = load_persisted_job
_map_executor_error = map_executor_error
_run_analysis_job = run_analysis_job
settings = app_settings
_store_job = store_job
_update_job = update_job
_update_job_step = update_job_step

router = APIRouter(prefix="/api", tags=["marketplace"])


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
    try:
        ext_dir: Path = marketplace_client.download_and_extract_vsix(
            request.publisher, request.name, request.version
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download extension: {exc}",
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


@router.post(
    "/marketplace/analyze/start",
    response_model=AnalyzeJobStatusResponse,
    status_code=202,
)
def start_analysis_job(request: AnalyzeRequest) -> dict[str, Any]:
    try:
        ensure_vsix_exists(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    job = create_job_snapshot(request)
    store_job(job)
    worker = threading.Thread(
        target=run_analysis_job,
        args=(job["job_id"], request.model_copy(deep=True)),
        daemon=True,
    )
    worker.start()
    return get_job_snapshot(job["job_id"])


@router.get("/marketplace/analyze/{job_id}", response_model=AnalyzeJobStatusResponse)
def get_analysis_job(job_id: str) -> dict[str, Any]:
    try:
        return get_job_snapshot(job_id)
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
    except ExecutorError as exc:
        raise map_executor_error(exc) from exc
