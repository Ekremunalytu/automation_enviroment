"""W8-1 — VSIX zip-bomb + entry-count guard tests.

Adversarial-VSIX archives must be rejected before extraction can saturate
disk or memory. ``_extract_vsix_to_dir`` enforces three module-level
limits (``MAX_UNCOMPRESSED_SIZE``, ``MAX_COMPRESSION_RATIO``,
``MAX_FILE_COUNT``); these tests verify the limits trigger and that a
benign small VSIX still extracts cleanly.

W9-6a additions: rejection-branch logging — path-traversal and
symlink-escape entries emit ``vsix_entry_rejected`` warning breadcrumbs
and contribute to the per-call rejection counter that ``_extract_vsix_to_dir``
returns.
"""

from __future__ import annotations

import io
import logging
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

    with pytest.raises(VSIXUnpackError, match="entry count") as excinfo:
        marketplace_client._extract_vsix_to_dir(vsix, tmp_path)

    # W12-* hardening: VSIXUnpackError now carries structured breach
    # metadata so the HTTP layer can render a popup naming the specific
    # threshold; the message-level match above pins backwards-compat.
    err = excinfo.value
    assert err.breach_kind == marketplace_client.VSIX_BREACH_ENTRY_COUNT
    assert err.threshold_name == "vsix_max_file_count"
    assert err.threshold_value == 5
    assert err.observed_value == 6  # the 6th entry trips the > limit branch


def test_extract_with_operator_threshold_dict_overrides_module_constants(
    tmp_path: Path,
) -> None:
    """When thresholds dict is supplied, module-level constants are not
    consulted — operator-tuned values take effect for that call."""
    members = [(f"extension/file_{i:03d}.txt", b"x") for i in range(10)]
    vsix = _build_vsix(members)

    # Module constants are wide enough (50_000) to accept; the per-call
    # dict tightens to 5 and trips the breach.
    with pytest.raises(VSIXUnpackError) as excinfo:
        marketplace_client._extract_vsix_to_dir(
            vsix,
            tmp_path,
            thresholds={
                "vsix_max_uncompressed_size": 256 * 1024 * 1024,
                "vsix_max_compression_ratio": 100,
                "vsix_max_file_count": 5,
            },
        )
    assert excinfo.value.threshold_value == 5
    assert excinfo.value.breach_kind == marketplace_client.VSIX_BREACH_ENTRY_COUNT


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


def test_path_traversal_emits_rejection_log(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """W9-6a: ``..`` rejection branch must emit a warning breadcrumb and
    contribute to the per-call rejection counter."""
    vsix = _build_vsix(
        [
            ("extension/../escape.txt", b"pwned"),
            ("extension/legit.txt", b"ok"),
        ]
    )

    with caplog.at_level(logging.WARNING, logger="workflows.marketplace.client"):
        rejected = marketplace_client._extract_vsix_to_dir(vsix, tmp_path)

    assert rejected == 1
    warnings = [
        rec
        for rec in caplog.records
        if rec.levelno == logging.WARNING and "vsix_entry_rejected" in rec.getMessage()
    ]
    assert len(warnings) == 1
    msg = warnings[0].getMessage()
    assert "reason=path_traversal" in msg
    assert "extension/../escape.txt" in msg


def test_symlink_escape_emits_rejection_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """W9-6a: relative_to-fail rejection branch must emit a warning
    breadcrumb. We force the failure by symlinking ``destination_dir`` so
    the resolved entry path falls outside the resolved sandbox."""
    sandbox_outside = tmp_path / "outside"
    sandbox_outside.mkdir()
    sandbox = tmp_path / "sandbox"
    sandbox.symlink_to(sandbox_outside)

    # The ``relative_to`` guard resolves both target and destination_dir.
    # Patch Path.resolve so the *target* entry resolves to a path that
    # escapes destination_dir.resolve(), tripping the ValueError branch.
    real_resolve = Path.resolve
    forbidden = tmp_path / "forbidden" / "escape.txt"
    forbidden.parent.mkdir(parents=True, exist_ok=True)

    def fake_resolve(self: Path, *args: object, **kwargs: object) -> Path:
        if self.name == "escape.txt":
            return forbidden
        return real_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    vsix = _build_vsix(
        [
            ("extension/escape.txt", b"pwned"),
            ("extension/legit.txt", b"ok"),
        ]
    )

    with caplog.at_level(logging.WARNING, logger="workflows.marketplace.client"):
        rejected = marketplace_client._extract_vsix_to_dir(vsix, sandbox)

    assert rejected == 1
    warnings = [
        rec
        for rec in caplog.records
        if rec.levelno == logging.WARNING and "vsix_entry_rejected" in rec.getMessage()
    ]
    assert len(warnings) == 1
    msg = warnings[0].getMessage()
    assert "reason=symlink_escape" in msg
    assert "extension/escape.txt" in msg
