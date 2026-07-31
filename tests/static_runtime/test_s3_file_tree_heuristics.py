"""Fire / silent unit tests for the S3 file-tree heuristic rules (ES-3a)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s3_file_tree_heuristics import (
    EmbeddedNativeBinaryRule,
    UnusualFileSignatureRule,
)

MakeContext = Callable[..., StaticAnalysisContext]


# --- extrace.s3.embedded_native_binary --------------------------------------


def test_native_binary_fires_on_node_suffix(make_context: MakeContext) -> None:
    ctx = make_context(files={"build/addon.node": b"\x7fELFpayload"})
    findings = EmbeddedNativeBinaryRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s3.embedded_native_binary"
    assert findings[0].severity.value == "medium"
    assert any(ev.relative_path == "build/addon.node" for ev in findings[0].evidence)


def test_native_binary_fires_on_renamed_elf(make_context: MakeContext) -> None:
    ctx = make_context(files={"data.dat": b"\x7fELFdeclawed-marker"})
    assert len(EmbeddedNativeBinaryRule().evaluate(ctx)) == 1


def test_native_binary_fires_on_renamed_pe(make_context: MakeContext) -> None:
    payload = bytearray(128)
    payload[:2] = b"MZ"
    payload[0x3C:0x40] = (80).to_bytes(4, "little")
    payload[80:84] = b"PE\0\0"
    ctx = make_context(files={"data.dat": bytes(payload)})
    findings = EmbeddedNativeBinaryRule().evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].rule_version == "1.1.0"
    assert findings[0].evidence[0].snippet
    assert "pe native artifact" in findings[0].evidence[0].snippet


def test_native_binary_fires_on_renamed_mach_o(make_context: MakeContext) -> None:
    ctx = make_context(files={"data.dat": b"\xfe\xed\xfa\xcfdeclawed-marker"})
    assert len(EmbeddedNativeBinaryRule().evaluate(ctx)) == 1


def test_native_binary_fires_on_declared_native_suffix_without_magic(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"build/addon.node": "declawed marker"})
    assert len(EmbeddedNativeBinaryRule().evaluate(ctx)) == 1


def test_native_binary_silent_for_opaque_nul_bytes(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"data.dat": b"abc\x00\x01\x02def"})
    assert EmbeddedNativeBinaryRule().evaluate(ctx) == []


def test_native_binary_silent_for_png_with_nul_bytes(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"assets/logo.png": b"\x89PNG\r\n\x1a\n\x00payload"})
    assert EmbeddedNativeBinaryRule().evaluate(ctx) == []


@pytest.mark.parametrize(
    ("relative_path", "payload"),
    [
        ("assets/font.woff2", b"wOF2\x00data"),
        ("state.db", b"SQLite format 3\0data"),
        ("bundle.zip", b"PK\x03\x04\x00data"),
        ("module.wasm", b"\0asm\x01\0\0\0"),
    ],
)
def test_native_binary_silent_for_non_native_binary_formats(
    make_context: MakeContext,
    relative_path: str,
    payload: bytes,
) -> None:
    ctx = make_context(files={relative_path: payload})
    assert EmbeddedNativeBinaryRule().evaluate(ctx) == []


def test_native_binary_silent_when_native_suffix_contains_png(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"assets/misleading.node": b"\x89PNG\r\n\x1a\n\x00data"})
    assert EmbeddedNativeBinaryRule().evaluate(ctx) == []


def test_native_binary_silent_for_pure_text_tree(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": "console.log(1)", "readme.md": "# hi"})
    assert EmbeddedNativeBinaryRule().evaluate(ctx) == []


# --- extrace.s3.unusual_file_signature --------------------------------------


def test_unusual_signature_fires_on_oversized_text(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"bundle.js": "x" * (2 * 1024 * 1024 + 16)})
    findings = UnusualFileSignatureRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s3.unusual_file_signature"
    assert findings[0].severity.value == "low"
    assert any(ev.relative_path == "bundle.js" for ev in findings[0].evidence)


def test_unusual_signature_silent_for_small_text(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": "console.log(1)"})
    assert UnusualFileSignatureRule().evaluate(ctx) == []


# --- evidence cap (no silent truncation) ------------------------------------


def test_native_binary_caps_evidence_but_reports_full_count(
    make_context: MakeContext,
) -> None:
    # 30 native files > the _MAX_EVIDENCE=25 cap: evidence is bounded, but the
    # true total is reported in the description rather than silently dropped.
    files = {f"libs/mod{i:02d}.node": b"\x7fELFbin" for i in range(30)}
    ctx = make_context(files=files)
    findings = EmbeddedNativeBinaryRule().evaluate(ctx)
    assert len(findings) == 1
    assert len(findings[0].evidence) == 25
    assert "30 native executable/module artifact(s)" in findings[0].description
    assert "showing 25" in findings[0].description
