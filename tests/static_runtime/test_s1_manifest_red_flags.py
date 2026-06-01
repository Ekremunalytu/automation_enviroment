"""Fire / silent unit tests for the S1 manifest red-flag rules (ES-3a)."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s1_manifest_red_flags import (
    ActivationWildcardRule,
    GenericPublisherRule,
    SuspiciousCapabilitiesRule,
)

MakeContext = Callable[..., StaticAnalysisContext]


# --- extrace.s1.activation_wildcard -----------------------------------------


def test_activation_wildcard_fires(make_context: MakeContext) -> None:
    ctx = make_context(manifest={"publisher": "acme", "activationEvents": ["*"]})
    findings = ActivationWildcardRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s1.activation_wildcard"
    assert findings[0].severity.value == "low"
    assert findings[0].evidence and findings[0].evidence[0].type == "manifest"


def test_activation_wildcard_silent_for_specific_events(
    make_context: MakeContext,
) -> None:
    ctx = make_context(manifest={"activationEvents": ["onLanguage:python"]})
    assert ActivationWildcardRule().evaluate(ctx) == []


def test_activation_wildcard_silent_without_manifest(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"extension.js": "x"})
    assert ctx.manifest_relative_path is None
    assert ActivationWildcardRule().evaluate(ctx) == []


# --- extrace.s1.suspicious_capabilities -------------------------------------


def test_suspicious_capabilities_fires_on_install_script(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        manifest={"publisher": "acme", "scripts": {"postinstall": "node x.js"}}
    )
    findings = SuspiciousCapabilitiesRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s1.suspicious_capabilities"
    assert findings[0].severity.value == "medium"
    assert "postinstall" in findings[0].description


def test_suspicious_capabilities_fires_on_untrusted_workspace(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        manifest={
            "publisher": "acme",
            "capabilities": {"untrustedWorkspaces": {"supported": True}},
        }
    )
    findings = SuspiciousCapabilitiesRule().evaluate(ctx)
    assert len(findings) == 1
    assert "untrusted" in findings[0].description.lower()


def test_suspicious_capabilities_silent_for_clean_manifest(
    make_context: MakeContext,
) -> None:
    ctx = make_context(manifest={"publisher": "acme", "scripts": {"build": "tsc"}})
    assert SuspiciousCapabilitiesRule().evaluate(ctx) == []


# --- extrace.s1.generic_publisher -------------------------------------------


def test_generic_publisher_fires_when_missing(make_context: MakeContext) -> None:
    ctx = make_context(manifest={"name": "thing"})
    findings = GenericPublisherRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s1.generic_publisher"


def test_generic_publisher_fires_on_placeholder(make_context: MakeContext) -> None:
    ctx = make_context(manifest={"publisher": "your-example-publisher"})
    assert len(GenericPublisherRule().evaluate(ctx)) == 1


def test_generic_publisher_silent_for_real_publisher(
    make_context: MakeContext,
) -> None:
    ctx = make_context(manifest={"publisher": "ms-python", "name": "python"})
    assert GenericPublisherRule().evaluate(ctx) == []
