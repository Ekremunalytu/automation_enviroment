"""End-to-end coverage for the operator-tunable security thresholds router.

Pins:
- ``GET /api/settings/security/thresholds`` returns defaults when the table
  is empty (fresh install / fresh transaction).
- ``PUT`` persists a partial update and the next ``GET`` reflects it.
- ``PUT`` of an out-of-bounds value returns HTTP 422 with a structured
  detail and does NOT touch the DB (atomic validation).
- ``PUT`` of an unknown key is rejected before any write.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from workflows.security_settings.defaults import (
    VSIX_MAX_COMPRESSION_RATIO_KEY,
    VSIX_MAX_FILE_COUNT_KEY,
    VSIX_MAX_UNCOMPRESSED_SIZE_KEY,
    VSIX_THRESHOLD_DEFAULTS,
)


pytestmark = pytest.mark.requires_db


def test_get_thresholds_returns_defaults_when_empty(db_client: TestClient) -> None:
    response = db_client.get("/api/settings/security/thresholds")
    assert response.status_code == 200

    body = response.json()
    assert body["values"] == VSIX_THRESHOLD_DEFAULTS
    assert body["defaults"] == VSIX_THRESHOLD_DEFAULTS
    assert set(body["bounds"].keys()) == set(VSIX_THRESHOLD_DEFAULTS.keys())
    for bound in body["bounds"].values():
        assert bound["min_value"] < bound["max_value"]


def test_put_persists_partial_update(db_client: TestClient) -> None:
    payload = {
        "values": {VSIX_MAX_FILE_COUNT_KEY: 75_000},
        "updated_by": "operator-test",
    }
    response = db_client.put("/api/settings/security/thresholds", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["values"][VSIX_MAX_FILE_COUNT_KEY] == 75_000
    # Other keys still report defaults.
    assert (
        body["values"][VSIX_MAX_UNCOMPRESSED_SIZE_KEY]
        == VSIX_THRESHOLD_DEFAULTS[VSIX_MAX_UNCOMPRESSED_SIZE_KEY]
    )

    # Next GET reflects the persisted update.
    follow_up = db_client.get("/api/settings/security/thresholds").json()
    assert follow_up["values"][VSIX_MAX_FILE_COUNT_KEY] == 75_000


def test_put_below_min_bound_rejected_with_structured_detail(
    db_client: TestClient,
) -> None:
    payload = {"values": {VSIX_MAX_COMPRESSION_RATIO_KEY: 5}}
    response = db_client.put("/api/settings/security/thresholds", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_threshold_value"
    assert detail["key"] == VSIX_MAX_COMPRESSION_RATIO_KEY
    assert detail["value"] == 5
    assert "out of allowed range" in detail["reason"]

    # No write occurred — GET still shows defaults.
    follow_up = db_client.get("/api/settings/security/thresholds").json()
    assert (
        follow_up["values"][VSIX_MAX_COMPRESSION_RATIO_KEY]
        == VSIX_THRESHOLD_DEFAULTS[VSIX_MAX_COMPRESSION_RATIO_KEY]
    )


def test_put_above_max_bound_rejected(db_client: TestClient) -> None:
    payload = {"values": {VSIX_MAX_FILE_COUNT_KEY: 10_000_000}}
    response = db_client.put("/api/settings/security/thresholds", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["key"] == VSIX_MAX_FILE_COUNT_KEY
    assert detail["value"] == 10_000_000


def test_put_unknown_key_rejected(db_client: TestClient) -> None:
    payload = {"values": {"vsix_unknown_setting": 42}}
    response = db_client.put("/api/settings/security/thresholds", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_threshold_value"
    assert detail["key"] == "vsix_unknown_setting"
    assert "unknown threshold key" in detail["reason"]


def test_put_empty_values_dict_is_noop(db_client: TestClient) -> None:
    response = db_client.put("/api/settings/security/thresholds", json={"values": {}})
    assert response.status_code == 200
    assert response.json()["values"] == VSIX_THRESHOLD_DEFAULTS
