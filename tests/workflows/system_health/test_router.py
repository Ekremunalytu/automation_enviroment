"""System health API contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from appcore.contracts.schemas import SystemHealthResponse


def test_system_health_endpoint_returns_aggregate_snapshot(
    client: TestClient,
    monkeypatch,
) -> None:
    from workflows.system_health import router

    monkeypatch.setattr(
        router,
        "build_system_health",
        lambda _db: SystemHealthResponse(
            observed_at=datetime(2026, 7, 28, 10, 0, tzinfo=UTC),
            services=[],
            inventory=[],
        ),
    )

    response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json() == {
        "observed_at": "2026-07-28T10:00:00Z",
        "services": [],
        "inventory": [],
    }
