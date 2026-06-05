"""Offline VSIX intake for the marketplace workflow.

Air-gapped counterpart to the marketplace download path. In a closed test
environment there is no egress to ``marketplace.visualstudio.com``, so the
operator drops raw ``.vsix`` files into the configured offline directory
(``settings.project.OFFLINE_DIR``, which lives under the already-mounted
``extensions`` tree). This module scans that directory and ingests a chosen
package through the *same* hardened extract path as a live download
(``client.persist_and_extract_vsix_bytes``) — identical zip-bomb,
path-traversal and symlink-escape guards.

Identity (``publisher``/``name``/``version``) is read from the
``extension/package.json`` manifest *inside* each archive, so the on-disk
filename is irrelevant.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schemas import OfflineExtension
from appcore.logging import get_extrace_logger
from packages.marketplace_identity import (
    MarketplaceIdentityError,
    safe_marketplace_slug,
)
from workflows.extension_catalog.manifest_reader import (
    PackageJsonReadError,
    get_package_json,
)
from workflows.marketplace import client as marketplace_client

logger = get_extrace_logger("extrace.workflows.marketplace.offline")

# The manifest is read fully into memory to derive identity; cap the
# decompressed size so a single hostile ``extension/package.json`` entry
# cannot exhaust memory during a directory scan of untrusted archives.
_MAX_MANIFEST_BYTES = 8 * 1024 * 1024

_VSIX_MANIFEST_ENTRY = "extension/package.json"


class OfflineIntakeError(ValueError):
    """Raised when an offline-intake request is structurally invalid.

    Covers a bad/unsafe ``filename`` and a missing offline file — operator
    input errors the router maps to 400/404 rather than the 5xx reserved for
    archive-content faults.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _offline_dir() -> Path:
    return Path(settings.project.OFFLINE_DIR)


def _read_vsix_manifest(vsix_bytes: bytes, *, source_label: str) -> dict[str, Any]:
    """Read and parse ``extension/package.json`` from raw VSIX bytes.

    Reuses ``PackageJsonReadError`` so the router maps manifest faults to the
    same status codes as the download path. Raises ``zipfile.BadZipFile`` if
    the bytes are not a valid ZIP archive.
    """
    manifest_path = Path(source_label) / _VSIX_MANIFEST_ENTRY
    with zipfile.ZipFile(io.BytesIO(vsix_bytes)) as zf:
        try:
            info = zf.getinfo(_VSIX_MANIFEST_ENTRY)
        except KeyError as exc:
            raise PackageJsonReadError.missing(manifest_path) from exc
        if info.file_size > _MAX_MANIFEST_BYTES:
            raise PackageJsonReadError.io_error(
                manifest_path,
                f"manifest exceeds {_MAX_MANIFEST_BYTES} bytes "
                f"(declared {info.file_size})",
            )
        raw = zf.read(info)

    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PackageJsonReadError.invalid_json(manifest_path, str(exc)) from exc

    if not isinstance(manifest, dict):
        raise PackageJsonReadError.invalid_json(
            manifest_path, "top-level manifest is not an object"
        )
    return manifest


def _identity(manifest: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(manifest.get("publisher", "")),
        str(manifest.get("name", "")),
        str(manifest.get("version", "")),
    )


def _is_ingested(publisher: str, name: str, version: str) -> bool:
    """True when the package is already staged and ready to analyze.

    Mirrors the post-download "Ready" state: the extracted dir holds a valid
    ``package.json`` *and* the canonical ``.vsix`` is present (the file
    ``ensure_vsix_exists`` checks before an analysis job starts). A manifest
    whose identity violates slug discipline can never have been staged, so it
    is reported as not-ingested.
    """
    try:
        slug = safe_marketplace_slug(publisher, name, version)
    except MarketplaceIdentityError:
        return False

    ext_dir = Path(settings.project.EXTENSION_DIR) / slug
    vsix_file = marketplace_client.get_vsix_path(publisher, name, version)
    if not vsix_file.exists():
        return False
    try:
        get_package_json(ext_dir)
    except PackageJsonReadError:
        return False
    return True


