"""Contract and safety tests for the shared trusted-entity catalog."""

from __future__ import annotations

from packages.analysis_contracts import (
    match_trusted_domain,
    normalize_observed_host,
    trusted_domains,
    trusted_entity_catalog,
)


def test_catalog_exposes_reviewed_organizations_and_publishers() -> None:
    catalog = trusted_entity_catalog()
    by_id = {organization.id: organization for organization in catalog.organizations}

    assert by_id["microsoft-vscode"].kind == "company"
    assert "ms-python" in by_id["microsoft-vscode"].publishers
    assert by_id["github"].publishers == ["github"]
    assert by_id["eclipse-open-vsx"].kind == "foundation"


def test_catalog_domains_are_unique_and_include_existing_baseline() -> None:
    domains = trusted_domains()
    assert {
        "127.0.0.1",
        "example.com",
        "github.com",
        "localhost",
        "microsoft.com",
        "open-vsx.org",
        "registry.npmjs.org",
        "visualstudio.com",
        "www.schemastore.org",
    } <= domains
    assert len(domains) == sum(
        len(organization.domains)
        for organization in trusted_entity_catalog().organizations
    )


def test_observed_host_normalization_handles_ports_urls_and_ipv6() -> None:
    assert normalize_observed_host("LOCALHOST:6080") == "localhost"
    assert normalize_observed_host("https://Marketplace.VisualStudio.com/path") == (
        "marketplace.visualstudio.com"
    )
    assert normalize_observed_host("[::1]:443") == "::1"


def test_matching_is_suffix_bounded_and_prefers_specific_entry() -> None:
    assert match_trusted_domain("edge.vscode-cdn.net:443") == "vscode-cdn.net"
    assert match_trusted_domain("api.github.com") == "github.com"
    assert match_trusted_domain("raw.githubusercontent.com") is None
    assert match_trusted_domain("github.com.evil.invalid") is None
