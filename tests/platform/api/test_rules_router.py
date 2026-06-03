"""TestClient coverage for the editable /api/rules/blacklist-domains surface.

``requires_db``: the endpoints are DB-backed, so this runs against the
postgres_test lane (skips locally without it). The denylist table + the
in-process override are wiped around each test for isolation.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from packages.analysis_contracts import domain_indicators

pytestmark = pytest.mark.requires_db


@pytest.fixture(autouse=True)
def clean_blacklist(test_engine):
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


def test_get_returns_seed_with_empty_operator(db_client: TestClient) -> None:
    response = db_client.get("/api/rules/blacklist-domains")
    assert response.status_code == 200
    body = response.json()
    assert body["seed"] == sorted(domain_indicators.seed_domains())
    assert body["operator"] == []
    assert body["effective"] == sorted(domain_indicators.seed_domains())
    assert body["count"] == len(domain_indicators.seed_domains())


def test_post_adds_then_delete_removes(db_client: TestClient) -> None:
    added = db_client.post(
        "/api/rules/blacklist-domains", json={"domain": "Mal-Beacon.Net"}
    )
    assert added.status_code == 200
    body = added.json()
    assert "mal-beacon.net" in body["operator"]
    assert "mal-beacon.net" in body["effective"]

    # A fresh GET reflects the addition.
    fetched = db_client.get("/api/rules/blacklist-domains").json()
    assert "mal-beacon.net" in fetched["operator"]

    deleted = db_client.delete("/api/rules/blacklist-domains/mal-beacon.net")
    assert deleted.status_code == 200
    assert "mal-beacon.net" not in deleted.json()["operator"]


def test_post_invalid_domain_returns_422(db_client: TestClient) -> None:
    response = db_client.post(
        "/api/rules/blacklist-domains", json={"domain": "http://not a domain"}
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "invalid_blacklist_domain"


def test_delete_unknown_domain_returns_404(db_client: TestClient) -> None:
    response = db_client.delete("/api/rules/blacklist-domains/never-added.example")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "blacklist_domain_not_found"
