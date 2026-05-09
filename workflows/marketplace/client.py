"""VS Code Marketplace HTTP client for the marketplace workflow."""

from __future__ import annotations

import io
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schemas import MarketplaceExtension
from packages.marketplace_identity import safe_marketplace_slug
from workflows.extension_catalog.manifest_reader import (
    PackageJsonReadError,
    get_package_json,
)

logger = logging.getLogger(__name__)

_MARKETPLACE_API = (
    "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
)
_VSIX_URL_TEMPLATE = (
    "https://marketplace.visualstudio.com/_apis/public/gallery"
    "/publishers/{publisher}/vsextensions/{name}/{version}/vspackage"
)
_ACCEPT_HEADER = "application/json;api-version=7.2-preview.1"

# Adversarial-VSIX extraction limits (W8-1 hardening; commit `bd9d1f1`).
# Two layers of defense:
#   1. Zip-bomb (resource exhaustion via expansion): MAX_UNCOMPRESSED_SIZE
#      caps cumulative inflated bytes; MAX_COMPRESSION_RATIO catches
#      pathological compression. These are the primary guards.
#   2. Entry-count DoS (extract-loop iteration overhead): MAX_FILE_COUNT.
#
# These module-level constants are the *fallback defaults* when no
# operator-tuned thresholds are passed to ``_extract_vsix_to_dir`` (e.g.
# unit tests that monkeypatch a single value, or callers without a DB
# handle). The production HTTP path (``download_and_extract_vsix``) loads
# the operator-tunable values from ``operator_settings`` via
# ``workflows.security_settings.service.load_vsix_thresholds``.
#
# 50_000 entries was promoted from the original 2_000 on `2026-05-08`
# after the Microsoft ms-python release (`2026.5.2026050801`) tripped it
# on real users.
MAX_UNCOMPRESSED_SIZE = 256 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
MAX_FILE_COUNT = 50_000


# Breach-kind discriminators on ``VSIXUnpackError``; the HTTP layer maps
# these to a structured 422 response so the UI popup can render the
# specific threshold that tripped.
VSIX_BREACH_ENTRY_COUNT = "entry_count"
VSIX_BREACH_UNCOMPRESSED_SIZE = "uncompressed_size"
VSIX_BREACH_COMPRESSION_RATIO = "compression_ratio"


class VSIXUnpackError(RuntimeError):
    """Raised when a VSIX archive violates extraction safety limits.

    Structured fields (``breach_kind`` / ``threshold_*`` / ``observed_value``)
    let the HTTP layer surface a machine-readable error so the UI can render
    a popup naming the specific threshold and pointing the operator at
    Settings → Security to raise it.
    """

    def __init__(
        self,
        message: str,
        *,
        breach_kind: str | None = None,
        threshold_name: str | None = None,
        threshold_value: int | None = None,
        observed_value: int | float | None = None,
    ) -> None:
        super().__init__(message)
        self.breach_kind = breach_kind
        self.threshold_name = threshold_name
        self.threshold_value = threshold_value
        self.observed_value = observed_value


