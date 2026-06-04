"""Fire / silent unit tests for the S12 invisible-Unicode rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s12_invisible_unicode import InvisibleUnicodeRunRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_fires_critical_on_contiguous_variation_selector_run(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"extension.js": 'const x = "ok";\ufe0f\ufe0f\ufe0f'})
    findings = InvisibleUnicodeRunRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s12.invisible_unicode_run"
    assert finding.severity.value == "critical"
    assert "maximum contiguous run is 3" in finding.description
    assert finding.evidence
    assert "U+FE0F" in (finding.evidence[0].snippet or "")
    assert "\ufe0f" not in (finding.evidence[0].snippet or "")


def test_single_invisible_codepoint_is_low_severity(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"extension.js": 'const label = "a\u200bb";'})
    findings = InvisibleUnicodeRunRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].severity.value == "low"


def test_silent_for_ascii_source(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": 'const x = "plain source";'})
    assert InvisibleUnicodeRunRule().evaluate(ctx) == []
