"""Marketplace workflow router."""

import json
import logging
import threading
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.api.deps import get_db
from appcore.contracts.schemas import (
    AnalyzeJobStatusResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    MarketplaceDownloadRequest,
    MarketplaceDownloadResponse,
    MarketplaceExtension,
)
from appcore.db.session import SessionLocal
from appcore.storage.crud import (
    get_extension_activation_events,
    get_extension_contributes_all,
)
from scanner.executor import (
    ExecutorError,
    install_extension_in_executor,
    reset_executor_sandbox_state,
    run_playwright_automation,
)
from workflows.extension_catalog.service import (
    ExtensionManifestMismatchError,
    create_extension_from_directory,
)
from workflows.marketplace import client as marketplace_client
from workflows.marketplace.triggers import select_scenarios, write_trigger_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["marketplace"])
_JOB_LOCK = threading.Lock()
_ANALYSIS_JOBS: dict[str, dict[str, Any]] = {}


def _now() -> float:
    return time.time()


def _get_jobs_dir() -> Path:
    """Return the shared directory used for persisted job snapshots."""
    return Path(settings.project.OUTPUT_DIR) / "analysis_jobs"


def _get_job_file(job_id: str) -> Path:
    """Return the filesystem path for a persisted job snapshot."""
    return _get_jobs_dir() / f"{job_id}.json"


def _persist_job(job: dict[str, Any]) -> None:
    """Persist a job snapshot so status reads work across worker processes."""
    jobs_dir = _get_jobs_dir()
    jobs_dir.mkdir(parents=True, exist_ok=True)

    job_file = _get_job_file(job["job_id"])
    temp_file = job_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(job), encoding="utf-8")
    temp_file.replace(job_file)


def _load_persisted_job(job_id: str) -> dict[str, Any]:
    """Load a job snapshot from shared storage."""
    with open(_get_job_file(job_id), encoding="utf-8") as handle:
        job = json.load(handle)

    if not isinstance(job, dict):
        raise KeyError(job_id)

    return job


def _empty_job_steps() -> list[dict[str, str]]:
    return [
        {
            "name": "reset_sandbox",
            "status": "pending",
            "message": "Waiting for sandbox cleanup.",
        },
        {"name": "install_extension", "status": "pending", "message": "Queued."},
        {
            "name": "build_triggers",
            "status": "pending",
            "message": "Waiting for activation metadata.",
        },
        {
            "name": "run_monitoring",
            "status": "pending",
            "message": "Waiting for sandbox automation.",
        },
        {
            "name": "finalize_report",
            "status": "pending",
            "message": "Waiting for report export.",
        },
    ]


def _build_report_name(request: AnalyzeRequest, run_id: str) -> str:
    """Build a unique activation report filename for a single analysis run."""
    return (
        f"activation_report_{request.publisher}.{request.name}-"
        f"{request.version}-{run_id[:12]}.json"
    )


def _create_job_snapshot(request: AnalyzeRequest) -> dict[str, Any]:
    created_at = _now()
    job_id = uuid4().hex
    return {
        "job_id": job_id,
        "status": "queued",
        "publisher": request.publisher,
        "name": request.name,
        "version": request.version,
        "scenario": request.scenario,
        "current_step": None,
        "message": "Queued for sandbox analysis.",
        "steps": _empty_job_steps(),
        "report_path": _build_report_name(request, job_id),
        "install_output": None,
        "automation_output": None,
        "error_detail": None,
        "created_at": created_at,
        "started_at": None,
        "finished_at": None,
        "updated_at": created_at,
    }


def _store_job(job: dict[str, Any]) -> None:
    with _JOB_LOCK:
        _ANALYSIS_JOBS[job["job_id"]] = job
        _persist_job(job)


def _get_job_snapshot(job_id: str) -> dict[str, Any]:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is not None:
            return deepcopy(job)

    try:
        return _load_persisted_job(job_id)
    except FileNotFoundError as exc:
        raise KeyError(job_id) from exc


