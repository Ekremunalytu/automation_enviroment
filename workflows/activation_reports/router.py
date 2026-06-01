"""Activation reports workflow router."""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi import Path as PathParam
from pydantic import ValidationError

from appcore.api.config import settings
from appcore.contracts.schema_defs.activation_reports import ActivationReportResponse
from appcore.contracts.schema_defs.report_bundle import ReportBundle
from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
)
from appcore.contracts.validators import ACTIVATION_REPORT_NAME_RE
from packages.analysis_contracts import (
    ActivationReport,
    ActivationReportFileSummary,
    ExtensionIdentity,
)
from packages.analysis_engine import run_detection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["activations"])
_REPORT_PATTERNS = ("activation_report*.json",)
# The marketplace flow names an activation report
# ``activation_report_{slug}-{job_id[:12]}.json`` (job_service.build_report_name)
# and persists its static pre-check next to it as ``static_report_{job_id}.json``.
# The shared 12-hex ``job_id`` prefix is the only deterministic link between the
# two files, so the static sibling is resolved by globbing on that token.
_RUN_ID_TOKEN_RE = re.compile(r"^[0-9a-f]{12}$")


def _get_output_dir() -> Path:
    """Return the output directory path from settings."""
    return Path(settings.project.OUTPUT_DIR)


def _list_report_files() -> list[Path]:
    """
    List all JSON report files in the output directory, sorted by
    modification time (newest first).

    Names are filtered through ``ACTIVATION_REPORT_NAME_RE`` (W9-6b) so a
    locally-writable file that happens to match the glob but not the
    canonical slug shape (e.g. ``activation_report_evil.json``) does not
    surface to API consumers. The single-name endpoints already gate
    inputs through the same regex via FastAPI ``Path(..., pattern=...)``;
    this listing-side filter closes the same defense-in-depth loop.
    """
    output_dir = _get_output_dir()
    if not output_dir.exists():
        return []
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in _REPORT_PATTERNS:
        for file_path in output_dir.glob(pattern):
            if not ACTIVATION_REPORT_NAME_RE.match(file_path.name):
                continue
            resolved = file_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(file_path)
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def _read_report_payload(path: Path, *, _retries: int = 3) -> dict[str, Any]:
    """Read and parse a JSON report file payload.

    Retries on transient OSError (e.g. Errno 35 on macOS Docker VirtioFS).
    """
    last_err: Exception | None = None
    for attempt in range(_retries):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            break
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read report file: {path.name} — {e}",
            ) from e
        except OSError as e:
            last_err = e
            if attempt < _retries - 1:
                time.sleep(0.3)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read report file: {path.name} — {last_err}",
        ) from last_err

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail=f"Report file must contain a JSON object: {path.name}",
        )
    return data


def _format_contract_error(path: Path, exc: ValidationError) -> str:
    """Build a compact validation detail for report contract failures."""
    errors = exc.errors()
    if not errors:
        return (
            "Report file failed activation report contract validation: "
            f"{path.name} (invalid activation report payload)"
        )

    first_error = errors[0]
    location = ".".join(str(part) for part in first_error["loc"])
    message = str(first_error["msg"])
    if location:
        return (
            "Report file failed activation report contract validation: "
            f"{path.name} ({location}: {message})"
        )
    return (
        "Report file failed activation report contract validation: "
        f"{path.name} ({message})"
    )


def _read_report(path: Path, *, _retries: int = 3) -> ActivationReport:
    """Read, parse, and validate an activation report."""
    payload = _read_report_payload(path, _retries=_retries)
    try:
        return ActivationReport.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail=_format_contract_error(path, exc),
        ) from exc


def _identity_from_report_name(
    name: str,
    report: ActivationReport,
) -> ExtensionIdentity:
    summary = report.summary if isinstance(report.summary, dict) else {}
    version = str(summary.get("target_extension_version", "unknown"))
    publisher, separator, extension_name = report.target_extension_expected.partition(
        "."
    )
    if not separator:
        publisher = "unknown"
        extension_name = report.target_extension_expected or "unknown"

    if name.startswith("activation_report_") and name.endswith(".json"):
        remainder = name.removeprefix("activation_report_").removesuffix(".json")
        try:
            extension_id, parsed_version, _ = remainder.rsplit("-", 2)
        except ValueError:
            extension_id = ""
        else:
            parsed_publisher, parsed_separator, parsed_name = extension_id.partition(
                "."
            )
            if parsed_separator:
                publisher = parsed_publisher
                extension_name = parsed_name
                version = parsed_version

    return ExtensionIdentity(
        publisher=publisher,
        name=extension_name,
        version=version,
    )


