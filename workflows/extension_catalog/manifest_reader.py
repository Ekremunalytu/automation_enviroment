"""Filesystem helpers for extension manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from appcore.api.config import settings


class PackageJsonReadError(ValueError):
    """Structured package.json read failure."""

    def __init__(self, *, reason: str, path: Path, detail: str = "") -> None:
        self.reason = reason
        self.path = path
        self.detail = detail

        message = f"package.json {reason} at {path}"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)

    @classmethod
    def missing(cls, path: Path) -> PackageJsonReadError:
        return cls(reason="missing", path=path)

    @classmethod
    def invalid_json(
        cls,
        path: Path,
        detail: str,
    ) -> PackageJsonReadError:
        return cls(reason="invalid_json", path=path, detail=detail)

    @classmethod
    def io_error(
        cls,
        path: Path,
        detail: str,
    ) -> PackageJsonReadError:
        return cls(reason="io_error", path=path, detail=detail)


def parse_json_file(json_path: Path) -> dict[str, Any]:
    """Parse a JSON file and classify manifest read failures."""
    try:
        with open(json_path, encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise PackageJsonReadError.invalid_json(json_path, str(exc)) from exc
    except OSError as exc:
        raise PackageJsonReadError.io_error(json_path, str(exc)) from exc


def get_package_json(extension_dir: Path) -> dict[str, Any]:
    """Read and parse package.json from an extension directory."""
    package_path = extension_dir / "package.json"
    if not package_path.exists() or not package_path.is_file():
        raise PackageJsonReadError.missing(package_path)
    return parse_json_file(package_path)


def search_extension(extension_name_field: str) -> dict[str, Any] | None:
    """Search all extension dirs for one whose package.json name matches exactly."""
    extension_path = Path(settings.project.EXTENSION_DIR)
    if not extension_path.exists() or not extension_path.is_dir():
        return None

    for extension_dir in (path for path in extension_path.iterdir() if path.is_dir()):
        try:
            package_data = get_package_json(extension_dir)
        except PackageJsonReadError:
            continue
        if package_data and package_data.get("name") == extension_name_field:
            return package_data

    return None


__all__ = [
    "PackageJsonReadError",
    "get_package_json",
    "parse_json_file",
    "search_extension",
]