def _update_job(job_id: str, **updates: Any) -> None:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is None:
            job = _load_persisted_job(job_id)
            _ANALYSIS_JOBS[job_id] = job
        job.update(updates)
        job["updated_at"] = _now()
        _persist_job(job)


def _update_job_step(job_id: str, step_name: str, status: str, message: str) -> None:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is None:
            job = _load_persisted_job(job_id)
            _ANALYSIS_JOBS[job_id] = job
        for step in job["steps"]:
            if step["name"] == step_name:
                step["status"] = status
                step["message"] = message
                break
        job["current_step"] = step_name if status == "running" else job["current_step"]
        if status in {"completed", "skipped"} and job["current_step"] == step_name:
            job["current_step"] = None
        if status == "failed":
            job["current_step"] = step_name
        job["updated_at"] = _now()
        _persist_job(job)


def _fail_job(job_id: str, detail: str) -> None:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is None:
            job = _load_persisted_job(job_id)
            _ANALYSIS_JOBS[job_id] = job
        current_step = job.get("current_step")
        if current_step:
            for step in job["steps"]:
                if step["name"] == current_step:
                    step["status"] = "failed"
                    step["message"] = detail
                    break
        job.update(
            status="failed",
            message=detail,
            error_detail=detail,
            finished_at=_now(),
            updated_at=_now(),
        )
        _persist_job(job)


def _ensure_vsix_exists(request: AnalyzeRequest) -> Path:
    vsix_path = marketplace_client.get_vsix_path(
        request.publisher,
        request.name,
        request.version,
    )
    if not vsix_path.exists():
        raise FileNotFoundError(
            f"VSIX file not found: {vsix_path.name}. "
            "Download the extension first via /api/marketplace/download."
        )
    return vsix_path


