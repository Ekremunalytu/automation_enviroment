"""
Tests for Marketplace Router
=============================

Tests for /api/marketplace/search and /api/marketplace/download endpoints.
All external calls (HTTP + DB writes) are mocked via unittest.mock.patch.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from scanner.executor import ExecutorError

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

SAMPLE_DOWNLOAD_RESPONSE = {
    "status": "success",
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
    "extension_dir": "/app/extensions/ms-python.python-2025.0.0",
    "db_id": 42,
    "message": (
        "Extension ms-python.python@2025.0.0 downloaded and analyzed successfully."
    ),
}


# ---------------------------------------------------------------------------
# Search Tests
# ---------------------------------------------------------------------------


def test_search_success(client: TestClient) -> None:
    """Normal search returns 200 with a list of extensions."""
    with patch(
        "scanner.marketplace.search_marketplace",
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
    """httpx.HTTPError from scanner results in 502."""
    with patch(
        "scanner.marketplace.search_marketplace",
        side_effect=httpx.HTTPStatusError(
            "Bad Gateway", request=MagicMock(), response=MagicMock()
        ),
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 502
    assert "Marketplace API unavailable" in response.json()["detail"]


def test_search_network_error(client: TestClient) -> None:
    """httpx.ConnectError (subclass of HTTPError) from scanner results in 502."""
    with patch(
        "scanner.marketplace.search_marketplace",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 502


def test_search_page_size_clamp_low(client: TestClient) -> None:
    """page_size=0 is clamped to 1 (no error raised)."""
    with patch(
        "scanner.marketplace.search_marketplace",
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
        "scanner.marketplace.search_marketplace",
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
        "scanner.marketplace.search_marketplace",
        return_value=[],
    ):
        response = client.get(
            "/api/marketplace/search", params={"query": "zzznoresults"}
        )

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Download Tests
# ---------------------------------------------------------------------------


def _mock_extension(db_id: int = 42) -> MagicMock:
    """Build a mock ORM Extension object."""
    ext = MagicMock()
    ext.id = db_id
    return ext


def test_download_success(client: TestClient) -> None:
    """Successful download returns 200 with db_id."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "scanner.marketplace.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "routers.marketplace.create_extension_by_name",
            return_value=_mock_extension(42),
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["db_id"] == 42
    assert data["publisher"] == "ms-python"
    assert data["name"] == "python"
    assert data["version"] == "2025.0.0"


def test_download_duplicate_409(client: TestClient) -> None:
    """ValueError from create_extension_by_name → 409 Conflict."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "scanner.marketplace.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "routers.marketplace.create_extension_by_name",
            side_effect=ValueError("Duplicate entry"),
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_download_none_from_service_500(client: TestClient) -> None:
    """None from create_extension_by_name (package.json missing) → 500."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "scanner.marketplace.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "routers.marketplace.create_extension_by_name",
            return_value=None,
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 500
    assert "package.json" in response.json()["detail"]


