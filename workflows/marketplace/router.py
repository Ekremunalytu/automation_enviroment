"""Marketplace workflow router."""

from __future__ import annotations

import threading
import zipfile
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
    OfflineExtension,
    OfflineIngestRequest,
    VsixExtractionMetrics,
    VsixThresholdBreachDetail,
)
from appcore.logging import get_extrace_logger
from packages.analysis_contracts import ExtensionIdentity
from packages.marketplace_identity import MarketplaceIdentityError
from workflows.executor_settings import load_dynamic_analysis_enabled
from workflows.extension_catalog.manifest_reader import PackageJsonReadError
from workflows.extension_catalog.service import (
    ExtensionManifestMismatchError,
    create_extension_from_directory,
    search_extension_by_name,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace import job_service
from workflows.marketplace import offline as offline_intake
from workflows.marketplace.analysis_errors import ActivationReportLoadError
from workflows.marketplace.analysis_reports import load_static_report_from_name
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
from workflows.marketplace.offline import OfflineIntakeError
from workflows.security_settings import load_vsix_thresholds
from workflows.security_settings.defaults import (
    VSIX_MAX_UNCOMPRESSED_SIZE_KEY,
    VSIX_THRESHOLD_DEFAULTS,
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


def _vsix_unpack_to_http(
    exc: marketplace_client.VSIXUnpackError,
    publisher: str,
    name: str,
    version: str,
) -> HTTPException:
    """Map a ``VSIXUnpackError`` to the structured 422 the UI popup consumes.

    Shared by the marketplace download and the offline-ingest endpoints so a
    threshold breach renders identically regardless of where the bytes came
    from. ``breach_kind`` may be ``None`` for legacy callers that raised the
    exception before the W12-* hardening pass; fall back to the opaque message
    so the typed 422 is never half-populated.
    """
    if (
        exc.breach_kind is None
        or exc.threshold_name is None
        or exc.threshold_value is None
        or exc.observed_value is None
    ):
        return HTTPException(status_code=422, detail=str(exc))
    logger.warning(
        "vsix_threshold_breach kind=%s threshold=%s value=%s observed=%s "
        "publisher=%s name=%s version=%s",
        exc.breach_kind,
        exc.threshold_name,
        exc.threshold_value,
        exc.observed_value,
        publisher,
        name,
        version,
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
        publisher=publisher,
        name=name,
        version=version,
    ).model_dump(mode="json")
    return HTTPException(status_code=422, detail=detail)


def _resolve_max_uncompressed_size(db: Session) -> int:
    """Operator-tuned ``vsix_max_uncompressed_size`` for the offline
    pre-read gate, so it agrees with the extraction-time guard (which
    loads the same value via ``persist_and_extract_vsix_bytes``). Falls
    back to the default ceiling when the setting row is unset."""
    thresholds = load_vsix_thresholds(db)
    return int(
        thresholds.get(
            VSIX_MAX_UNCOMPRESSED_SIZE_KEY,
            VSIX_THRESHOLD_DEFAULTS[VSIX_MAX_UNCOMPRESSED_SIZE_KEY],
        )
    )


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
        raise _vsix_unpack_to_http(
            exc, request.publisher, request.name, request.version
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

    return _register_extension_response(
        db,
        ext_dir,
        request.publisher,
        request.name,
        request.version,
        metrics_collector,
        success_message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            "downloaded and analyzed successfully."
        ),
        already_message=(
            f"Extension {request.publisher}.{request.name}@{request.version} "
            "is already downloaded and ready to analyze."
        ),
    )


def _register_extension_response(
    db: Session,
    ext_dir: Path,
    publisher: str,
    name: str,
    version: str,
    metrics_collector: dict[str, float],
    *,
    success_message: str,
    already_message: str,
) -> MarketplaceDownloadResponse:
    """Register an extracted extension in the catalog and build the response.

    Shared by the marketplace download and the offline-ingest endpoints: both
    extract into the canonical store, then register the manifest and surface
    the same ``MarketplaceDownloadResponse`` shape (incl. VSIX integrity
    metrics). An already-registered extension returns the idempotent
    ``already_message`` variant instead of 409.
    """
    try:
        extension = create_extension_from_directory(
            db,
            ext_dir,
            expected_name=name,
            expected_publisher=publisher,
            expected_version=version,
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
            name,
            extension_publisher=publisher,
            extension_version=version,
        )
        if existing_extension is None:
            raise HTTPException(
                status_code=409,
                detail=f"Extension already registered: {exc}",
            ) from exc

        return MarketplaceDownloadResponse(
            status="success",
            publisher=publisher,
            name=name,
            version=version,
            extension_dir=str(ext_dir),
            db_id=existing_extension.id,
            message=already_message,
            vsix_metrics=_metrics_payload(metrics_collector),
        )

    return MarketplaceDownloadResponse(
        status="success",
        publisher=publisher,
        name=name,
        version=version,
        extension_dir=str(ext_dir),
        db_id=extension.id,
        message=success_message,
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


@router.get("/marketplace/offline/list", response_model=list[OfflineExtension])
def list_offline_extensions_endpoint(
    db: Session = Depends(get_db),
) -> list[OfflineExtension]:
    """Enumerate readable ``.vsix`` packages in the offline intake directory.

    Air-gapped counterpart to ``/marketplace/search``: instead of querying
    the live marketplace, it lists packages the operator has dropped into
    ``settings.project.OFFLINE_DIR``. Unreadable *or* over-limit archives are
    skipped by the service (the latter under the same operator-tuned
    ``vsix_max_uncompressed_size`` the extractor enforces); only a filesystem
    fault on the directory itself is an error.
    """
    try:
        return offline_intake.list_offline_extensions(
            max_uncompressed_size=_resolve_max_uncompressed_size(db),
        )
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Offline intake directory unavailable: {exc}",
        ) from exc


@router.post(
    "/marketplace/offline/ingest",
    response_model=MarketplaceDownloadResponse,
)
def ingest_offline_extension_endpoint(
    request: OfflineIngestRequest,
    db: Session = Depends(get_db),
) -> MarketplaceDownloadResponse:
    """Stage one offline ``.vsix`` and register it — air-gapped download twin.

    Reuses the exact hardened extract path and catalog-registration helper as
    ``/marketplace/download``, so a threshold breach surfaces the same
    structured 422 and an already-present package returns idempotently.
    """
    metrics_collector: dict[str, float] = {}
    try:
        publisher, name, version, vsix_bytes = offline_intake.read_offline_vsix(
            request.filename,
            max_uncompressed_size=_resolve_max_uncompressed_size(db),
        )
    except OfflineIntakeError as exc:
        status = 404 if exc.reason == "not_found" else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except marketplace_client.VSIXUnpackError as exc:
        # F-2: an over-limit archive is rejected before read_bytes(); surface
        # the same structured 422 as an extraction-time breach. Identity is
        # not yet known (we reject before reading the manifest), so the
        # filename stands in for the package name.
        raise _vsix_unpack_to_http(exc, "", request.filename, "") from exc
    except MarketplaceIdentityError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Offline package manifest has an unsafe identity: {exc}",
        ) from exc
    except zipfile.BadZipFile as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Offline file is not a valid VSIX archive: {request.filename}",
        ) from exc
    except PackageJsonReadError as exc:
        raise HTTPException(
            status_code=500,
            detail=_package_json_error_detail(exc),
        ) from exc

    try:
        ext_dir = marketplace_client.persist_and_extract_vsix_bytes(
            publisher,
            name,
            version,
            vsix_bytes,
            db=db,
            metrics_out=metrics_collector,
        )
    except marketplace_client.VSIXUnpackError as exc:
        raise _vsix_unpack_to_http(exc, publisher, name, version) from exc
    except PackageJsonReadError as exc:
        raise HTTPException(
            status_code=500,
            detail=_package_json_error_detail(exc),
        ) from exc

    return _register_extension_response(
        db,
        ext_dir,
        publisher,
        name,
        version,
        metrics_collector,
        success_message=(
            f"Extension {publisher}.{name}@{version} "
            "ingested from offline intake and ready to analyze."
        ),
        already_message=(
            f"Extension {publisher}.{name}@{version} "
            "is already ingested and ready to analyze."
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
    dynamic_analysis_enabled = load_dynamic_analysis_enabled(db)

    try:
        vsix_path = ensure_vsix_exists(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # W26 / Stream 3 (B5): hash the exact .vsix this run will scan, at
    # analyze-start, so the row (created by reserve_job) and both report
    # producers (via the worker) are all bound to the same bytes. Streamed, so a
    # bounded archive costs milliseconds.
    vsix_sha256 = marketplace_client.compute_vsix_sha256(vsix_path)

    # S2 (W23 B3): before reserving the single-active slot, sweep any same-boot
    # `running` job whose heartbeat has gone stale. Without this a hung/crashed
    # prior worker would hold the slot and 409-block every fresh submit until an
    # API restart. No-op unless a running job is actually past the stale timeout.
    job_service.reap_stale_running_jobs(db=db)

    try:
        job = job_service.reserve_job(request, db=db, vsix_sha256=vsix_sha256)
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
        args=(
            job["job_id"],
            request.model_copy(deep=True),
            vsix_sha256,
            dynamic_analysis_enabled,
        ),
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
    # S2 (W23 B3): a status poll is the operator noticing the job. Sweep stale
    # same-boot `running` jobs first so a wedged run self-heals to terminal
    # `failed` in the view (and releases the single-active slot) instead of
    # appearing stuck `running` forever. No-op unless past the stale timeout.
    job_service.reap_stale_running_jobs(db=db)

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

    # ES-5 (ADR 0016): fold the persisted static pre-check report into the
    # response whenever the static gate ran (``static_report_path`` is set on the
    # ALLOW/WARN completion and the BLOCK ``rejected_static`` reject; NULL when
    # the flag was OFF). Read-side graceful degradation — a missing / unreadable
    # static artifact surfaces as a ``report_error`` note, never a 500.
    static_report_path = snapshot.get("static_report_path")
    if isinstance(static_report_path, str):
        static_report = load_static_report_from_name(static_report_path)
        if static_report is not None:
            snapshot["static_report"] = static_report.model_dump(mode="json")
        else:
            snapshot["static_report"] = None
            snapshot["report_error"] = (
                snapshot.get("report_error")
                or f"static_report_unavailable: {static_report_path}"
            )
    return snapshot


@router.post("/marketplace/analyze", response_model=AnalyzeResponse)
def analyze_extension(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    dynamic_analysis_enabled = load_dynamic_analysis_enabled(db)

    # W15-1 (Codex 2026-05-10 M10 close-out): single except clause over the
    # closed ``ANALYZE_ERROR_TYPES`` taxonomy so the sync entry and the
    # async ``run_analysis_job`` worker handle the same exception classes.
    # The helper maps each class to the status code that mirrors the async
    # ``fail_job`` semantics; arch parity gate
    # ``tests/architecture/test_analyze_error_taxonomy_parity.py`` pins both
    # surfaces to the same source-of-truth tuples.
    try:
        # W26 / Stream 3 (B5, review B5-2): bind the sync surface's verdict to the
        # analyzed bytes too. The async start_analysis_job path hashes at reserve
        # time; this entry must hash here, inside the taxonomy try so a missing
        # .vsix still maps to 404 (FileNotFoundError) instead of falling through to
        # execute_analysis_request's empty (unbound) stamp. ensure_vsix_exists only
        # resolves+stats (no staging); execute_analysis_request re-checks it.
        vsix_path = ensure_vsix_exists(request)
        vsix_sha256 = marketplace_client.compute_vsix_sha256(vsix_path)
        return execute_analysis_request(
            request,
            db,
            vsix_sha256=vsix_sha256,
            dynamic_analysis_enabled=dynamic_analysis_enabled,
        )
    except ANALYZE_ERROR_TYPES as exc:
        raise analyze_error_to_http_response(exc) from exc
