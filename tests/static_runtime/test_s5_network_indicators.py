"""Fire / silent unit tests for the S5 suspicious-network-endpoint rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s5_network_indicators import SuspiciousNetworkEndpointRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_fires_on_routable_ip_literal(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": 'connect("http://8.8.8.8:4444/x");'})
    findings = SuspiciousNetworkEndpointRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s5.suspicious_network_endpoint"
    assert findings[0].severity.value == "medium"
    assert "routable IPv4 endpoint" in findings[0].description


def test_fires_on_cleartext_http_external_host(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": 'get("http://tracker.badcdn.net/p");'})
    findings = SuspiciousNetworkEndpointRule().evaluate(ctx)
    assert len(findings) == 1
    assert "cleartext http" in findings[0].description


def test_silent_for_private_ip_localhost_and_https(make_context: MakeContext) -> None:
    ctx = make_context(
        files={
            "extension.js": (
                'a("http://127.0.0.1:3000");'
                'b("http://10.0.0.5/x");'
                'c("http://localhost/y");'
                'd("https://api.service.com/z");'
            )
        }
    )
    assert SuspiciousNetworkEndpointRule().evaluate(ctx) == []


def test_silent_for_documentation_ip_and_reserved_tld(
    make_context: MakeContext,
) -> None:
    # 203.0.113.0/24 is RFC 5737 docs (not is_global); .example is reserved.
    ctx = make_context(
        files={"extension.js": 'a("http://203.0.113.9");b("http://x.example/p");'}
    )
    assert SuspiciousNetworkEndpointRule().evaluate(ctx) == []
