"""Fire / silent unit tests for the S2 static typosquat rule (ES-3a)."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s2_typosquat_static import StaticTyposquatRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_typosquat_fires_on_distance_one_typo(make_context: MakeContext) -> None:
    ctx = make_context(manifest={"publisher": "ms-pyton", "name": "python"})
    findings = StaticTyposquatRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s2.typosquat"
    assert finding.severity.value == "high"
    assert finding.confidence.value == "medium"
    assert "ms-python.python" in finding.description
    assert finding.evidence, "typosquat finding must carry evidence"


def test_typosquat_silent_for_exact_popular_extension(
    make_context: MakeContext,
) -> None:
    ctx = make_context(manifest={"publisher": "ms-python", "name": "python"})
    assert StaticTyposquatRule().evaluate(ctx) == []


def test_typosquat_silent_for_unrelated_identifier(
    make_context: MakeContext,
) -> None:
    ctx = make_context(manifest={"publisher": "acme-corp", "name": "totally-unrelated"})
    assert StaticTyposquatRule().evaluate(ctx) == []


def test_typosquat_silent_when_identity_incomplete(
    make_context: MakeContext,
) -> None:
    # name missing -> no identifier -> no finding, no exception.
    ctx = make_context(manifest={"publisher": "ms-pyton"})
    assert StaticTyposquatRule().evaluate(ctx) == []
