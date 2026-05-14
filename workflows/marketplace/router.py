"""Marketplace workflow router."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
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
    VsixExtractionMetrics,
    VsixThresholdBreachDetail,
)
from appcore.logging import get_extrace_logger
from packages.analysis_contracts import ExtensionIdentity
from workflows.extension_catalog.manifest_reader import PackageJsonReadError
from workflows.extension_catalog.service import (
    ExtensionManifestMismatchError,
    create_extension_from_directory,
    search_extension_by_name,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace import job_service
from workflows.marketplace.analysis_errors import ActivationReportLoadError
from workflows.marketplace.analysis_service import (
    ANALYZE_ERROR_TYPES,
    analyze_error_to_http_response,
    build_analysis_bundle_from_report_name,
    ensure_vsix_exists,
    execute_analysis_request,
    run_analysis_job,
)
from workflows.marketplace.job_service import (
    ActiveAnalysisJobError,
    JobNotCancellableError,
)

settings = app_settings
logger = get_extrace_logger("extrace.workflows.marketplace.router")

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
def search_marketplace(query: str, page_size: int = 10) -> list[MarketplaceExtension]:
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
    metrics_collector: dict[str, float] = {}
    try:
        ext_dir = marketplace_client.download_and_extract_vsix(
            request.publisher,
            request.name,
            request.version,
            db=db,
            metrics_out=metrics_collector,
        )
    except marketplace_client.VSIXUnpackError as exc:
        # Structured 422 so the UI can render a popup naming the specific
        # threshold and pointing the operator at Settings → Security.
        # ``breach_kind`` may be ``None`` for legacy callers that raised the
        # exception before the W12-* hardening pass; fall back to the opaque
        # message if any structured field is missing so the typed 422 is
        # never half-populated.
        if (
            exc.breach_kind is None
            or exc.threshold_name is None
            or exc.threshold_value is None
            or exc.observed_value is None
        ):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        logger.warning(
            "vsix_threshold_breach kind=%s threshold=%s value=%s observed=%s "
            "publisher=%s name=%s version=%s",
            exc.breach_kind,
            exc.threshold_name,
            exc.threshold_value,
            exc.observed_value,
            request.publisher,
            request.name,
            request.version,
        )
        detail = VsixThresholdBreachDetail(
            error="vsix_threshold_breach",
            breach_kind=cast(
                Literal["entry_count", "uncompressed_size", "compression_ratio"],
                exc.breach_kind,
            ),
            threshold_name=exc.threshold_name,
            threshold_value=exc.threshold_value,
            observed_value=exc.observed_value,
            message=str(exc),
            publisher=request.publisher,
            name=request.name,
            version=request.version,
        ).model_dump(mode="json")
        raise HTTPException(
            status_code=422,
            detail=detail,
        ) from exc
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
            vsix_metrics=_metrics_payload(metrics_collector),
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
        vsix_metrics=_metrics_payload(metrics_collector),
    )


def _metrics_payload(
    collected: dict[str, float],
) -> VsixExtractionMetrics | None:
    """Promote the mutable dict the marketplace client populates into the
    typed schema. Returns ``None`` for the idempotent re-download path
    (extension already on disk) where no fresh metrics were measured."""
    if not collected:
        return None
    return VsixExtractionMetrics(
        file_count=int(collected.get("file_count", 0)),
        uncompressed_size=int(collected.get("uncompressed_size", 0)),
        compressed_size=int(collected.get("compressed_size", 0)),
        compression_ratio=float(collected.get("compression_ratio", 0.0)),
        rejected_entry_count=int(collected.get("rejected_entry_count", 0)),
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


@router.post(
    "/marketplace/analyze/{job_id}/cancel",
    response_model=AnalyzeJobStatusResponse,
)
def cancel_analysis_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return job_service.cancel_job(job_id, db=db)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis job not found: {job_id}",
        ) from exc
    except JobNotCancellableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/marketplace/analyze/{job_id}", response_model=AnalyzeJobStatusResponse)
def get_analysis_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        snapshot = job_service.get_job_snapshot(job_id, db=db)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis job not found: {job_id}",
        ) from exc

    report_path = snapshot.get("report_path")
    if snapshot.get("status") == "completed" and isinstance(report_path, str):
        try:
            bundle = build_analysis_bundle_from_report_name(
                report_path,
                analyzed_extension=ExtensionIdentity(
                    publisher=str(snapshot.get("publisher", "unknown")),
                    name=str(snapshot.get("name", "unknown")),
                    version=str(snapshot.get("version", "unknown")),
                ),
            )
        except (ActivationReportLoadError, ValueError, ValidationError) as exc:
            logger.error(
                "Detection bundle build failed for job %s (report=%s): %s",
                job_id,
                report_path,
                exc,
            )
            snapshot["detection_report"] = None
            snapshot["report_error"] = f"activation_report_schema_invalid: {exc}"
        else:
            if bundle is not None:
                snapshot["detection_report"] = bundle.detection_report.model_dump(
                    mode="json"
                )
            else:
                snapshot["detection_report"] = None
                snapshot["report_error"] = f"activation_report_missing: {report_path}"
    return snapshot


@router.post("/marketplace/analyze", response_model=AnalyzeResponse)
def analyze_extension(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    # W15-1 (Codex 2026-05-10 M10 close-out): single except clause over the
    # closed ``ANALYZE_ERROR_TYPES`` taxonomy so the sync entry and the
    # async ``run_analysis_job`` worker handle the same exception classes.
    # The helper maps each class to the status code that mirrors the async
    # ``fail_job`` semantics; arch parity gate
    # ``tests/architecture/test_analyze_error_taxonomy_parity.py`` pins both
    # surfaces to the same source-of-truth tuples.
    try:
        return execute_analysis_request(request, db)
    except ANALYZE_ERROR_TYPES as exc:
        raise analyze_error_to_http_response(exc) from exc
