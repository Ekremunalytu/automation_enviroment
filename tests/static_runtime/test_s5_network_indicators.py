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


def test_silent_for_external_cleartext_urls_in_documentation(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        files={
            "README.md": "See http://downloads.example.org/install for details.",
            "docs/setup.txt": "Legacy guide: http://legacy.vendor.org/setup",
            "LICENSE": "License reference: http://license.vendor.org/text",
            "dist/extension.js.map": '{"sourceRoot":"http://source.vendor.org/src"}',
        }
    )
    assert SuspiciousNetworkEndpointRule().evaluate(ctx) == []


def test_silent_for_manifest_documentation_metadata(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        manifest={
            "name": "documented-extension",
            "publisher": "trusted-vendor",
            "version": "1.0.0",
            "homepage": "http://homepage.vendor.org/project",
            "repository": {
                "type": "git",
                "url": "http://git.vendor.org/project.git",
            },
            "bugs": {"url": "http://bugs.vendor.org/project"},
            "funding": "http://funding.vendor.org/project",
        }
    )
    assert SuspiciousNetworkEndpointRule().evaluate(ctx) == []


def test_manifest_runtime_configuration_endpoint_still_fires(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        manifest={
            "name": "runtime-config-extension",
            "publisher": "trusted-vendor",
            "version": "1.0.0",
            "contributes": {
                "configuration": {
                    "properties": {
                        "extension.endpoint": {
                            "default": "http://runtime.vendor.org/api"
                        }
                    }
                }
            },
        }
    )
    findings = SuspiciousNetworkEndpointRule().evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].evidence[0].type == "manifest"
    assert findings[0].evidence[0].line_number is None


def test_malformed_manifest_endpoint_remains_visible(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        files={
            "package.json": (
                '{"name":"broken","endpoint":"http://runtime.vendor.org/api",'
            )
        }
    )
    findings = SuspiciousNetworkEndpointRule().evaluate(ctx)

    assert ctx.manifest_status == "malformed"
    assert len(findings) == 1
    assert findings[0].evidence[0].type == "manifest"
    assert findings[0].evidence[0].line_number is None


def test_runtime_source_with_same_cleartext_url_still_fires(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        files={"extension.js": 'fetch("http://legacy.vendor.org/payload");'}
    )
    assert len(SuspiciousNetworkEndpointRule().evaluate(ctx)) == 1


def test_evidence_is_capped_but_description_reports_all_hits(
    make_context: MakeContext,
) -> None:
    urls = "\n".join(
        f'fetch("http://host{i:02d}.vendor.org/payload");' for i in range(30)
    )
    ctx = make_context(files={"extension.js": urls})
    findings = SuspiciousNetworkEndpointRule().evaluate(ctx)

    assert len(findings) == 1
    assert len(findings[0].evidence) == 25
    assert "30 suspicious network endpoint(s)" in findings[0].description
