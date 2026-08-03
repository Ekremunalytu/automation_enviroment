"""Bounded artifact role and format classification for static analysis.

The classifier is deliberately stdlib-only so it can run inside the hardened
static analyzer image.  It uses paths as context and a small, bounded header
read as evidence; an arbitrary NUL byte is never treated as proof that a file
is a native executable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from packages.analysis_contracts.static_detection import (
    StaticArtifactFormat,
    StaticArtifactRole,
)

ArtifactRole = StaticArtifactRole
ArtifactFormat = StaticArtifactFormat

_HEADER_BYTES = 512
_NATIVE_SUFFIXES = frozenset({".node", ".so", ".dylib", ".dll", ".exe"})
_ARCHIVE_SUFFIXES = frozenset(
    {".zip", ".vsix", ".jar", ".tgz", ".gz", ".7z", ".rar", ".tar"}
)
_IMAGE_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg"}
)
_FONT_SUFFIXES = frozenset({".ttf", ".otf", ".woff", ".woff2"})
_CONFIG_SUFFIXES = frozenset(
    {".json", ".jsonc", ".yml", ".yaml", ".xml", ".toml", ".ini", ".env"}
)
_RUNTIME_SUFFIXES = frozenset(
    {".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs", ".py", ".sh"}
)
DEEP_SCAN_SOURCE_SUFFIXES = frozenset({".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs"})
_DOCUMENTATION_SUFFIXES = frozenset({".md", ".mdx", ".rst", ".adoc"})
_DOCUMENTATION_PREFIXES = ("readme", "changelog", "history", "authors")
_LICENSE_PREFIXES = (
    "license",
    "licence",
    "copying",
    "notice",
    "thirdpartynotice",
)
_DOCUMENTATION_DIRS = frozenset({"doc", "docs", "documentation"})
_TEST_DIRS = frozenset({"test", "tests", "__tests__", "spec", "specs"})
_ASSET_DIRS = frozenset({"asset", "assets", "image", "images", "media", "icons"})

_MACH_O_MAGICS = frozenset(
    {
        b"\xfe\xed\xfa\xce",
        b"\xfe\xed\xfa\xcf",
        b"\xce\xfa\xed\xfe",
        b"\xcf\xfa\xed\xfe",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
        b"\xca\xfe\xba\xbf",
        b"\xbf\xba\xfe\xca",
    }
)


@dataclass(frozen=True, slots=True)
class ArtifactClassification:
    role: ArtifactRole
    format: ArtifactFormat
    suffix: str
    header_sha256: str | None
    header_bytes_read: int
    extension_header_match: bool | None
    read_error: bool

    @property
    def is_native_executable(self) -> bool:
        """Whether the artifact has native format evidence or a native ABI suffix."""

        return self.format in {"pe", "elf", "mach_o"} or self.role == "native"


def _read_header(path: Path) -> tuple[bytes, bool]:
    try:
        with path.open("rb") as handle:
            return handle.read(_HEADER_BYTES), False
    except OSError:
        return b"", True


def _is_pe(header: bytes) -> bool:
    if len(header) < 64 or not header.startswith(b"MZ"):
        return False
    pe_offset = int.from_bytes(header[0x3C:0x40], "little")
    return (
        0 <= pe_offset <= len(header) - 4
        and header[pe_offset : pe_offset + 4] == b"PE\0\0"
    )


def _format_from_header(header: bytes) -> ArtifactFormat:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"
    if header.startswith((b"\x00\x01\x00\x00", b"OTTO", b"wOFF", b"wOF2")):
        return "font"
    if header.startswith(b"SQLite format 3\0"):
        return "sqlite"
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "zip"
    if header.startswith(b"\x1f\x8b"):
        return "gzip"
    if header.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z"
    if header.startswith((b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00")):
        return "rar"
    if len(header) >= 262 and header[257:262] == b"ustar":
        return "tar"
    if _is_pe(header):
        return "pe"
    if header.startswith(b"\x7fELF"):
        return "elf"
    if header[:4] in _MACH_O_MAGICS:
        return "mach_o"
    if header.startswith(b"\0asm"):
        return "wasm"
    if b"\0" in header:
        return "opaque_binary"
    if header:
        try:
            header.decode("utf-8")
        except UnicodeDecodeError:
            return "opaque_binary"
        return "text"
    return "unknown"


def _extension_header_match(suffix: str, format_name: ArtifactFormat) -> bool | None:
    expected: dict[str, frozenset[ArtifactFormat]] = {
        ".png": frozenset({"png"}),
        ".jpg": frozenset({"jpeg"}),
        ".jpeg": frozenset({"jpeg"}),
        ".gif": frozenset({"gif"}),
        ".webp": frozenset({"webp"}),
        ".ttf": frozenset({"font"}),
        ".otf": frozenset({"font"}),
        ".woff": frozenset({"font"}),
        ".woff2": frozenset({"font"}),
        ".sqlite": frozenset({"sqlite"}),
        ".db": frozenset({"sqlite"}),
        ".zip": frozenset({"zip"}),
        ".vsix": frozenset({"zip"}),
        ".jar": frozenset({"zip"}),
        ".gz": frozenset({"gzip"}),
        ".tgz": frozenset({"gzip"}),
        ".7z": frozenset({"7z"}),
        ".rar": frozenset({"rar"}),
        ".tar": frozenset({"tar"}),
        ".exe": frozenset({"pe"}),
        ".dll": frozenset({"pe"}),
        ".so": frozenset({"elf"}),
        ".dylib": frozenset({"mach_o"}),
        ".node": frozenset({"pe", "elf", "mach_o"}),
        ".wasm": frozenset({"wasm"}),
    }
    if suffix in DEEP_SCAN_SOURCE_SUFFIXES:
        return format_name == "text" if format_name != "unknown" else None
    allowed = expected.get(suffix)
    if allowed is None or format_name == "unknown":
        return None
    return format_name in allowed


def dependency_owner(relative_path: str) -> str | None:
    """Return the nearest npm package owning a path under ``node_modules``."""

    parts = PurePosixPath(relative_path.replace("\\", "/")).parts
    owner: str | None = None
    for index, part in enumerate(parts):
        if part.lower() != "node_modules" or index + 1 >= len(parts):
            continue
        first = parts[index + 1]
        if first.startswith("@") and index + 2 < len(parts):
            owner = f"{first}/{parts[index + 2]}"
        else:
            owner = first
    return owner


def is_vendor_path(relative_path: str) -> bool:
    parts = tuple(
        part.lower()
        for part in PurePosixPath(relative_path.replace("\\", "/")).parts[:-1]
    )
    return "node_modules" in parts or "vendor" in parts or "vendors" in parts


def is_minified_path(relative_path: str) -> bool:
    name = PurePosixPath(relative_path.replace("\\", "/")).name.lower()
    return ".min." in name


def artifact_role(relative_path: str) -> ArtifactRole:
    """Classify a normalized extension-relative path without reading content."""

    path = PurePosixPath(relative_path.replace("\\", "/"))
    lowered_parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    suffix = path.suffix.lower()
    parent_parts = frozenset(lowered_parts[:-1])

    if name == "package.json":
        return "manifest"
    if name.startswith(_LICENSE_PREFIXES):
        return "license"
    if (
        suffix in _DOCUMENTATION_SUFFIXES
        or name.startswith(_DOCUMENTATION_PREFIXES)
        or parent_parts & _DOCUMENTATION_DIRS
    ):
        return "documentation"
    if parent_parts & _TEST_DIRS or ".test." in name or ".spec." in name:
        return "test"
    if suffix == ".map":
        return "source_map"
    if suffix == ".wasm":
        return "wasm"
    if suffix in _NATIVE_SUFFIXES:
        return "native"
    if suffix in _ARCHIVE_SUFFIXES:
        return "archive"
    if (
        suffix in _IMAGE_SUFFIXES
        or suffix in _FONT_SUFFIXES
        or parent_parts & _ASSET_DIRS
    ):
        return "asset"
    if suffix in _CONFIG_SUFFIXES:
        return "configuration"
    if suffix in _RUNTIME_SUFFIXES:
        if "node_modules" in parent_parts:
            return "dependency_runtime"
        return "first_party_runtime"
    return "unknown"


def classify_artifact(relative_path: str, path: Path) -> ArtifactClassification:
    """Return bounded role + magic/header evidence for one regular file."""

    suffix = PurePosixPath(relative_path.replace("\\", "/")).suffix.lower()
    role = artifact_role(relative_path)
    header, read_error = _read_header(path)
    format_name = _format_from_header(header)
    if format_name == "wasm":
        role = "wasm"
    elif format_name in {"pe", "elf", "mach_o"}:
        role = "native"
    elif format_name in {"zip", "gzip", "7z", "rar", "tar"}:
        role = "archive"
    elif format_name in {"png", "jpeg", "gif", "webp", "font"}:
        role = "asset"
    return ArtifactClassification(
        role=role,
        format=format_name,
        suffix=suffix,
        header_sha256=None if read_error else hashlib.sha256(header).hexdigest(),
        header_bytes_read=len(header),
        extension_header_match=_extension_header_match(suffix, format_name),
        read_error=read_error,
    )


__all__ = [
    "DEEP_SCAN_SOURCE_SUFFIXES",
    "ArtifactClassification",
    "ArtifactFormat",
    "ArtifactRole",
    "artifact_role",
    "classify_artifact",
    "dependency_owner",
    "is_minified_path",
    "is_vendor_path",
]