def _build_trigger_payload(
    db: Session,
    request: AnalyzeRequest,
) -> tuple[str | None, list[str], str]:
    if request.scenario:
        return None, [], "Explicit scenario selected; smart trigger selection skipped."

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

    if not activation_events:
        return (
            None,
            [],
            "No stored activation events found; using default sandbox flow.",
        )

    events_data = [
        {"event_type": event.event_type, "event_value": event.event_value}
        for event in activation_events
    ]
    custom_editors = contributes.customEditors if contributes else None
    publisher_name = f"{request.publisher}.{request.name}"

    commands_data = None
    if contributes and contributes.commands:
        commands_data = [
            {"title": command.title, "command_id": command.command_id}
            for command in contributes.commands
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
    return (
        trigger_container_path,
        payload.selected_scenarios,
        (
            f"Selected {len(payload.selected_scenarios)} scenario(s) "
            "from activation metadata."
        ),
    )


def _execute_analysis_request(
    request: AnalyzeRequest,
    db: Session,
    progress_callback: Callable[[str, str, str], None] | None = None,
    report_name: str | None = None,
) -> AnalyzeResponse:
    def report(step_name: str, status: str, message: str) -> None:
        if progress_callback is not None:
            progress_callback(step_name, status, message)

    _ensure_vsix_exists(request)

    report(
        "reset_sandbox",
        "running",
        "Resetting executor sandbox to a clean baseline.",
    )
    try:
        reset_executor_sandbox_state()
    except ExecutorError:
        report(
            "reset_sandbox",
            "failed",
            "Sandbox reset failed before extension installation.",
        )
        raise
    report(
        "reset_sandbox",
        "completed",
        "Sandbox reset completed.",
    )

    report(
        "install_extension",
        "running",
        "Installing extension in the executor sandbox.",
    )
    try:
        install_output = install_extension_in_executor(
            request.publisher,
            request.name,
            request.version,
        )
    except ExecutorError:
        report(
            "install_extension",
            "failed",
            "Extension installation failed inside the sandbox.",
        )
        raise
    report(
        "install_extension",
        "completed",
        "Extension installed in sandbox.",
    )

    trigger_container_path: str | None = None
    trigger_message = "Using default sandbox flow."
    report(
        "build_triggers",
        "running",
        "Resolving activation events and contribution metadata.",
    )
    try:
        trigger_container_path, _, trigger_message = _build_trigger_payload(db, request)
        report("build_triggers", "completed", trigger_message)
    except (SQLAlchemyError, OSError, ValueError, TypeError, AttributeError) as exc:
        trigger_message = (
            "Trigger selection unavailable; continuing with default sandbox flow."
        )
        logger.warning(
            "Failed to build trigger payload for %s.%s: %s",
            request.publisher,
            request.name,
            exc,
        )
        report("build_triggers", "completed", trigger_message)

    report(
        "run_monitoring",
        "running",
        "Reloading VS Code under monitoring and executing automation scenarios.",
    )
    report_name = report_name or _build_report_name(request, uuid4().hex)
    report_container_path = f"/results/{report_name}"
    try:
        automation_output = run_playwright_automation(
            report_path=report_container_path,
            scenario=request.scenario,
            trigger_container_path=trigger_container_path,
            reload_before_run=True,
        )
    except ExecutorError:
        report(
            "run_monitoring",
            "failed",
            "Sandbox automation failed before the report could be finalized.",
        )
        raise
    report(
        "run_monitoring",
        "completed",
        "Sandbox automation finished.",
    )
    report(
        "finalize_report",
        "completed",
        f"Report exported to {report_name}.",
    )

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


def _map_executor_error(exc: ExecutorError) -> HTTPException:
    """Convert executor failures into endpoint-specific HTTP responses."""
    message = str(exc)
    if "install" in message.lower():
        detail = f"Failed to install extension in executor: {message}"
    else:
        detail = f"Automation failed: {message}"
    return HTTPException(status_code=502, detail=detail)


def _run_analysis_job(job_id: str, request: AnalyzeRequest) -> None:
    report_name = _get_job_snapshot(job_id)["report_path"] or _build_report_name(
        request,
        job_id,
    )
    _update_job(
        job_id,
        status="running",
        message="Starting sandbox analysis.",
        report_path=report_name,
        started_at=_now(),
    )

    db = SessionLocal()
    try:
        result = _execute_analysis_request(
            request,
            db,
            progress_callback=lambda step, status, message: _update_job_step(
                job_id,
                step,
                status,
                message,
            ),
            report_name=report_name,
        )
    except (FileNotFoundError, ExecutorError, OSError) as exc:
        _fail_job(job_id, str(exc))
        return
    except (SQLAlchemyError, ValueError, TypeError, AttributeError) as exc:
        _fail_job(job_id, str(exc))
        return
    finally:
        db.close()

    _update_job(
        job_id,
        status="completed",
        current_step=None,
        message=result.message,
        report_path=result.report_path,
        install_output=result.install_output,
        automation_output=result.automation_output,
        finished_at=_now(),
    )


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
        results = marketplace_client.search_marketplace(query.strip(), page_size)
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
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
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
    """Queue a sandbox analysis job and return its initial status."""
    try:
        _ensure_vsix_exists(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    job = _create_job_snapshot(request)
    _store_job(job)

    worker = threading.Thread(
        target=_run_analysis_job,
        args=(job["job_id"], request.model_copy(deep=True)),
        daemon=True,
    )
    worker.start()
    return _get_job_snapshot(job["job_id"])


@router.get(
    "/marketplace/analyze/{job_id}",
    response_model=AnalyzeJobStatusResponse,
)
def get_analysis_job(job_id: str) -> dict[str, Any]:
    """Return the latest status snapshot for an analysis job."""
    try:
        return _get_job_snapshot(job_id)
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
    try:
        return _execute_analysis_request(request, db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ExecutorError as exc:
        raise _map_executor_error(exc) from exc
