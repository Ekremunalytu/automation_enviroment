"""Coverage for the operator-curated benign-domain allowlist.

``benign_domains.txt`` feeds ``is_benign_domain``, which the a2 / a4 / a7 dynamic
rules use to exclude trusted hosts from their "unknown outbound" correlations.
These tests guard the allowlist additions (legitimate VS Code / npm / schema
infrastructure observed on the ms-python.python scan surface) so a future trim
regresses visibly, and pin the exact-or-subdomain matching contract.
"""

from __future__ import annotations

import pytest

from packages.analysis_engine.rules._common import is_benign_domain

# Hosts added to benign_domains.txt from the ms-python.python network surface.
_ADDED = (
    "main.vscode-cdn.net",
    "registry.npmjs.org",
    "www.schemastore.org",
)


@pytest.mark.parametrize("host", _ADDED)
def test_added_hosts_are_benign(host: str) -> None:
    assert is_benign_domain(host)


@pytest.mark.parametrize("host", _ADDED)
def test_subdomains_of_added_hosts_are_benign(host: str) -> None:
    # is_benign_domain matches the exact host or any subdomain (endswith ".<allowed>").
    assert is_benign_domain(f"edge.{host}")


def test_baseline_allowlist_intact() -> None:
    for host in ("github.com", "marketplace.visualstudio.com", "microsoft.com"):
        assert is_benign_domain(host)


def test_unknown_host_is_not_benign() -> None:
    # A non-allowlisted host (and a near-miss parent of an allowlisted subdomain)
    # must still read as unknown so the correlation rules can act on it.
    assert not is_benign_domain("pool.evil.invalid")
    assert not is_benign_domain("npmjs.org")  # only registry.npmjs.org is allowed
