"""VS Code Marketplace HTTP client for the marketplace workflow."""

from __future__ import annotations

import io
import os
import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

import httpx

from appcore.api.config import settings
from workflows.extension_catalog.manifest_reader import (
    PackageJsonReadError,
    get_package_json,
)

_MARKETPLACE_API = (
    "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
)
_VSIX_URL_TEMPLATE = (
    "https://marketplace.visualstudio.com/_apis/public/gallery"
    "/publishers/{publisher}/vsextensions/{name}/{version}/vspackage"
)
_ACCEPT_HEADER = "application/json;api-version=7.2-preview.1"


def search_marketplace(query: str, page_size: int = 10) -> list[dict]:
    """
    Search the VS Code Marketplace for extensions.

    Args:
        query: Search term (non-empty).
        page_size: Number of results to return (clamped to 1-100).

    Returns:
        List of dicts with keys:
            publisher, name, version, displayName, description, installs, rating

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

    results: list[dict] = []
    extensions = data.get("results", [{}])[0].get("extensions", [])

    for ext in extensions:
        publisher = ext.get("publisher", {}).get("publisherName", "")
        name = ext.get("extensionName", "")
        versions = ext.get("versions") or []
        version = versions[0].get("version", "") if versions else ""

        stats = {s["statisticName"]: s["value"] for s in ext.get("statistics", [])}

        results.append(
            {
                "publisher": publisher,
                "name": name,
                "version": version,
                "displayName": ext.get("displayName", ""),
                "description": ext.get("shortDescription", ""),
                "installs": int(stats.get("install", 0)),
                "rating": round(float(stats.get("averagerating", 0.0)), 2),
            }
        )

    return results


def get_vsix_path(publisher: str, name: str, version: str) -> Path:
    """Return the expected path for a raw .vsix file on disk."""
    return Path(settings.project.EXTENSION_DIR) / f"{publisher}.{name}-{version}.vsix"


def _artifact_name(publisher: str, name: str, version: str) -> str:
    return f"{publisher}.{name}-{version}"


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


def _extract_vsix_to_dir(vsix_bytes: bytes, destination_dir: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(vsix_bytes)) as zf:
        for member in zf.namelist():
            if not member.startswith("extension/"):
                continue

            parts = Path(member).parts
            if ".." in parts:
                continue

            rel_parts = parts[1:]
            if not rel_parts:
                continue

            rel_path = Path(*rel_parts)
            target = destination_dir / rel_path

            try:
                target.resolve().relative_to(destination_dir.resolve())
            except ValueError:
                continue

            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))


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


def download_and_extract_vsix(publisher: str, name: str, version: str) -> Path:
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

    Returns:
        Path to the extracted extension directory.

    Raises:
        httpx.HTTPError: On network or upstream errors.
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

    try:
        _extract_vsix_to_dir(vsix_bytes, partial_dir)
        get_package_json(partial_dir)
    except (OSError, PackageJsonReadError, zipfile.BadZipFile):
        _cleanup_partial_dir(partial_dir)
        raise

    return _publish_extracted_extension(partial_dir, ext_dir)
