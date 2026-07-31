"""Coverage for the curated trusted-domain allowlist.

The shared trust catalog feeds ``is_benign_domain``, which the A1/A2/A4/A8
dynamic rules use to exclude reviewed infrastructure from their unknown-outbound
correlations. These tests pin exact/subdomain matching, official additions, and
host-with-port normalization observed in real activation reports.
"""

from __future__ import annotations

import pytest

from packages.analysis_engine.rules._common import is_benign_domain

# Hosts retained from the ms-python.python network surface.
_OBSERVED = (
    "main.vscode-cdn.net",
    "registry.npmjs.org",
    "www.schemastore.org",
)


@pytest.mark.parametrize("host", _OBSERVED)
def test_added_hosts_are_benign(host: str) -> None:
    assert is_benign_domain(host)


@pytest.mark.parametrize("host", _OBSERVED)
def test_subdomains_of_added_hosts_are_benign(host: str) -> None:
    # is_benign_domain matches the exact host or any subdomain (endswith ".<allowed>").
    assert is_benign_domain(f"edge.{host}")


def test_baseline_allowlist_intact() -> None:
    for host in ("github.com", "marketplace.visualstudio.com", "microsoft.com"):
        assert is_benign_domain(host)


@pytest.mark.parametrize(
    "host",
    (
        "edge.vscode-cdn.net",
        "assets.gallery.vsassets.io",
        "assets.gallerycdn.vsassets.io",
        "api.business.githubcopilot.com",
        "copilot-proxy.githubusercontent.com",
        "vscode.dev",
    ),
)
def test_reviewed_official_service_domains_are_benign(host: str) -> None:
    assert is_benign_domain(host)


@pytest.mark.parametrize(
    "host",
    ("localhost:6080", "127.0.0.1:43757", "MARKETPLACE.VISUALSTUDIO.COM:443"),
)
def test_host_with_port_is_normalized_before_matching(host: str) -> None:
    assert is_benign_domain(host)


def test_unknown_host_is_not_benign() -> None:
    # A non-allowlisted host (and a near-miss parent of an allowlisted subdomain)
    # must still read as unknown so the correlation rules can act on it.
    assert not is_benign_domain("pool.evil.invalid")
    assert not is_benign_domain("npmjs.org")  # only registry.npmjs.org is allowed
    assert not is_benign_domain("vsassets.io")
    assert not is_benign_domain("raw.githubusercontent.com")
    assert not is_benign_domain("githubcopilot.com.evil.invalid")
