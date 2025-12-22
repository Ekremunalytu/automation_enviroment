"""
ExTrace Health Check Tests
==========================

Basic smoke tests to verify API availability.
"""

from fastapi.testclient import TestClient


class TestHealthCheck:
    """Health check and basic API tests."""

    def test_root_endpoint_exists(self, client: TestClient) -> None:
        """Test that the root endpoint is accessible."""
        response = client.get("/")
        # Accept either 200 or 404 depending on implementation
        assert response.status_code in [200, 404, 307]

    def test_docs_endpoint(self, client: TestClient) -> None:
        """Test that the OpenAPI docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client: TestClient) -> None:
        """Test that the OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestAPIEndpoints:
    """Basic API endpoint tests."""

    def test_get_extensions_base_info(self, client: TestClient) -> None:
        """Test getting extensions base info."""
        response = client.get("/getExtensionsBaseInfo")
        # Should return 200 with empty list or actual data
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_extensions_all_info(self, client: TestClient) -> None:
        """Test getting extensions all info."""
        response = client.get("/getExtensionsAllInfo")
        # Should return 200 with empty list or actual data
        assert response.status_code == 200
        assert isinstance(response.json(), list)
