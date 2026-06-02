"""Tests for the operator blacklist service (validation + DB flow + live override).

Validation tests are DB-free and run everywhere. The add/list/remove flow is a
``requires_db`` lane (skips without the postgres_test container); it also asserts
the in-process matcher override is refreshed so the dynamic ``a7`` rule sees edits
live.
"""

from __future__ import annotations

import pytest

from packages.analysis_contracts import domain_indicators
from workflows.detection_rules.blacklist_service import (
    BlacklistDomainValidationError,
    add_domain,
    remove_domain,
    validate_domain,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Evil.Example", "evil.example"),
        ("  c2.bad.test.  ", "c2.bad.test"),
        ("sub.domain.co.uk", "sub.domain.co.uk"),
    ],
)
def test_validate_domain_normalizes(raw: str, expected: str) -> None:
    assert validate_domain(raw) == expected


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "not a domain",
        "http://evil.example",
        "evil",  # no dot / no TLD
        "1.2.3.4",  # numeric TLD
        "a..b.com",  # empty label
        "-bad.example",  # label starts with '-'
        "bad-.example",  # label ends with '-'
    ],
)
def test_validate_domain_rejects_malformed(bad: str) -> None:
    with pytest.raises(BlacklistDomainValidationError):
        validate_domain(bad)


@pytest.fixture
def clean_blacklist(test_engine):
    """Wipe the blacklist table + the in-process override around each DB test."""
    from sqlalchemy.orm import Session

    from appcore.storage.models import BlacklistDomain

    def _wipe() -> None:
        with Session(test_engine) as session:
            session.query(BlacklistDomain).delete()
            session.commit()
        domain_indicators.clear_operator_blacklist()

    _wipe()
    yield
    _wipe()


@pytest.mark.requires_db
def test_add_list_remove_flow_and_live_override(db_session, clean_blacklist) -> None:
    view = add_domain(db_session, "Mal-Beacon.Net", added_by="operator")
    assert "mal-beacon.net" in view.operator
    assert "mal-beacon.net" in view.effective
    # The shipped seed is always a subset of the effective list (never dropped).
    assert set(view.seed).issubset(set(view.effective))
    # The in-process override was refreshed -> the dynamic matcher sees it live.
    assert domain_indicators.match_host("sub.mal-beacon.net") == "mal-beacon.net"

    removed, after = remove_domain(db_session, "mal-beacon.net")
    assert removed is True
    assert "mal-beacon.net" not in after.operator
    assert domain_indicators.match_host("mal-beacon.net") is None


@pytest.mark.requires_db
def test_remove_unknown_domain_returns_false(db_session, clean_blacklist) -> None:
    removed, _ = remove_domain(db_session, "never-added.example")
    assert removed is False


@pytest.mark.requires_db
def test_add_is_idempotent(db_session, clean_blacklist) -> None:
    add_domain(db_session, "dup.example")
    view = add_domain(db_session, "dup.example")
    assert view.operator.count("dup.example") == 1
