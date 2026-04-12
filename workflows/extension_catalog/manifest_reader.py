"""Filesystem helpers for extension manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from appcore.api.config import settings


def parse_json_file(json_path: Path) -> dict[str, Any] | None:
    """Parse a JSON file and return its contents, or None on expected I/O errors."""
    try:
        with open(json_path, encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


def get_package_json(extension_dir: Path) -> dict[str, Any] | None:
    """Read and parse package.json from an extension directory."""
    package_path = extension_dir / "package.json"
    if package_path.exists() and package_path.is_file():
        return parse_json_file(package_path)
    return None


def search_extension(extension_name_field: str) -> dict[str, Any] | None:
    """Search all extension dirs for one whose package.json name matches exactly."""
    extension_path = Path(settings.project.EXTENSION_DIR)
    if not extension_path.exists() or not extension_path.is_dir():
        return None

    for extension_dir in (path for path in extension_path.iterdir() if path.is_dir()):
        package_data = get_package_json(extension_dir)
        if package_data and package_data.get("name") == extension_name_field:
            return package_data

    return None


__all__ = ["get_package_json", "parse_json_file", "search_extension"]
