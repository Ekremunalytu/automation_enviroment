"""Tests for /api/marketplace/search endpoint.

Split from tests/workflows/marketplace/test_router.py during W16-6 to reduce single-file size.
All external calls (HTTP) are mocked via unittest.mock.patch.
"""

from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SEARCH_RESULTS = [
    {
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "displayName": "Python",
        "description": "Python language support.",
        "installs": 100_000_000,
        "rating": 4.8,
    }
]

# ---------------------------------------------------------------------------
# Search Tests
# ---------------------------------------------------------------------------


def test_search_success(client: TestClient) -> None:
    """Normal search returns 200 with a list of extensions."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=SAMPLE_SEARCH_RESULTS,
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "python"
    assert data[0]["publisher"] == "ms-python"
    assert data[0]["installs"] == 100_000_000


def test_search_empty_query(client: TestClient) -> None:
    """Empty query string returns 400."""
    response = client.get("/api/marketplace/search", params={"query": ""})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_whitespace_query(client: TestClient) -> None:
    """Whitespace-only query string returns 400."""
    response = client.get("/api/marketplace/search", params={"query": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_upstream_error(client: TestClient) -> None:
    """httpx.HTTPError from marketplace client results in 502."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        side_effect=httpx.HTTPStatusError(
            "Bad Gateway", request=MagicMock(), response=MagicMock()
        ),
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 502
    assert "Marketplace API unavailable" in response.json()["detail"]


def test_search_network_error(client: TestClient) -> None:
    """httpx.ConnectError (subclass of HTTPError) from marketplace client results in 502."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 502


def test_search_page_size_clamp_low(client: TestClient) -> None:
    """page_size=0 is clamped to 1 (no error raised)."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=[],
    ) as mock_search:
        response = client.get(
            "/api/marketplace/search", params={"query": "test", "page_size": 0}
        )

    assert response.status_code == 200
    # Verify clamped value was passed (1, not 0)
    mock_search.assert_called_once_with("test", 1)


def test_search_page_size_clamp_high(client: TestClient) -> None:
    """page_size=500 is clamped to 100."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=[],
    ) as mock_search:
        response = client.get(
            "/api/marketplace/search", params={"query": "test", "page_size": 500}
        )

    assert response.status_code == 200
    mock_search.assert_called_once_with("test", 100)


def test_search_returns_empty_list(client: TestClient) -> None:
    """Scanner returning [] is a valid 200 response."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=[],
    ):
        response = client.get(
            "/api/marketplace/search", params={"query": "zzznoresults"}
        )

    assert response.status_code == 200
    assert response.json() == []