def _resolve_static_sibling(name: str) -> StaticAnalysisReport | None:
    """Best-effort load of the static pre-check report for an activation report.

    Resolves the ``static_report_{job_id}.json`` sibling persisted by the static
    gate (a ``CombinedAnalysisBundle``) via the shared 12-hex ``job_id`` token
    embedded in the activation report name, and returns its ``StaticAnalysisReport``.

    Returns ``None`` — never raises — when the report was not produced by a
    static-gate run (no token / no sibling), when the match is ambiguous, or when
    the sibling is unreadable / schema-invalid. A missing or degraded static
    artifact must read as "no static pre-check for this run" on the Reports UI,
    not break the dynamic bundle.
    """
    stem = name.removeprefix("activation_report_").removesuffix(".json")
    token = stem.rsplit("-", 1)[-1]
    if not _RUN_ID_TOKEN_RE.match(token):
        return None

    output_dir = _get_output_dir()
    matches = sorted(output_dir.glob(f"static_report_{token}*.json"))
    if len(matches) != 1:
        # 0 → no static gate ran; >1 → ambiguous prefix, refuse to guess.
        return None

    try:
        raw = matches[0].read_text(encoding="utf-8")
        bundle = CombinedAnalysisBundle.model_validate(json.loads(raw))
    except (OSError, UnicodeDecodeError, ValueError, ValidationError) as exc:
        # ValueError covers json.JSONDecodeError (a ValueError subclass).
        logger.warning("Static sibling load failed for %s: %s", name, exc)
        return None
    return bundle.static_report


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/activations", response_model=list[ActivationReportFileSummary])
def list_activations() -> list[ActivationReportFileSummary]:
    """
    List all available activation report files.

    Returns metadata for each report file (filename, size, modified date).
    Reports are sorted by modification time, newest first.
    """
    files = _list_report_files()
    results: list[ActivationReportFileSummary] = []
    for f in files:
        stat = f.stat()
        results.append(
            ActivationReportFileSummary(
                filename=f.name,
                size_bytes=stat.st_size,
                modified=stat.st_mtime,
            )
        )
    return results


@router.get("/activations/latest", response_model=ActivationReportResponse)
def get_latest_activation() -> dict[str, Any]:
    """
    Get the most recent activation report.

    Returns the full contents of the newest JSON report file.
    Raises 404 if no reports exist.
    """
    files = _list_report_files()
    if not files:
        raise HTTPException(
            status_code=404,
            detail="No activation reports found in output directory.",
        )
    # The newest file can be partially written while executor is updating it.
    # Fall back to the next-most-recent valid JSON object report.
    last_error: HTTPException | None = None
    for report_file in files:
        try:
            report = _read_report(report_file)
        except HTTPException as exc:
            last_error = exc
            continue
        data = report.model_dump(mode="json")
        data["_metadata"] = {"filename": report_file.name}
        return data

    if last_error is not None:
        raise last_error

    raise HTTPException(
        status_code=404,
        detail="No valid activation reports found in output directory.",
    )


@router.get("/activations/{name}", response_model=ActivationReportResponse)
def get_activation_by_name(
    name: str = PathParam(..., pattern=ACTIVATION_REPORT_NAME_RE.pattern),
) -> dict[str, Any]:
    """
    Get a specific activation report by filename.

    The path parameter is gated by ``ACTIVATION_REPORT_NAME_RE`` (W8-5);
    directory-traversal sequences, separators, control characters, and
    overlength inputs return 422 before this handler runs.
    """
    path = _get_output_dir() / name
    if not path.exists() or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Report not found: {name}",
        )
    report = _read_report(path)
    data = report.model_dump(mode="json")
    data["_metadata"] = {"filename": name}
    return data


@router.get("/activations/{name}/bundle", response_model=ReportBundle)
def get_activation_bundle_by_name(
    name: str = PathParam(..., pattern=ACTIVATION_REPORT_NAME_RE.pattern),
) -> ReportBundle:
    path = _get_output_dir() / name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Report not found: {name}")

    report = _read_report(path)
    analyzed_extension = _identity_from_report_name(name, report)
    detection_report = run_detection(
        report,
        activation_report_ref=name,
        analyzed_extension=analyzed_extension,
    )
    return ReportBundle(
        activation_report=report,
        detection_report=detection_report,
        static_report=_resolve_static_sibling(name),
    )
