"""Tests for the marketplace HTTP client helpers."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from workflows.marketplace import client as marketplace_client


def test_search_marketplace_parses_gallery_response() -> None:
    """Marketplace search responses should be flattened into API records."""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [
            {
                "extensions": [
                    {
                        "publisher": {"publisherName": "ms-python"},
                        "extensionName": "python",
                        "versions": [{"version": "2025.0.0"}],
                        "displayName": "Python",
                        "shortDescription": "Python language support.",
                        "statistics": [
                            {"statisticName": "install", "value": 123456},
                            {"statisticName": "averagerating", "value": 4.876},
                        ],
                    }
                ]
            }
        ]
    }
    http_client = MagicMock()
    http_client.post.return_value = response
    context_manager = MagicMock()
    context_manager.__enter__.return_value = http_client

    with patch(
        "workflows.marketplace.client.httpx.Client",
        return_value=context_manager,
    ):
        results = marketplace_client.search_marketplace("python", page_size=5)

    assert results == [
        {
            "publisher": "ms-python",
            "name": "python",
            "version": "2025.0.0",
            "displayName": "Python",
            "description": "Python language support.",
            "installs": 123456,
            "rating": 4.88,
        }
    ]
    http_client.post.assert_called_once()


def test_download_and_extract_vsix_is_idempotent(monkeypatch, tmp_path: Path) -> None:
    """Existing extracted extensions should be reused without downloading again."""
    monkeypatch.setattr(
        marketplace_client.settings.project,
        "EXTENSION_DIR",
        str(tmp_path),
    )

    ext_dir = tmp_path / "ms-python.python-2025.0.0"
    ext_dir.mkdir()
    (ext_dir / "package.json").write_text('{"name": "python"}', encoding="utf-8")
    marketplace_client.get_vsix_path(
        "ms-python",
        "python",
        "2025.0.0",
    ).write_bytes(b"vsix")

    with patch("workflows.marketplace.client.httpx.Client") as mock_client:
        result = marketplace_client.download_and_extract_vsix(
            "ms-python", "python", "2025.0.0"
        )

    assert result == ext_dir
    mock_client.assert_not_called()


def test_download_and_extract_vsix_downloads_and_extracts(
    monkeypatch, tmp_path: Path
) -> None:
    """Only safe files under extension/ should be written to disk."""
    monkeypatch.setattr(
        marketplace_client.settings.project,
        "EXTENSION_DIR",
        str(tmp_path),
    )

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("extension/", "")
        zip_file.writestr("extension/package.json", '{"name": "python"}')
        zip_file.writestr("extension/src/mod.py", "print('ok')")
        zip_file.writestr("other/ignored.txt", "ignored")
        zip_file.writestr("extension/../escape.txt", "blocked")
    vsix_bytes = archive.getvalue()

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.content = vsix_bytes
    http_client = MagicMock()
    http_client.get.return_value = response
    context_manager = MagicMock()
    context_manager.__enter__.return_value = http_client

    with patch(
        "workflows.marketplace.client.httpx.Client",
        return_value=context_manager,
    ):
        result = marketplace_client.download_and_extract_vsix(
            "ms-python", "python", "2025.0.0"
        )

    assert result == tmp_path / "ms-python.python-2025.0.0"
    assert (result / "package.json").read_text(encoding="utf-8") == '{"name": "python"}'
    assert (result / "src" / "mod.py").read_text(encoding="utf-8") == "print('ok')"
    assert (
        marketplace_client.get_vsix_path("ms-python", "python", "2025.0.0").read_bytes()
        == vsix_bytes
    )
    assert not (tmp_path / "escape.txt").exists()
    assert not (result / "ignored.txt").exists()
