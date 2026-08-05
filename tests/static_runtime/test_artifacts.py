"""Artifact role and bounded magic/header classification tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from static_runtime.artifacts import (
    artifact_role,
    classify_artifact,
    dependency_owner,
    is_minified_path,
    is_vendor_path,
)


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        ("package.json", "manifest"),
        ("README.md", "documentation"),
        ("docs/setup.txt", "documentation"),
        ("LICENSE", "license"),
        ("ThirdPartyNotices.txt", "license"),
        ("tests/extension.test.js", "test"),
        ("assets/logo.png", "asset"),
        ("dist/extension.js.map", "source_map"),
        ("node_modules/pkg/index.js", "dependency_runtime"),
        ("dist/extension.js", "first_party_runtime"),
        (r"node_modules\pkg\index.js", "dependency_runtime"),
        ("config/settings.yaml", "configuration"),
        ("bin/addon.node", "native"),
        ("module.wasm", "wasm"),
        ("payload.zip", "archive"),
        ("payload.dat", "unknown"),
    ],
)
def test_artifact_role(relative_path: str, expected: str) -> None:
    assert artifact_role(relative_path) == expected


@pytest.mark.parametrize(
    ("relative_path", "payload", "expected_format", "expected_role"),
    [
        ("renamed.dat", b"\x7fELFdeclawed", "elf", "native"),
        ("renamed.dat", b"\xfe\xed\xfa\xcfdeclawed", "mach_o", "native"),
        ("logo.bin", b"\x89PNG\r\n\x1a\n\x00data", "png", "asset"),
        ("photo.bin", b"\xff\xd8\xff\x00data", "jpeg", "asset"),
        ("animation.bin", b"GIF89a\x00data", "gif", "asset"),
        ("image.bin", b"RIFF\x04\x00\x00\x00WEBPdata", "webp", "asset"),
        ("font.bin", b"wOF2\x00data", "font", "asset"),
        ("state.bin", b"SQLite format 3\0data", "sqlite", "unknown"),
        ("bundle.bin", b"PK\x03\x04\x00data", "zip", "archive"),
        ("bundle.bin", b"\x1f\x8b\x08\x00data", "gzip", "archive"),
        ("bundle.bin", b"7z\xbc\xaf\x27\x1cdata", "7z", "archive"),
        ("bundle.bin", b"Rar!\x1a\x07\x01\x00data", "rar", "archive"),
        ("module.bin", b"\0asm\x01\0\0\0", "wasm", "wasm"),
        ("opaque.bin", b"abc\0def", "opaque_binary", "unknown"),
    ],
)
def test_classify_artifact_magic(
    tmp_path: Path,
    relative_path: str,
    payload: bytes,
    expected_format: str,
    expected_role: str,
) -> None:
    path = tmp_path / relative_path
    path.write_bytes(payload)
    classification = classify_artifact(relative_path, path)
    assert classification.format == expected_format
    assert classification.role == expected_role


def test_classify_artifact_detects_tar_header(tmp_path: Path) -> None:
    payload = bytearray(300)
    payload[257:262] = b"ustar"
    path = tmp_path / "renamed.dat"
    path.write_bytes(payload)

    classification = classify_artifact("renamed.dat", path)

    assert classification.format == "tar"
    assert classification.role == "archive"


def test_classify_artifact_validates_pe_header(tmp_path: Path) -> None:
    payload = bytearray(128)
    payload[:2] = b"MZ"
    payload[0x3C:0x40] = (80).to_bytes(4, "little")
    payload[80:84] = b"PE\0\0"
    path = tmp_path / "renamed.dat"
    path.write_bytes(payload)

    classification = classify_artifact("renamed.dat", path)

    assert classification.format == "pe"
    assert classification.role == "native"


def test_mz_prefix_without_pe_header_is_not_native(tmp_path: Path) -> None:
    path = tmp_path / "image.dat"
    path.write_bytes(b"MZ" + b"x" * 80)

    classification = classify_artifact("image.dat", path)

    assert classification.format == "text"
    assert not classification.is_native_executable


def test_magic_overrides_misleading_native_suffix(tmp_path: Path) -> None:
    path = tmp_path / "misleading.node"
    path.write_bytes(b"\x89PNG\r\n\x1a\n\x00data")

    classification = classify_artifact("misleading.node", path)

    assert classification.format == "png"
    assert classification.role == "asset"
    assert not classification.is_native_executable


def test_header_read_is_bounded_before_late_native_marker(tmp_path: Path) -> None:
    path = tmp_path / "payload.dat"
    path.write_bytes(b"a" * 512 + b"\x7fELF")

    classification = classify_artifact("payload.dat", path)

    assert classification.format == "text"
    assert not classification.is_native_executable
    assert classification.header_bytes_read == 512
    assert classification.header_sha256 is not None


def test_missing_file_has_unknown_format(tmp_path: Path) -> None:
    classification = classify_artifact("missing.dat", tmp_path / "missing.dat")

    assert classification.format == "unknown"
    assert classification.role == "unknown"
    assert classification.read_error is True
    assert classification.header_sha256 is None


def test_header_evidence_is_bounded_hashed_and_checks_source_extension(
    tmp_path: Path,
) -> None:
    source = tmp_path / "extension.js"
    source.write_bytes(b"const active = true;" + b"x" * 600)

    classification = classify_artifact("extension.js", source)

    expected_header = source.read_bytes()[:512]
    assert classification.header_bytes_read == 512
    assert classification.header_sha256 == hashlib.sha256(expected_header).hexdigest()
    assert classification.extension_header_match is True
    assert classification.read_error is False


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        ("node_modules/pkg/index.js", "pkg"),
        ("node_modules/@scope/pkg/index.js", "@scope/pkg"),
        ("node_modules/a/node_modules/@inner/b/file.js", "@inner/b"),
        ("dist/index.js", None),
    ],
)
def test_dependency_owner_uses_nearest_package(
    relative_path: str, expected: str | None
) -> None:
    assert dependency_owner(relative_path) == expected


def test_vendor_and_minified_path_classification() -> None:
    assert is_vendor_path("extension/vendor/client.js") is True
    assert is_vendor_path("node_modules/pkg/client.js") is True
    assert is_vendor_path("extension/src/client.js") is False
    assert is_minified_path("dist/client.min.js") is True
    assert is_minified_path("dist/client.js") is False