def test_download_network_error_502(client: TestClient) -> None:
    """httpx.HTTPError during VSIX download → 502."""
    with patch(
        "scanner.marketplace.download_and_extract_vsix",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 502
    assert "Failed to download" in response.json()["detail"]


def test_download_missing_publisher_422(client: TestClient) -> None:
    """Missing required field 'publisher' → 422 Unprocessable Entity."""
    response = client.post(
        "/api/marketplace/download",
        json={"name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422


def test_download_missing_name_422(client: TestClient) -> None:
    """Missing required field 'name' → 422."""
    response = client.post(
        "/api/marketplace/download",
        json={"publisher": "ms-python", "version": "2025.0.0"},
    )
    assert response.status_code == 422


def test_download_empty_publisher_422(client: TestClient) -> None:
    """Empty string for 'publisher' (min_length=1) → 422."""
    response = client.post(
        "/api/marketplace/download",
        json={"publisher": "", "name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422


def test_download_http_status_error_502(client: TestClient) -> None:
    """httpx.HTTPStatusError during download → 502."""
    with patch(
        "scanner.marketplace.download_and_extract_vsix",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "nonexistent",
                "name": "nonexistent",
                "version": "0.0.0",
            },
        )

    assert response.status_code == 502


# ---------------------------------------------------------------------------
# Analyze Tests
# ---------------------------------------------------------------------------

ANALYZE_PAYLOAD = {
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
}


def _vsix_path_exists(exists: bool = True):
    """Return a mock Path whose .exists() returns the given value."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = exists
    mock_path.name = "ms-python.python-2025.0.0.vsix"
    return mock_path


def test_analyze_success(client: TestClient) -> None:
    """Successful analyze returns 200 with install and automation output."""
    with (
        patch(
            "scanner.marketplace.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "routers.marketplace.reset_executor_sandbox_state",
            return_value="Sandbox reset.",
        ),
        patch(
            "routers.marketplace.install_extension_in_executor",
            return_value="Extension installed successfully.",
        ),
        patch(
            "routers.marketplace.run_playwright_automation",
            return_value="Automation completed.",
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["install_output"] == "Extension installed successfully."
    assert data["automation_output"] == "Automation completed."
    assert data["report_path"].startswith(
        "activation_report_ms-python.python-2025.0.0-"
    )
    assert data["report_path"].endswith(".json")


def test_analyze_vsix_not_found_404(client: TestClient) -> None:
    """Missing .vsix file returns 404."""
    with patch(
        "scanner.marketplace.get_vsix_path",
        return_value=_vsix_path_exists(False),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 404
    assert "VSIX file not found" in response.json()["detail"]


def test_analyze_install_failure_502(client: TestClient) -> None:
    """ExecutorError during install returns 502."""
    with (
        patch(
            "scanner.marketplace.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "routers.marketplace.reset_executor_sandbox_state",
            return_value="Sandbox reset.",
        ),
        patch(
            "routers.marketplace.install_extension_in_executor",
            side_effect=ExecutorError("Install failed", returncode=1, output="error"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "install extension" in response.json()["detail"].lower()


def test_analyze_automation_failure_502(client: TestClient) -> None:
    """ExecutorError during automation returns 502."""
    with (
        patch(
            "scanner.marketplace.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "routers.marketplace.reset_executor_sandbox_state",
            return_value="Sandbox reset.",
        ),
        patch(
            "routers.marketplace.install_extension_in_executor",
            return_value="ok",
        ),
        patch(
            "routers.marketplace.run_playwright_automation",
            side_effect=ExecutorError("Automation crashed", returncode=1, output="err"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "Automation crashed" in response.json()["detail"]


def test_analyze_start_returns_job_snapshot(client: TestClient) -> None:
    """Async analyze start returns a queued job payload."""
    with (
        patch(
            "scanner.marketplace.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch("routers.marketplace.threading.Thread") as mock_thread,
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["publisher"] == ANALYZE_PAYLOAD["publisher"]
    assert len(payload["steps"]) == 5
    assert payload["report_path"].startswith(
        "activation_report_ms-python.python-2025.0.0-"
    )
    mock_thread.return_value.start.assert_called_once()


def test_analyze_start_missing_vsix_404(client: TestClient) -> None:
    """Async analyze start validates the VSIX before queueing a job."""
    with patch(
        "scanner.marketplace.get_vsix_path",
        return_value=_vsix_path_exists(False),
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 404
    assert "VSIX file not found" in response.json()["detail"]


def test_get_analysis_job_status_404(client: TestClient) -> None:
    """Unknown analysis jobs return 404."""
    response = client.get("/api/marketplace/analyze/missing-job")
    assert response.status_code == 404


def test_analyze_missing_publisher_422(client: TestClient) -> None:
    """Missing publisher field returns 422."""
    response = client.post(
        "/api/marketplace/analyze",
        json={"name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422
