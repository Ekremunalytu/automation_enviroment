"""
Tests for Activation Reports Router
===================================

Tests for /api/activations endpoints.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_output_dir(tmp_path: Path):
    """
    Creates a temporary output directory and patches the router to use it.
    """
    # Create the directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Patch the _get_output_dir function in the router
    with patch("routers.activations._get_output_dir", return_value=output_dir):
        yield output_dir


def create_report(directory: Path, filename: str, content: dict, delay: float = 0):
    """Helper to create a JSON report file with an optional delay for mtime."""
    if delay:
        time.sleep(delay)

    file_path = directory / filename
    with open(file_path, "w") as f:
        json.dump(content, f)
    return file_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_list_activations_empty(client: TestClient, mock_output_dir: Path):
    """Test listing activations when no reports exist."""
    response = client.get("/api/activations")
    assert response.status_code == 200
    assert response.json() == []


def test_list_activations_sorted(client: TestClient, mock_output_dir: Path):
    """Test that reports are listed sorted by modification time (newest first)."""
    # Create files with delay to ensure different mtimes
    create_report(mock_output_dir, "old.json", {"id": 1})
    # Small sleep to guarantee mtime difference on fast filesystems
    time.sleep(0.01)
    create_report(mock_output_dir, "new.json", {"id": 2})

    response = client.get("/api/activations")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["filename"] == "new.json"
    assert data[1]["filename"] == "old.json"


def test_get_latest_activation(client: TestClient, mock_output_dir: Path):
    """Test fetching the latest activation report."""
    create_report(mock_output_dir, "first.json", {"data": "first"})
    time.sleep(0.01)
    create_report(mock_output_dir, "second.json", {"data": "second"})

    response = client.get("/api/activations/latest")
    assert response.status_code == 200
    data = response.json()

    assert data["data"] == "second"
    assert data["_metadata"]["filename"] == "second.json"


def test_get_latest_activation_404(client: TestClient, mock_output_dir: Path):
    """Test 404 when fetching latest report from empty directory."""
    response = client.get("/api/activations/latest")
    assert response.status_code == 404
    assert "No activation reports found" in response.json()["detail"]


def test_get_activation_by_name(client: TestClient, mock_output_dir: Path):
    """Test fetching a specific report by name."""
    create_report(mock_output_dir, "target.json", {"target": True})

    response = client.get("/api/activations/target.json")
    assert response.status_code == 200
    assert response.json()["target"] is True
    assert response.json()["_metadata"]["filename"] == "target.json"


def test_get_activation_by_name_404(client: TestClient, mock_output_dir: Path):
    """Test fetching a non-existent report."""
    response = client.get("/api/activations/ghost.json")
    assert response.status_code == 404


def test_get_activation_security_traversal(client: TestClient, mock_output_dir: Path):
    """Test path traversal protection."""
    # Test with ".." which is blocked by our logic
    response = client.get("/api/activations/suspicious..name.json")
    assert response.status_code == 400
    assert "Invalid filename" in response.json()["detail"]


def test_read_report_corrupt_json(client: TestClient, mock_output_dir: Path):
    """Test handling of corrupt JSON files."""
    # Write invalid JSON
    with open(mock_output_dir / "bad.json", "w") as f:
        f.write("{ invalid json }")

    response = client.get("/api/activations/bad.json")
    assert response.status_code == 500
    assert "Failed to read report file" in response.json()["detail"]
