"""End-to-end coverage for operator-tunable executor preferences."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.requires_db


def test_dynamic_analysis_defaults_to_off(db_client: TestClient) -> None:
    response = db_client.get("/api/settings/executor/preferences")

    assert response.status_code == 200
    assert response.json() == {"dynamic_analysis_enabled": False}


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/marketplace/analyze",
        "/api/marketplace/analyze/start",
    ],
)
def test_analysis_endpoints_reach_vsix_validation_while_dynamic_is_off(
    db_client: TestClient,
    endpoint: str,
) -> None:
    response = db_client.post(
        endpoint,
        json={"publisher": "example", "name": "blocked", "version": "1.0.0"},
    )

    # Dynamic-off selects the static-only pipeline; it no longer rejects the
    # request before the artifact/static stages. The missing artifact proves
    # routing reached the existing VSIX validation boundary.
    assert response.status_code == 404


def test_dynamic_analysis_preference_persists(db_client: TestClient) -> None:
    response = db_client.put(
        "/api/settings/executor/preferences",
        json={"dynamic_analysis_enabled": True, "updated_by": "operator-test"},
    )

    assert response.status_code == 200
    assert response.json() == {"dynamic_analysis_enabled": True}
    assert db_client.get("/api/settings/executor/preferences").json() == {
        "dynamic_analysis_enabled": True
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/marketplace/analyze",
        "/api/marketplace/analyze/start",
    ],
)
def test_dynamic_analysis_endpoints_pass_the_gate_while_on(
    db_client: TestClient,
    endpoint: str,
) -> None:
    update = db_client.put(
        "/api/settings/executor/preferences",
        json={"dynamic_analysis_enabled": True},
    )
    assert update.status_code == 200

    response = db_client.post(
        endpoint,
        json={"publisher": "example", "name": "missing", "version": "1.0.0"},
    )

    # The missing artifact proves execution passed the preference gate and
    # reached the existing VSIX validation path.
    assert response.status_code == 404


@pytest.mark.parametrize("invalid_value", [1, "true", None])
def test_dynamic_analysis_preference_requires_a_boolean(
    db_client: TestClient,
    invalid_value: object,
) -> None:
    response = db_client.put(
        "/api/settings/executor/preferences",
        json={"dynamic_analysis_enabled": invalid_value},
    )

    assert response.status_code == 422
    assert db_client.get("/api/settings/executor/preferences").json() == {
        "dynamic_analysis_enabled": False
    }
