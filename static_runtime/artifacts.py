"""Bounded artifact role and format classification for static analysis.

The classifier is deliberately stdlib-only so it can run inside the hardened
static analyzer image.  It uses paths as context and a small, bounded header
read as evidence; an arbitrary NUL byte is never treated as proof that a file
is a native executable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

ArtifactRole = Literal[
    "manifest",
    "first_party_runtime",
    "dependency_runtime",
    "documentation",
    "license",
    "test",
    "asset",
    "source_map",
    "configuration",
    "native",
    "wasm",
    "archive",
    "unknown",
]
ArtifactFormat = Literal[
    "text",
    "png",
    "jpeg",
    "gif",
    "webp",
    "font",
    "sqlite",
    "zip",
    "gzip",
    "7z",
    "rar",
    "tar",
    "pe",
    "elf",
    "mach_o",
    "wasm",
    "opaque_binary",
    "unknown",
]

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

    @property
    def is_native_executable(self) -> bool:
        """Whether the artifact has native format evidence or a native ABI suffix."""

        return self.format in {"pe", "elf", "mach_o"} or self.role == "native"


def _read_header(path: Path) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(_HEADER_BYTES)
    except OSError:
        return b""


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
    format_name = _format_from_header(_read_header(path))
    if format_name == "wasm":
        role = "wasm"
    elif format_name in {"pe", "elf", "mach_o"}:
        role = "native"
    elif format_name in {"zip", "gzip", "7z", "rar", "tar"}:
        role = "archive"
    elif format_name in {"png", "jpeg", "gif", "webp", "font"}:
        role = "asset"
    return ArtifactClassification(role=role, format=format_name, suffix=suffix)


__all__ = [
    "ArtifactClassification",
    "ArtifactFormat",
    "ArtifactRole",
    "artifact_role",
    "classify_artifact",
]
