"""Fire / silent unit tests for the S3 file-tree heuristic rules (ES-3a)."""

from __future__ import annotations

from collections.abc import Callable

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


def test_native_binary_fires_on_disguised_binary(make_context: MakeContext) -> None:
    # Non-text suffix + NUL byte -> content-sniffed as binary.
    ctx = make_context(files={"data.dat": b"abc\x00\x01\x02def"})
    assert len(EmbeddedNativeBinaryRule().evaluate(ctx)) == 1


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
    files = {f"libs/mod{i:02d}.node": b"\x00bin" for i in range(30)}
    ctx = make_context(files=files)
    findings = EmbeddedNativeBinaryRule().evaluate(ctx)
    assert len(findings) == 1
    assert len(findings[0].evidence) == 25
    assert "30 native/binary file(s)" in findings[0].description
    assert "showing 25" in findings[0].description
