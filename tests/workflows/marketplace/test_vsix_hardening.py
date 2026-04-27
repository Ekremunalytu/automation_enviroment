"""W8-1 — VSIX zip-bomb + entry-count guard tests.

Adversarial-VSIX archives must be rejected before extraction can saturate
disk or memory. ``_extract_vsix_to_dir`` enforces three module-level
limits (``MAX_UNCOMPRESSED_SIZE``, ``MAX_COMPRESSION_RATIO``,
``MAX_FILE_COUNT``); these tests verify the limits trigger and that a
benign small VSIX still extracts cleanly.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from workflows.marketplace import client as marketplace_client
from workflows.marketplace.client import VSIXUnpackError


def _build_vsix(
    members: list[tuple[str, bytes]], compression: int = zipfile.ZIP_DEFLATED
) -> bytes:
    """Return raw VSIX (zip) bytes containing ``members``."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as zf:
        for name, payload in members:
            zf.writestr(name, payload)
    return buffer.getvalue()


def test_normal_vsix_extracts_cleanly(tmp_path: Path) -> None:
    vsix = _build_vsix(
        [
            ("extension.vsixmanifest", b"<manifest/>"),
            ("extension/package.json", b'{"name":"x","version":"1.0.0"}'),
            ("extension/extension.js", b"// noop\n"),
            ("extension/README.md", b"hello"),
        ]
    )

    marketplace_client._extract_vsix_to_dir(vsix, tmp_path)

    assert (tmp_path / "package.json").read_text() == '{"name":"x","version":"1.0.0"}'
    assert (tmp_path / "extension.js").exists()
    assert (tmp_path / "README.md").exists()


def test_oversize_uncompressed_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(marketplace_client, "MAX_UNCOMPRESSED_SIZE", 1024)
    # Random-ish bytes so the compression ratio stays well below the cap.
    payload = b"abcdefgh" * 256  # 2 KiB > 1 KiB cap
    vsix = _build_vsix(
        [
            ("extension.vsixmanifest", b"<manifest/>"),
            ("extension/big.bin", payload),
        ],
        compression=zipfile.ZIP_STORED,
    )

    with pytest.raises(VSIXUnpackError, match="uncompressed size"):
        marketplace_client._extract_vsix_to_dir(vsix, tmp_path)


def test_high_compression_ratio_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(marketplace_client, "MAX_COMPRESSION_RATIO", 5)
    # Highly compressible — 64 KiB of zeros squashes to a few hundred bytes.
    payload = b"\x00" * (64 * 1024)
    vsix = _build_vsix([("extension/zero.bin", payload)])

    with pytest.raises(VSIXUnpackError, match="compression ratio"):
        marketplace_client._extract_vsix_to_dir(vsix, tmp_path)


def test_file_count_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(marketplace_client, "MAX_FILE_COUNT", 5)
    members = [(f"extension/file_{i:03d}.txt", b"x") for i in range(10)]
    vsix = _build_vsix(members)

    with pytest.raises(VSIXUnpackError, match="entry count"):
        marketplace_client._extract_vsix_to_dir(vsix, tmp_path)


def test_path_traversal_still_blocked(tmp_path: Path) -> None:
    """The pre-W8-1 ``..`` reject + ``relative_to`` guards are unchanged."""
    vsix = _build_vsix(
        [
            ("extension/../escape.txt", b"pwned"),
            ("extension/legit.txt", b"ok"),
        ]
    )

    marketplace_client._extract_vsix_to_dir(vsix, tmp_path)

    assert (tmp_path / "legit.txt").exists()
    # The traversal entry was silently skipped — it must not land outside
    # ``destination_dir`` and must not land inside it either, since its
    # filename contains ``..``.
    assert not (tmp_path.parent / "escape.txt").exists()
    assert not (tmp_path / "escape.txt").exists()
