"""W8-5 security regression: router-level path-traversal + slug regex gate.

The activation-report router exposes ``/api/activations/{name}`` and
``/api/activations/{name}/bundle``. Both gate the ``name`` path parameter
through ``ACTIVATION_REPORT_NAME_RE`` (W8-5), so adversarial inputs are
rejected with HTTP 422 *before* the handler runs and never reach the
filesystem.

This test consolidates the adversarial coverage previously scattered
across `test_router.py:test_get_activation_security_traversal` (single
``..`` case) into seven adversarial classes parametrized over both
endpoints.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_output_dir(tmp_path: Path):
    """Mirror ``test_router.py``'s mock_output_dir so the gate test stays
    isolated from on-disk reports."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    with patch(
        "workflows.activation_reports.router._get_output_dir",
        return_value=output_dir,
    ):
        yield output_dir


_ADVERSARIAL_NAMES = [
    pytest.param("suspicious..name.json", id="missing-activation-prefix-and-traversal"),
    pytest.param(
        quote("activation_report_\\bad.json", safe=""), id="encoded-backslash"
    ),
    pytest.param(quote("activation_report_\x00.json", safe=""), id="encoded-null-byte"),
    pytest.param(".activation_report_pub.name-1.0.json", id="leading-dot"),
    pytest.param("activation_report_-bad.json", id="leading-dash-in-slug"),
    pytest.param("activation_report_" + "x" * 80 + ".json", id="overlength-slug"),
    pytest.param("report_pub.name-1.0.0.json", id="missing-activation-prefix"),
    pytest.param("activation_report_pub.name-1.0.0.txt", id="wrong-suffix"),
]


@pytest.mark.parametrize("name", _ADVERSARIAL_NAMES)
def test_get_activation_by_name_rejects_adversarial_path(
    name: str, client: TestClient, mock_output_dir: Path
) -> None:
    response = client.get(f"/api/activations/{name}")
    assert response.status_code == 422, (
        f"adversarial path was not rejected: {name!r} → {response.status_code}"
    )


@pytest.mark.parametrize("name", _ADVERSARIAL_NAMES)
def test_get_activation_bundle_rejects_adversarial_path(
    name: str, client: TestClient, mock_output_dir: Path
) -> None:
    response = client.get(f"/api/activations/{name}/bundle")
    assert response.status_code == 422, (
        f"adversarial bundle path was not rejected: {name!r} → {response.status_code}"
    )


def test_canonical_filename_passes_gate_then_404s(
    client: TestClient, mock_output_dir: Path
) -> None:
    """Whitelist proof: a name that satisfies the regex passes the 422 gate
    and reaches the 404 fallthrough (file does not exist on disk)."""
    response = client.get("/api/activations/activation_report_pub.name-1.0.0.json")
    assert response.status_code == 404


def test_canonical_filename_passes_gate_then_404s_on_bundle(
    client: TestClient, mock_output_dir: Path
) -> None:
    response = client.get(
        "/api/activations/activation_report_pub.name-1.0.0.json/bundle"
    )
    assert response.status_code == 404


def test_list_endpoint_filters_malformed_names(
    client: TestClient, mock_output_dir: Path
) -> None:
    """W9-6b: ``GET /api/activations`` must drop glob hits that fail the
    canonical-name regex. The single-name endpoints already gate via
    ``Path(..., pattern=...)``; this closes the listing-side gap so a
    locally-writable file like ``activation_report_evil.json`` never
    surfaces to API consumers.
    """
    valid_name = "activation_report_pub.name-1.0.0.json"
    # Names that match the glob ``activation_report*.json`` but fail
    # ``ACTIVATION_REPORT_NAME_RE`` (slug body must satisfy
    # MARKETPLACE_SLUG_TOKEN_RE: ``[A-Za-z0-9][-_.A-Za-z0-9]{0,64}``).
    malformed_names = [
        "activation_report_-bad.json",  # leading dash violates first-char class
        "activation_report_" + "x" * 80 + ".json",  # body length > 65
        "activation_report_a b.json",  # whitespace inside the body
    ]
    payload = '{"report_version": 1}'
    (mock_output_dir / valid_name).write_text(payload)
    for name in malformed_names:
        (mock_output_dir / name).write_text(payload)

    response = client.get("/api/activations")
    assert response.status_code == 200
    returned = {entry["filename"] for entry in response.json()}
    assert returned == {valid_name}