def _safe_offline_path(filename: str) -> Path:
    """Resolve ``filename`` to a path inside the offline dir, or reject it.

    Only a bare leaf filename ending in ``.vsix`` is accepted — no separators,
    no ``..``, no absolute paths — so a request can never escape the
    configured offline directory.
    """
    if not filename or Path(filename).name != filename:
        raise OfflineIntakeError(
            f"Invalid offline filename: {filename!r}", reason="bad_filename"
        )
    if not filename.lower().endswith(".vsix"):
        raise OfflineIntakeError(
            f"Offline file is not a .vsix: {filename!r}", reason="bad_filename"
        )

    offline_dir = _offline_dir()
    candidate = offline_dir / filename
    try:
        candidate.resolve().relative_to(offline_dir.resolve())
    except ValueError as exc:
        raise OfflineIntakeError(
            f"Offline filename escapes the intake directory: {filename!r}",
            reason="bad_filename",
        ) from exc
    return candidate


def list_offline_extensions() -> list[OfflineExtension]:
    """Scan the offline directory and return one record per readable ``.vsix``.

    The directory is created on demand so the operator can see where to drop
    packages even on a fresh checkout. Archives whose manifest cannot be read
    are skipped with a warning rather than failing the whole listing.
    Results are sorted by display name for a stable UI ordering.
    """
    offline_dir = _offline_dir()
    offline_dir.mkdir(parents=True, exist_ok=True)

    records: list[OfflineExtension] = []
    for path in sorted(offline_dir.glob("*.vsix")):
        if not path.is_file():
            continue
        try:
            vsix_bytes = path.read_bytes()
            manifest = _read_vsix_manifest(vsix_bytes, source_label=path.name)
        except (OSError, zipfile.BadZipFile, PackageJsonReadError) as exc:
            logger.warning(
                "offline_vsix_skipped filename=%s reason=%s",
                path.name,
                type(exc).__name__,
            )
            continue

        publisher, name, version = _identity(manifest)
        records.append(
            OfflineExtension(
                publisher=publisher,
                name=name,
                version=version,
                displayName=str(manifest.get("displayName") or name or path.name),
                description=str(manifest.get("description") or ""),
                filename=path.name,
                size_bytes=path.stat().st_size,
                already_ingested=_is_ingested(publisher, name, version),
            )
        )

    records.sort(key=lambda r: (r.displayName.lower(), r.filename.lower()))
    return records


def read_offline_vsix(filename: str) -> tuple[str, str, str, bytes]:
    """Validate ``filename`` and read its identity + raw bytes off disk.

    The deliberate split from extraction lets the router learn the package
    identity (``publisher``/``name``/``version``) *before* it funnels the
    bytes through the shared extractor, so a ``VSIXUnpackError`` thrown during
    extraction can be mapped to the same structured 422 the download endpoint
    emits.

    Returns ``(publisher, name, version, vsix_bytes)``.

    Raises:
        OfflineIntakeError: Bad/unsafe filename or missing offline file.
        zipfile.BadZipFile: The file is not a valid ZIP/VSIX archive.
        PackageJsonReadError: The in-archive manifest is missing/invalid.
        MarketplaceIdentityError: The manifest identity violates slug rules.
    """
    path = _safe_offline_path(filename)
    if not path.exists() or not path.is_file():
        raise OfflineIntakeError(
            f"Offline file not found: {filename}", reason="not_found"
        )

    vsix_bytes = path.read_bytes()
    manifest = _read_vsix_manifest(vsix_bytes, source_label=filename)
    publisher, name, version = _identity(manifest)

    # Form the slug eagerly so an unsafe identity fails fast with a clear
    # MarketplaceIdentityError before any bytes touch the extension store.
    safe_marketplace_slug(publisher, name, version)

    return publisher, name, version, vsix_bytes


def ingest_offline_extension(
    filename: str,
    *,
    db: Session | None = None,
    metrics_out: dict[str, float] | None = None,
) -> tuple[str, str, str, Path]:
    """Validate, read and stage one offline ``.vsix`` in a single call.

    Convenience wrapper over ``read_offline_vsix`` +
    ``client.persist_and_extract_vsix_bytes`` for direct/test use; the router
    uses the two steps separately so it can attach identity to extraction
    errors. Catalog/DB registration is left to the caller, mirroring the
    download endpoint.

    Returns ``(publisher, name, version, extracted_dir)``.
    """
    publisher, name, version, vsix_bytes = read_offline_vsix(filename)
    ext_dir = marketplace_client.persist_and_extract_vsix_bytes(
        publisher,
        name,
        version,
        vsix_bytes,
        db=db,
        metrics_out=metrics_out,
    )
    return publisher, name, version, ext_dir
