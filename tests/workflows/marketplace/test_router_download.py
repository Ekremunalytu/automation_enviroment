"""Tests for /api/marketplace/download endpoint.

Split from tests/workflows/marketplace/test_router.py during W16-6 to reduce single-file size.
All external calls (HTTP + DB writes) are mocked via unittest.mock.patch.
"""

from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from workflows.extension_catalog.manifest_reader import PackageJsonReadError
from workflows.marketplace import router as marketplace_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
# Download Tests
# ---------------------------------------------------------------------------


def _mock_extension(db_id: int = 42) -> MagicMock:
    """Build a mock ORM Extension object."""
    ext = MagicMock()
    ext.id = db_id
    return ext


def test_download_threshold_breach_returns_structured_422(client: TestClient) -> None:
    """W12-* hardening: when ``download_and_extract_vsix`` raises
    ``VSIXUnpackError`` with structured breach metadata, the router maps
    it to HTTP 422 with a JSON detail object the UI popup can consume."""
    from workflows.marketplace.client import (
        VSIX_BREACH_ENTRY_COUNT,
        VSIXUnpackError,
    )

    err = VSIXUnpackError(
        "VSIX archive exceeds entry count limit (50000)",
        breach_kind=VSIX_BREACH_ENTRY_COUNT,
        threshold_name="vsix_max_file_count",
        threshold_value=50_000,
        observed_value=50_001,
    )

    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2026.5.2026050801",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "vsix_threshold_breach"
    assert detail["breach_kind"] == VSIX_BREACH_ENTRY_COUNT
    assert detail["threshold_name"] == "vsix_max_file_count"
    assert detail["threshold_value"] == 50_000
    assert detail["observed_value"] == 50_001
    assert detail["publisher"] == "ms-python"
    assert detail["name"] == "python"
    assert detail["version"] == "2026.5.2026050801"


def test_download_threshold_breach_accepts_float_observed_value(
    client: TestClient,
) -> None:
    from workflows.marketplace.client import (
        VSIX_BREACH_COMPRESSION_RATIO,
        VSIXUnpackError,
    )

    err = VSIXUnpackError(
        "VSIX compression ratio 101.5:1 exceeds limit (100:1)",
        breach_kind=VSIX_BREACH_COMPRESSION_RATIO,
        threshold_name="vsix_max_compression_ratio",
        threshold_value=100,
        observed_value=101.5,
    )

    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2026.5.2026050801",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["breach_kind"] == VSIX_BREACH_COMPRESSION_RATIO
    assert detail["observed_value"] == 101.5


def test_download_legacy_vsix_unpack_error_falls_back_to_string_detail(
    client: TestClient,
) -> None:
    """Older raise sites that do not pass ``breach_kind`` keep the
    backwards-compat HTTPException with a plain string detail (still 422,
    so the UI surfaces a generic threshold error rather than 500)."""
    from workflows.marketplace.client import VSIXUnpackError

    err = VSIXUnpackError("legacy unstructured failure")

    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "legacy unstructured failure"


def test_download_success(client: TestClient) -> None:
    """Successful download returns 200 with db_id."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            return_value=_mock_extension(42),
        ) as mock_create,
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
    mock_create.assert_called_once_with(
        ANY,
        ext_path,
        expected_name="python",
        expected_publisher="ms-python",
        expected_version="2025.0.0",
    )


def test_download_duplicate_returns_existing_extension(client: TestClient) -> None:
    """Duplicate catalog insert should still return a usable download response."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=ValueError("Duplicate entry"),
        ),
        patch(
            "workflows.marketplace.router.search_extension_by_name",
            return_value=_mock_extension(42),
        ) as mock_search,
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
    assert "already downloaded" in data["message"]
    mock_search.assert_called_once_with(
        ANY,
        "python",
        extension_publisher="ms-python",
        extension_version="2025.0.0",
    )


def test_download_duplicate_without_existing_record_returns_409(
    client: TestClient,
) -> None:
    """Keep the conflict response if the duplicate cannot be resolved to a stored extension."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=ValueError("Duplicate entry"),
        ),
        patch(
            "workflows.marketplace.router.search_extension_by_name",
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

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_download_missing_manifest_returns_specific_500(client: TestClient) -> None:
    """Missing package.json should surface a diagnostic 500 detail."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=PackageJsonReadError.missing(ext_path / "package.json"),
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
    assert "package.json is missing" in response.json()["detail"]


def test_download_invalid_manifest_returns_specific_500(client: TestClient) -> None:
    """Invalid package.json should surface a parse-specific 500 detail."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=PackageJsonReadError.invalid_json(
                ext_path / "package.json",
                "Expecting property name enclosed in double quotes",
            ),
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
    assert "contains invalid JSON" in response.json()["detail"]


def test_download_manifest_mismatch_returns_502(client: TestClient) -> None:
    """Manifest mismatch from downloaded VSIX should surface as upstream failure."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=marketplace_router.ExtensionManifestMismatchError(
                "Downloaded extension metadata does not match the requested artifact."
            ),
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

    assert response.status_code == 502
    assert "does not match" in response.json()["detail"]


def test_download_network_error_502(client: TestClient) -> None:
    """httpx.HTTPError during VSIX download → 502."""
    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
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
        "workflows.marketplace.client.download_and_extract_vsix",
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

