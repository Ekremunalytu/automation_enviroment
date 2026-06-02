"""Fire / silent unit tests for the S6 obfuscation-indicators rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s6_obfuscation_indicators import ObfuscationIndicatorsRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_fires_on_decode_then_execute(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": 'var r = eval(atob("ZXZpbA=="));'})
    findings = ObfuscationIndicatorsRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s6.obfuscation_indicators"
    assert findings[0].severity.value == "medium"
    assert "decode-then-execute" in findings[0].description


def test_fires_on_long_fromcharcode_chain(make_context: MakeContext) -> None:
    args = ", ".join(str(n) for n in range(101, 113))  # 12 args
    ctx = make_context(files={"a.js": f"var s = String.fromCharCode({args});"})
    findings = ObfuscationIndicatorsRule().evaluate(ctx)
    assert len(findings) == 1
    assert "fromCharCode" in findings[0].description


def test_fires_on_large_base64_blob(make_context: MakeContext) -> None:
    blob = "A" * 250
    ctx = make_context(files={"a.js": f'var p = "{blob}";'})
    findings = ObfuscationIndicatorsRule().evaluate(ctx)
    assert len(findings) == 1
    assert "base64" in findings[0].description


def test_fires_on_dense_hex_escape_run(make_context: MakeContext) -> None:
    run = "".join(r"\x41" for _ in range(25))
    ctx = make_context(files={"a.js": f'var p = "{run}";'})
    findings = ObfuscationIndicatorsRule().evaluate(ctx)
    assert len(findings) == 1
    assert "hex-escape" in findings[0].description


def test_silent_for_clean_source(make_context: MakeContext) -> None:
    ctx = make_context(files={"a.js": "export function add(a, b) { return a + b; }"})
    assert ObfuscationIndicatorsRule().evaluate(ctx) == []
