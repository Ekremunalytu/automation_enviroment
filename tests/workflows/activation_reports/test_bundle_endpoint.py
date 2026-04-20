from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]


def _malicious_report_payload() -> dict[str, object]:
    payload = json.loads(
        (
            REPO_ROOT
            / "extensions"
            / "malicious"
            / "t1-a1-credential-read-canary"
            / "activation_report.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_activation_bundle_endpoint_returns_detection_report(
    client: TestClient,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    report_name = "activation_report_fixture_bundle.json"
    (output_dir / report_name).write_text(
        json.dumps(_malicious_report_payload()),
        encoding="utf-8",
    )

    with patch(
        "workflows.activation_reports.router._get_output_dir",
        return_value=output_dir,
    ):
        response = client.get(f"/api/activations/{report_name}/bundle")
        legacy_response = client.get(f"/api/activations/{report_name}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["detection_report"]["verdict"] == "malicious"
    assert payload["detection_report"]["findings"]
    assert (
        payload["detection_report"]["findings"][0]["rule_id"]
        == "extrace.a1.credential_read_then_network"
    )

    assert legacy_response.status_code == 200
    assert legacy_response.json()["target_extension_expected"] == (
        "extrace.t1-a1-credential-read-canary"
    )
