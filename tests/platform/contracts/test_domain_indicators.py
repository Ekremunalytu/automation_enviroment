"""Unit tests for the shared blacklist-domain matcher (blacklist_domains feature).

``packages.analysis_contracts.domain_indicators`` is the single stdlib-only leaf
shared by the static ``s4_blacklisted_domain`` rule and the dynamic
``a7_blacklisted_domain`` rule, so its host-suffix / registrable-boundary
semantics are exercised here directly. The denylist is pointed at a temp file so
assertions are independent of the curated ``blacklist_domains.txt`` contents.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import pytest

from packages.analysis_contracts import domain_indicators


def _reset_caches() -> None:
    domain_indicators._seed_domains.cache_clear()
    domain_indicators._compile_pattern.cache_clear()
    domain_indicators.clear_operator_blacklist()


@pytest.fixture
def blacklist(tmp_path, monkeypatch) -> Callable[[Iterable[str]], None]:
    def _set(domains: Iterable[str]) -> None:
        path = tmp_path / "blacklist_domains.txt"
        path.write_text(
            "# comment line\n" + "\n".join(domains) + "\n", encoding="utf-8"
        )
        monkeypatch.setattr(domain_indicators, "_BLACKLIST_DOMAIN_PATH", path)
        _reset_caches()

    yield _set
    # Restore the real curated list for any later test in the session.
    _reset_caches()


def test_loader_ignores_comments_and_blanks(blacklist) -> None:
    blacklist(["evil.example", "", "  ", "exfil.test"])
    assert domain_indicators.blacklisted_domains() == frozenset(
        {"evil.example", "exfil.test"}
    )


def test_match_host_exact_and_subdomain(blacklist) -> None:
    blacklist(["evil.example"])
    assert domain_indicators.match_host("evil.example") == "evil.example"
    assert domain_indicators.match_host("c2.evil.example") == "evil.example"
    assert domain_indicators.match_host("A.B.EVIL.EXAMPLE.") == "evil.example"


def test_match_host_registrable_boundary_safe(blacklist) -> None:
    blacklist(["evil.example"])
    # A different registrable domain must NOT match.
    assert domain_indicators.match_host("notevil.example") is None
    assert domain_indicators.match_host("evil.example.org") is None
    assert domain_indicators.match_host("good.com") is None
    assert domain_indicators.match_host("") is None


def test_find_in_text_finds_hosts_with_subdomains(blacklist) -> None:
    blacklist(["evil.example", "beacon.test"])
    text = 'fetch("https://c2.evil.example/cb"); ping("beacon.test")'
    assert domain_indicators.find_in_text(text) == ["beacon.test", "evil.example"]


def test_find_in_text_boundary_safe(blacklist) -> None:
    blacklist(["evil.example"])
    assert domain_indicators.find_in_text("see notevil.example/x") == []
    assert domain_indicators.find_in_text("see evil.example.org/x") == []


def test_find_in_text_empty_blacklist_is_silent(blacklist) -> None:
    blacklist([])
    assert domain_indicators.find_in_text("anything evil.example here") == []
    assert domain_indicators.match_host("evil.example") is None


def test_curated_seed_file_loads_and_is_nonempty() -> None:
    # After the fixture teardown the real curated denylist is read again.
    domain_indicators._seed_domains.cache_clear()
    seed = domain_indicators.blacklisted_domains()
    assert seed
    assert all(domain == domain.strip().lower() for domain in seed)


def test_operator_override_augments_seed(blacklist) -> None:
    blacklist(["evil.example"])
    # Operator additions union with the seed and are subdomain-matched live.
    domain_indicators.set_operator_blacklist(["Custom-Bad.Test", "evil.example", ""])
    assert domain_indicators.operator_domains() == frozenset(
        {"custom-bad.test", "evil.example"}
    )
    assert domain_indicators.match_host("a.b.custom-bad.test") == "custom-bad.test"
    assert domain_indicators.match_host("c2.evil.example") == "evil.example"
    assert domain_indicators.find_in_text("hit custom-bad.test here") == [
        "custom-bad.test"
    ]


def test_clear_operator_override_returns_to_seed(blacklist) -> None:
    blacklist(["evil.example"])
    domain_indicators.set_operator_blacklist(["custom-bad.test"])
    domain_indicators.clear_operator_blacklist()
    assert domain_indicators.operator_domains() == frozenset()
    assert domain_indicators.match_host("custom-bad.test") is None
    assert domain_indicators.match_host("evil.example") == "evil.example"


def test_static_container_default_is_seed_only(blacklist) -> None:
    # Without any set_operator_blacklist call (the static container case), the
    # effective list equals the seed.
    blacklist(["evil.example", "exfil.test"])
    assert domain_indicators.blacklisted_domains() == frozenset(
        {"evil.example", "exfil.test"}
    )


def test_seed_loader_missing_file_degrades_to_empty(tmp_path, monkeypatch) -> None:
    """An unreadable seed file degrades to an empty denylist instead of raising.

    The matcher leaf is imported by both the dynamic engine and the hardened
    static-analyzer container; a missing/unreadable ``blacklist_domains.txt``
    must not crash either surface. Covers the ``except OSError`` fallback in
    ``_seed_domains`` — and confirms an operator override still applies on top of
    the empty seed.
    """
    missing = tmp_path / "nonexistent" / "blacklist_domains.txt"
    monkeypatch.setattr(domain_indicators, "_BLACKLIST_DOMAIN_PATH", missing)
    _reset_caches()
    try:
        assert domain_indicators.seed_domains() == frozenset()
        assert domain_indicators.blacklisted_domains() == frozenset()
        assert domain_indicators.match_host("evil.example") is None
        # The operator override is independent of the seed file and still works.
        domain_indicators.set_operator_blacklist(["op-only.test"])
        assert domain_indicators.match_host("a.b.op-only.test") == "op-only.test"
    finally:
        _reset_caches()
