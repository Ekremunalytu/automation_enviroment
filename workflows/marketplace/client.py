"""VS Code Marketplace HTTP client for the marketplace workflow."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx

from appcore.api.config import settings

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
    ext_dir = Path(settings.project.EXTENSION_DIR) / f"{publisher}.{name}-{version}"
    vsix_file = get_vsix_path(publisher, name, version)

    # Idempotent: skip download if already extracted and .vsix exists
    if ext_dir.exists() and (ext_dir / "package.json").exists() and vsix_file.exists():
        return ext_dir

    ext_dir.mkdir(parents=True, exist_ok=True)

    url = _VSIX_URL_TEMPLATE.format(publisher=publisher, name=name, version=version)

    with httpx.Client(timeout=120, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        vsix_bytes = resp.content

    # Preserve the raw .vsix file (VS Code CLI requires it for installation)
    if not vsix_file.exists():
        vsix_file.write_bytes(vsix_bytes)

    with zipfile.ZipFile(io.BytesIO(vsix_bytes)) as zf:
        for member in zf.namelist():
            # Only extract files inside the extension/ subdirectory
            if not member.startswith("extension/"):
                continue

            parts = Path(member).parts

            # Path traversal protection: reject any ".." components
            if ".." in parts:
                continue

            # Strip the leading "extension/" component
            rel_parts = parts[1:]
            if not rel_parts:
                # Bare "extension/" directory entry — skip
                continue

            rel_path = Path(*rel_parts)
            target = ext_dir / rel_path

            # Security: ensure resolved target stays inside ext_dir
            try:
                target.resolve().relative_to(ext_dir.resolve())
            except ValueError:
                continue

            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))

    return ext_dir