def search_marketplace(query: str, page_size: int = 10) -> list[MarketplaceExtension]:
    """
    Search the VS Code Marketplace for extensions.

    Args:
        query: Search term (non-empty).
        page_size: Number of results to return (clamped to 1-100).

    Returns:
        List of validated marketplace extension records.

    Raises:
        httpx.HTTPError: On network or upstream API errors.
    """
    body = {
        "filters": [
            {
                "criteria": [
                    {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                    {"filterType": 10, "value": query},
                ],
                "pageSize": page_size,
                "sortBy": 4,
            }
        ],
        "flags": 914,
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            _MARKETPLACE_API,
            json=body,
            headers={"Accept": _ACCEPT_HEADER},
        )
        resp.raise_for_status()
        data = resp.json()

    results: list[MarketplaceExtension] = []
    extensions = data.get("results", [{}])[0].get("extensions", [])

    for ext in extensions:
        publisher = ext.get("publisher", {}).get("publisherName", "")
        name = ext.get("extensionName", "")
        versions = ext.get("versions") or []
        version = versions[0].get("version", "") if versions else ""

        stats = {s["statisticName"]: s["value"] for s in ext.get("statistics", [])}

        results.append(
            MarketplaceExtension(
                publisher=publisher,
                name=name,
                version=version,
                displayName=ext.get("displayName", ""),
                description=ext.get("shortDescription", ""),
                installs=int(stats.get("install", 0)),
                rating=round(float(stats.get("averagerating", 0.0)), 2),
            )
        )

    return results


def get_vsix_path(publisher: str, name: str, version: str) -> Path:
    """Return the expected path for a raw .vsix file on disk."""
    slug = safe_marketplace_slug(publisher, name, version)
    return Path(settings.project.EXTENSION_DIR) / f"{slug}.vsix"


def _artifact_name(publisher: str, name: str, version: str) -> str:
    return safe_marketplace_slug(publisher, name, version)


def _extension_dir(publisher: str, name: str, version: str) -> Path:
    return Path(settings.project.EXTENSION_DIR) / _artifact_name(
        publisher, name, version
    )


def _partial_extract_dir(base_dir: Path, artifact_name: str) -> Path:
    return base_dir / f".{artifact_name}.partial.{os.getpid()}.{uuid4().hex}"


def _partial_vsix_path(base_dir: Path, artifact_name: str) -> Path:
    return base_dir / f".{artifact_name}.vsix.partial.{os.getpid()}.{uuid4().hex}"


def _cleanup_partial_dir(partial_dir: Path) -> None:
    if partial_dir.exists():
        shutil.rmtree(partial_dir)


def _is_valid_extracted_extension(extension_dir: Path) -> bool:
    try:
        get_package_json(extension_dir)
    except PackageJsonReadError:
        return False
    return True


def _publish_vsix_file(vsix_file: Path, vsix_bytes: bytes, artifact_name: str) -> None:
    if vsix_file.exists():
        return

    partial_vsix = _partial_vsix_path(vsix_file.parent, artifact_name)
    partial_vsix.write_bytes(vsix_bytes)

    try:
        partial_vsix.replace(vsix_file)
    except OSError:
        partial_vsix.unlink(missing_ok=True)
        raise


def _resolve_thresholds(thresholds: dict[str, int] | None) -> tuple[int, int, int]:
    """Return effective (max_size, max_ratio, max_count) for this extract call.

    When ``thresholds`` is ``None`` we fall back to the module-level
    constants — this is the test-friendly path: unit tests monkeypatch
    ``MAX_FILE_COUNT`` etc. and call ``_extract_vsix_to_dir`` without
    plumbing a DB session through. Production callers go through
    ``download_and_extract_vsix`` which fetches operator-tuned values.
    """
    if thresholds is None:
        return MAX_UNCOMPRESSED_SIZE, MAX_COMPRESSION_RATIO, MAX_FILE_COUNT

    # Operator-tuned dict comes straight from
    # ``workflows.security_settings.defaults.VSIX_THRESHOLD_KEYS``.
    return (
        int(thresholds.get("vsix_max_uncompressed_size", MAX_UNCOMPRESSED_SIZE)),
        int(thresholds.get("vsix_max_compression_ratio", MAX_COMPRESSION_RATIO)),
        int(thresholds.get("vsix_max_file_count", MAX_FILE_COUNT)),
    )


def _extract_vsix_to_dir(
    vsix_bytes: bytes,
    destination_dir: Path,
    *,
    thresholds: dict[str, int] | None = None,
    metrics_out: dict[str, float] | None = None,
) -> int:
    """Extract a VSIX archive into ``destination_dir`` under safety limits.

    Returns the count of entries rejected for path-traversal or
    symlink-escape reasons (silently skipped during extraction). Limit
    breaches still raise ``VSIXUnpackError``.

    ``thresholds`` is a dict keyed by ``VSIX_THRESHOLD_KEYS``; when ``None``
    we fall back to the module-level constants. Production callers pass a
    dict loaded from the operator-tunable settings table; tests typically
    rely on the fallback path with a monkeypatched constant.

    ``metrics_out`` (optional, mutated in place) collects the observed
    extraction metrics — ``file_count`` / ``uncompressed_size`` /
    ``compressed_size`` / ``compression_ratio`` / ``rejected_entry_count``.
    The HTTP layer uses these to populate ``MarketplaceDownloadResponse``
    so the UI can render the "VSIX Integrity" panel and highlight
    extensions whose footprint approaches the operator-set thresholds.
    """
    max_uncompressed, max_ratio, max_file_count = _resolve_thresholds(thresholds)

    cumulative_uncompressed = 0
    cumulative_compressed = 0
    file_count = 0
    rejected_count = 0

    with zipfile.ZipFile(io.BytesIO(vsix_bytes)) as zf:
        for info in zf.infolist():
            if not info.filename.startswith("extension/"):
                continue

            parts = Path(info.filename).parts
            if ".." in parts:
                rejected_count += 1
                logger.warning(
                    "vsix_entry_rejected reason=path_traversal entry=%s",
                    info.filename,
                )
                continue

            rel_parts = parts[1:]
            if not rel_parts:
                continue

            file_count += 1
            if file_count > max_file_count:
                raise VSIXUnpackError(
                    f"VSIX archive exceeds entry count limit ({max_file_count})",
                    breach_kind=VSIX_BREACH_ENTRY_COUNT,
                    threshold_name="vsix_max_file_count",
                    threshold_value=max_file_count,
                    observed_value=file_count,
                )

            cumulative_uncompressed += info.file_size
            cumulative_compressed += info.compress_size
            if cumulative_uncompressed > max_uncompressed:
                raise VSIXUnpackError(
                    f"VSIX archive exceeds uncompressed size limit "
                    f"({max_uncompressed} bytes)",
                    breach_kind=VSIX_BREACH_UNCOMPRESSED_SIZE,
                    threshold_name="vsix_max_uncompressed_size",
                    threshold_value=max_uncompressed,
                    observed_value=cumulative_uncompressed,
                )
            if cumulative_compressed > 0:
                ratio = cumulative_uncompressed / cumulative_compressed
                if ratio > max_ratio:
                    raise VSIXUnpackError(
                        f"VSIX compression ratio {ratio:.1f}:1 exceeds "
                        f"limit ({max_ratio}:1)",
                        breach_kind=VSIX_BREACH_COMPRESSION_RATIO,
                        threshold_name="vsix_max_compression_ratio",
                        threshold_value=max_ratio,
                        observed_value=round(ratio, 2),
                    )

            rel_path = Path(*rel_parts)
            target = destination_dir / rel_path

            try:
                target.resolve().relative_to(destination_dir.resolve())
            except ValueError:
                rejected_count += 1
                logger.warning(
                    "vsix_entry_rejected reason=symlink_escape entry=%s",
                    info.filename,
                )
                continue

            if info.filename.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(info))

    if rejected_count:
        logger.info(
            "vsix_extraction_rejections total=%d destination=%s",
            rejected_count,
            destination_dir,
        )

    if metrics_out is not None:
        ratio = (
            cumulative_uncompressed / cumulative_compressed
            if cumulative_compressed > 0
            else 0.0
        )
        metrics_out["file_count"] = file_count
        metrics_out["uncompressed_size"] = cumulative_uncompressed
        metrics_out["compressed_size"] = cumulative_compressed
        metrics_out["compression_ratio"] = round(ratio, 3)
        metrics_out["rejected_entry_count"] = rejected_count

    return rejected_count


