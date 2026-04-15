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
    with patch(
        "workflows.activation_reports.router._get_output_dir", return_value=output_dir
    ):
        yield output_dir


def create_report(directory: Path, filename: str, content: dict, delay: float = 0):
    """Helper to create a JSON report file with an optional delay for mtime."""
    if delay:
        time.sleep(delay)

    file_path = directory / filename
    with open(file_path, "w") as f:
        json.dump(content, f)
    return file_path


def build_valid_report(**overrides: object) -> dict[str, object]:
    report: dict[str, object] = {
        "report_version": 2,
        "target_extension_expected": "ms-python.python",
        "target_extension_observed": False,
        "automation_health": {"status": "ok", "reasons": []},
        "verdict": {},
        "summary": {"total_activated": 0},
        "scenario_traces": [],
        "evidence_events": [],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
    }
    report.update(overrides)
    return report


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
    create_report(mock_output_dir, "activation_report_old.json", {"id": 1})
    # Small sleep to guarantee mtime difference on fast filesystems
    time.sleep(0.01)
    create_report(mock_output_dir, "activation_report_new.json", {"id": 2})
    create_report(mock_output_dir, "triggers_ignored.json", {"selected_scenarios": []})

    response = client.get("/api/activations")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["filename"] == "activation_report_new.json"
    assert data[1]["filename"] == "activation_report_old.json"


def test_get_latest_activation(client: TestClient, mock_output_dir: Path):
    """Test fetching the latest activation report."""
    create_report(
        mock_output_dir,
        "activation_report_first.json",
        build_valid_report(target_extension_expected="first.publisher"),
    )
    time.sleep(0.01)
    create_report(
        mock_output_dir,
        "activation_report_second.json",
        build_valid_report(
            target_extension_expected="second.publisher",
            report_version=2,
            evidence_events=[{"event_id": "activation-0001", "kind": "activation"}],
            evidence_links=[],
        ),
    )

    response = client.get("/api/activations/latest")
    assert response.status_code == 200
    data = response.json()

    assert data["target_extension_expected"] == "second.publisher"
    assert data["report_version"] == 2
    assert data["evidence_events"][0]["event_id"] == "activation-0001"
    assert data["evidence_links"] == []
    assert data["_metadata"]["filename"] == "activation_report_second.json"


def test_get_latest_activation_skips_corrupt_newest(
    client: TestClient, mock_output_dir: Path
):
    """Test latest endpoint falls back when newest JSON is corrupt."""
    create_report(
        mock_output_dir,
        "activation_report_good.json",
        build_valid_report(target_extension_expected="good.publisher"),
    )
    time.sleep(0.01)
    with open(mock_output_dir / "activation_report_broken.json", "w") as f:
        f.write("{ invalid json }")

    response = client.get("/api/activations/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["target_extension_expected"] == "good.publisher"
    assert data["_metadata"]["filename"] == "activation_report_good.json"


def test_get_latest_activation_skips_non_object_newest(
    client: TestClient, mock_output_dir: Path
):
    """Test latest endpoint falls back when newest JSON is not an object."""
    create_report(
        mock_output_dir,
        "activation_report_good.json",
        build_valid_report(target_extension_expected="good.publisher"),
    )
    time.sleep(0.01)
    with open(mock_output_dir / "activation_report_array.json", "w") as f:
        json.dump([{"data": "array"}], f)

    response = client.get("/api/activations/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["target_extension_expected"] == "good.publisher"
    assert data["_metadata"]["filename"] == "activation_report_good.json"


def test_get_latest_activation_skips_schema_invalid_newest(
    client: TestClient, mock_output_dir: Path
):
    """Schema-invalid newest reports should be skipped like other invalid files."""
    create_report(
        mock_output_dir,
        "activation_report_valid.json",
        build_valid_report(target_extension_expected="valid.publisher"),
    )
    time.sleep(0.01)
    create_report(
        mock_output_dir,
        "activation_report_invalid.json",
        {"report_version": 2, "unexpected": True},
    )

    response = client.get("/api/activations/latest")

    assert response.status_code == 200
    data = response.json()
    assert data["target_extension_expected"] == "valid.publisher"
    assert data["_metadata"]["filename"] == "activation_report_valid.json"


def test_get_latest_activation_returns_500_when_all_reports_are_invalid(
    client: TestClient,
    mock_output_dir: Path,
):
    """Corrupt report sets should surface the underlying read failure."""
    with open(mock_output_dir / "activation_report_newer.json", "w") as f:
        f.write("{ invalid json }")
    time.sleep(0.01)
    with open(mock_output_dir / "activation_report_older.json", "w") as f:
        json.dump([{"bad": "shape"}], f)

    response = client.get("/api/activations/latest")

    assert response.status_code == 500
    assert "activation_report_" in response.json()["detail"]


def test_get_latest_activation_404(client: TestClient, mock_output_dir: Path):
    """Test 404 when fetching latest report from empty directory."""
    response = client.get("/api/activations/latest")
    assert response.status_code == 404
    assert "No activation reports found" in response.json()["detail"]


def test_get_activation_by_name(client: TestClient, mock_output_dir: Path):
    """Test fetching a specific report by name."""
    create_report(
        mock_output_dir,
        "activation_report_target.json",
        build_valid_report(
            report_version=1,
            target_extension_expected="target.publisher",
        ),
    )

    response = client.get("/api/activations/activation_report_target.json")
    assert response.status_code == 200
    assert response.json()["target_extension_expected"] == "target.publisher"
    assert response.json()["report_version"] == 1
    assert response.json()["_metadata"]["filename"] == "activation_report_target.json"


def test_get_activation_by_name_404(client: TestClient, mock_output_dir: Path):
    """Test fetching a non-existent report."""
    response = client.get("/api/activations/activation_report_ghost.json")
    assert response.status_code == 404


def test_get_activation_security_traversal(client: TestClient, mock_output_dir: Path):
    """Test path traversal protection."""
    # Test with ".." which is blocked by our logic
    response = client.get("/api/activations/suspicious..name.json")
    assert response.status_code == 400
    assert "Invalid filename" in response.json()["detail"]


def test_get_activation_rejects_non_report_name(
    client: TestClient, mock_output_dir: Path
):
    """Only activation report filenames are allowed."""
    create_report(mock_output_dir, "triggers_hidden.json", {"selected_scenarios": []})

    response = client.get("/api/activations/triggers_hidden.json")
    assert response.status_code == 400
    assert "Invalid activation report name" in response.json()["detail"]


def test_read_report_corrupt_json(client: TestClient, mock_output_dir: Path):
    """Test handling of corrupt JSON files."""
    # Write invalid JSON
    with open(mock_output_dir / "activation_report_bad.json", "w") as f:
        f.write("{ invalid json }")

    response = client.get("/api/activations/activation_report_bad.json")
    assert response.status_code == 500
    assert "Failed to read report file" in response.json()["detail"]


def test_get_activation_by_name_returns_500_for_schema_invalid_report(
    client: TestClient, mock_output_dir: Path
):
    """A schema-invalid JSON object should not pass activation report validation."""
    create_report(
        mock_output_dir,
        "activation_report_invalid.json",
        {"report_version": 2, "unexpected": True},
    )

    response = client.get("/api/activations/activation_report_invalid.json")

    assert response.status_code == 500
    assert "activation report contract validation" in response.json()["detail"]
