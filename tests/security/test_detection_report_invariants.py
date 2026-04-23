from __future__ import annotations

import pytest

from packages.analysis_contracts import (
    Confidence,
    detection_report_invariant_issues,
    quantize_confidence,
)


def _activation_payload(event_ids: list[str]) -> dict[str, object]:
    return {
        "evidence_events": [
            {"event_id": event_id, "kind": "file"} for event_id in event_ids
        ]
    }


def test_detection_report_clean_when_evidence_resolves() -> None:
    activation = _activation_payload(["file-0001", "network-0002"])
    detection = {
        "findings": [
            {
                "id": "01J000000000000000000FIND01",
                "evidence": [
                    {"event_id": "file-0001", "type": "filesystem_read"},
                    {"event_id": "network-0002", "type": "network_request"},
                ],
            }
        ],
        "rules_executed": [
            {
                "rule_id": "extrace.a1.credential_read_then_network",
                "finding_ids": ["01J000000000000000000FIND01"],
            }
        ],
    }

    assert detection_report_invariant_issues(detection, activation) == []


def test_detection_report_flags_unknown_evidence_event() -> None:
    activation = _activation_payload(["file-0001"])
    detection = {
        "findings": [
            {
                "id": "01J000000000000000000FIND02",
                "evidence": [
                    {"event_id": "file-0001"},
                    {"event_id": "file-9999"},
                ],
            }
        ],
        "rules_executed": [],
    }

    issues = detection_report_invariant_issues(detection, activation)

    assert any("file-9999" in issue for issue in issues)
    assert all("file-0001" not in issue for issue in issues)


def test_detection_report_flags_dangling_rule_finding_id() -> None:
    activation = _activation_payload(["file-0001"])
    detection = {
        "findings": [
            {
                "id": "01J000000000000000000FIND03",
                "evidence": [{"event_id": "file-0001"}],
            }
        ],
        "rules_executed": [
            {
                "rule_id": "extrace.a4.workspace_exfil",
                "finding_ids": ["01J000000000000000000MISSING"],
            }
        ],
    }

    issues = detection_report_invariant_issues(detection, activation)

    assert any("MISSING" in issue for issue in issues)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.99, Confidence.HIGH),
        (0.85, Confidence.HIGH),
        (0.84999, Confidence.MEDIUM),
        (0.65, Confidence.MEDIUM),
        (0.6499, Confidence.LOW),
        (0.0, Confidence.LOW),
    ],
)
def test_quantize_confidence_matches_contract_thresholds(
    score: float, expected: Confidence
) -> None:
    assert quantize_confidence(score) is expected