def _publish_extracted_extension(partial_dir: Path, final_dir: Path) -> Path:
    if final_dir.exists() and _is_valid_extracted_extension(final_dir):
        _cleanup_partial_dir(partial_dir)
        return final_dir

    try:
        if final_dir.exists():
            _cleanup_partial_dir(final_dir)
        partial_dir.rename(final_dir)
    except FileExistsError:
        if _is_valid_extracted_extension(final_dir):
            _cleanup_partial_dir(partial_dir)
            return final_dir
        if final_dir.exists():
            _cleanup_partial_dir(final_dir)
        try:
            partial_dir.rename(final_dir)
        except OSError:
            _cleanup_partial_dir(partial_dir)
            raise
    except OSError:
        _cleanup_partial_dir(partial_dir)
        raise

    return final_dir


def download_and_extract_vsix(
    publisher: str,
    name: str,
    version: str,
    *,
    db: Session | None = None,
    metrics_out: dict[str, float] | None = None,
) -> Path:
    """
    Download and extract a VSIX extension package from the VS Code Marketplace.

    The VSIX is a ZIP archive containing an ``extension/`` subdirectory with the
    extension source. This function extracts that subdirectory into:
        ``{EXTENSION_DIR}/{publisher}.{name}-{version}/``

    Idempotent: if the directory already contains a ``package.json``, the
    download and extraction are skipped.

    Args:
        publisher: Publisher name (e.g. ``ms-python``).
        name: Extension name (e.g. ``python``).
        version: Extension version string (e.g. ``2025.0.0``).
        db: Optional SQLAlchemy session. When supplied, the operator-tuned
            VSIX hardening thresholds are loaded from
            ``operator_settings`` and passed to the extractor; otherwise
            the module-level fallback constants apply.

    Returns:
        Path to the extracted extension directory.

    Raises:
        httpx.HTTPError: On network or upstream errors.
        VSIXUnpackError: When extraction trips a hardening threshold; the
            exception carries structured ``breach_kind`` /
            ``threshold_value`` / ``observed_value`` fields for the HTTP
            layer.
    """
    base_dir = Path(settings.project.EXTENSION_DIR)
    artifact_name = _artifact_name(publisher, name, version)
    ext_dir = _extension_dir(publisher, name, version)
    vsix_file = get_vsix_path(publisher, name, version)
    base_dir.mkdir(parents=True, exist_ok=True)

    manifest_ready = False
    if ext_dir.exists():
        try:
            get_package_json(ext_dir)
        except PackageJsonReadError:
            manifest_ready = False
        else:
            manifest_ready = True

    if manifest_ready and vsix_file.exists():
        return ext_dir

    url = _VSIX_URL_TEMPLATE.format(publisher=publisher, name=name, version=version)

    with httpx.Client(timeout=120, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        vsix_bytes = resp.content

    _publish_vsix_file(vsix_file, vsix_bytes, artifact_name)

    if manifest_ready:
        return ext_dir

    partial_dir = _partial_extract_dir(base_dir, artifact_name)
    partial_dir.mkdir(parents=False, exist_ok=False)

    # Load operator-tuned thresholds when a DB session is available; the
    # extractor falls back to module constants if we pass ``None``.
    thresholds: dict[str, int] | None = None
    if db is not None:
        from workflows.security_settings import load_vsix_thresholds

        thresholds = load_vsix_thresholds(db)

    try:
        _extract_vsix_to_dir(
            vsix_bytes,
            partial_dir,
            thresholds=thresholds,
            metrics_out=metrics_out,
        )
        get_package_json(partial_dir)
    except (OSError, PackageJsonReadError, zipfile.BadZipFile, VSIXUnpackError):
        _cleanup_partial_dir(partial_dir)
        raise

    return _publish_extracted_extension(partial_dir, ext_dir)
