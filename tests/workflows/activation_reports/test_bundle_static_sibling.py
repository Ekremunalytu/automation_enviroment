"""The Reports `/bundle` route folds in the sibling static pre-check report.

Static analysis is persisted separately as ``static_report_{job_id}.json`` (a
``CombinedAnalysisBundle``). The bundle route links an activation report to its
sibling via the shared 12-hex ``job_id`` prefix and exposes the
``StaticAnalysisReport`` on ``ReportBundle.static_report`` so the Reports UI can
render static + dynamic rule activation together. A missing / ambiguous /
unreadable sibling must degrade to ``null`` — never a 500.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]

# Activation report whose trailing token (``abc123def456``) is the 12-hex job_id
# prefix the resolver globs the static sibling on.
_ACTIVATION_NAME = "activation_report_pub.ext-1.0.0-abc123def456.json"
_JOB_ID_PREFIX = "abc123def456"


def _activation_payload() -> dict[str, Any]:
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


def _combined_bundle_payload(*, fired_rule_id: str, decision: str) -> dict[str, Any]:
    from appcore.contracts.schema_defs.static_analysis_bundle import (
        CombinedAnalysisBundle,
        StaticAnalysisReport,
    )
    from packages.analysis_contracts.static_detection import (
        StaticDetectionReport,
        StaticGateOutcome,
    )
    from packages.analysis_contracts.static_detection.report import (
        StaticDetectionFinding,
        StaticToolExecutionRecord,
    )

    finding = StaticDetectionFinding(
        rule_id=fired_rule_id,
        rule_version="1.0.0",
        rule_lifecycle="production",
        categories=["attack.T1105", "extrace.ext.native_binary"],
        severity="medium",
        confidence="high",
        title="Embedded native binary",
        description="Ships embedded native/binary files.",
    )
    tool = StaticToolExecutionRecord(
        tool="inhouse",
        version="0.0.0",
        rules_loaded=6,
        findings_emitted=1,
        duration_ms=10,
        status="ok",
    )
    bundle = CombinedAnalysisBundle(
        static_report=StaticAnalysisReport(
            detection_report=StaticDetectionReport(
                findings=[finding],
                tool_executions=[tool],
            ),
            gate_outcome=StaticGateOutcome(
                decision=decision,
                warned_by=[fired_rule_id] if decision == "warn" else [],
            ),
        ),
        dynamic_bundle=None,
    )
    return bundle.model_dump(mode="json")


def _seed_activation(output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)
    (output_dir / _ACTIVATION_NAME).write_text(
        json.dumps(_activation_payload()),
        encoding="utf-8",
    )


def _get(client: TestClient, output_dir: Path) -> Any:
    with patch(
        "workflows.activation_reports.router._get_output_dir",
        return_value=output_dir,
    ):
        return client.get(f"/api/activations/{_ACTIVATION_NAME}/bundle")


def test_bundle_attaches_static_sibling(client: TestClient, tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    _seed_activation(output_dir)
    # Sibling shares the 12-hex token, then any suffix (full job_id is 32 hex).
    (
        output_dir / f"static_report_{_JOB_ID_PREFIX}deadbeefcafe0000feed.json"
    ).write_text(
        json.dumps(
            _combined_bundle_payload(
                fired_rule_id="extrace.s3.embedded_native_binary",
                decision="warn",
            )
        ),
        encoding="utf-8",
    )

    response = _get(client, output_dir)

    assert response.status_code == 200
    payload = response.json()
    # Dynamic side still present and unchanged.
    assert "detection_report" in payload
    static = payload["static_report"]
    assert static is not None
    assert static["gate_outcome"]["decision"] == "warn"
    assert static["detection_report"]["findings"][0]["rule_id"] == (
        "extrace.s3.embedded_native_binary"
    )


def test_bundle_static_null_when_no_sibling(client: TestClient, tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    _seed_activation(output_dir)

    response = _get(client, output_dir)

    assert response.status_code == 200
    assert response.json()["static_report"] is None


def test_bundle_static_null_when_ambiguous(client: TestClient, tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    _seed_activation(output_dir)
    payload = json.dumps(
        _combined_bundle_payload(
            fired_rule_id="extrace.s2.typosquat",
            decision="warn",
        )
    )
    # Two siblings sharing the same 12-hex prefix → ambiguous, refuse to guess.
    (
        output_dir / f"static_report_{_JOB_ID_PREFIX}aaaaaaaaaaaaaaaaaaaa.json"
    ).write_text(payload, encoding="utf-8")
    (
        output_dir / f"static_report_{_JOB_ID_PREFIX}bbbbbbbbbbbbbbbbbbbb.json"
    ).write_text(payload, encoding="utf-8")

    response = _get(client, output_dir)

    assert response.status_code == 200
    assert response.json()["static_report"] is None


def test_bundle_static_null_when_sibling_unreadable(
    client: TestClient, tmp_path: Path
) -> None:
    output_dir = tmp_path / "output"
    _seed_activation(output_dir)
    (
        output_dir / f"static_report_{_JOB_ID_PREFIX}ffffffffffffffffffff.json"
    ).write_text("{not valid json", encoding="utf-8")

    response = _get(client, output_dir)

    # Degraded artifact must not crash the bundle read.
    assert response.status_code == 200
    assert response.json()["static_report"] is None
