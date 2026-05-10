"""Rules must only fire on target-owned evidence, not automation noise."""

from __future__ import annotations

from typing import Any

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import Verdict
from packages.analysis_engine.runner import run_detection
from packages.analysis_engine.rules.a1_credential_read_then_network import (
    CredentialReadThenNetworkRule,
)
from packages.analysis_engine.rules.a2_startup_network_beacon import (
    StartupNetworkBeaconRule,
)
from packages.analysis_engine.rules.a4_workspace_exfil import WorkspaceExfilRule


def _report(events: list[dict[str, Any]]) -> ActivationReport:
    return ActivationReport.model_validate(
        {
            "report_version": 2,
            "target_extension_expected": "extrace.target",
            "automation_health": {"status": "healthy", "reasons": []},
            "signal_summary": {},
            "summary": {},
            "scenario_traces": [],
            "evidence_events": events,
            "network_events": [],
            "file_events": [],
            "log_streams": {"automation": []},
        }
    )


def _a1_events(
    *, is_target: bool = True, attribution: str = "strong"
) -> list[dict[str, Any]]:
    return [
        {
            "event_id": "activation-0001",
            "kind": "extension_host",
            "rel_time_s": 0.0,
            "summary": "Activated extrace.target",
            "raw_context": {"event_class": "activation"},
        },
        {
            "event_id": "file-0001",
            "kind": "file",
            "rel_time_s": 4.0,
            "operation": "read",
            "path": "/home/executor/.ssh/id_rsa",
            "summary": "Credential file read",
            "is_target_extension_event": is_target,
            "attribution_status": attribution,
        },
        {
            "event_id": "network-0001",
            "kind": "network",
            "rel_time_s": 18.0,
            "protocol": "http",
            "host": "collector.evil.invalid",
            "path": "/upload",
            "summary": "Outbound POST to collector",
            "is_target_extension_event": is_target,
            "attribution_status": attribution,
            "raw_context": {
                "event_class": "network",
                "event_type": "http_request",
                "http_method": "POST",
            },
        },
    ]


def test_a1_fires_on_target_owned_evidence() -> None:
    report = run_detection(
        _report(_a1_events()), rules=[CredentialReadThenNetworkRule()]
    )
    assert any(
        finding.rule_id == "extrace.a1.credential_read_then_network"
        for finding in report.findings
    )


def test_a1_stays_silent_for_unattributed_noise() -> None:
    events = _a1_events(is_target=False, attribution="")
    report = run_detection(_report(events), rules=[CredentialReadThenNetworkRule()])
    assert report.findings == []
    assert report.verdict == Verdict.CLEAN


def test_a1_stays_silent_for_foreign_extension_correlative() -> None:
    events = _a1_events(is_target=False, attribution="correlative")
    report = run_detection(_report(events), rules=[CredentialReadThenNetworkRule()])
    assert report.findings == []


def _a4_events(
    *, is_target: bool = True, attribution: str = "strong"
) -> list[dict[str, Any]]:
    return [
        {
            "event_id": "activation-0001",
            "kind": "extension_host",
            "rel_time_s": 0.0,
            "summary": "Activated extrace.target",
            "raw_context": {"event_class": "activation"},
        },
        {
            "event_id": "file-0001",
            "kind": "file",
            "rel_time_s": 8.0,
            "operation": "read",
            "path": "/workspace/secrets.env",
            "summary": "Workspace secret read",
            "is_target_extension_event": is_target,
            "attribution_status": attribution,
        },
        {
            "event_id": "network-0001",
            "kind": "network",
            "rel_time_s": 20.0,
            "protocol": "http",
            "host": "exfil.evil.invalid",
            "path": "/ingest",
            "summary": "Outbound workspace upload",
            "is_target_extension_event": is_target,
            "attribution_status": attribution,
            "raw_context": {
                "event_class": "network",
                "event_type": "http_request",
                "http_method": "POST",
            },
        },
    ]


def test_a4_stays_silent_for_unattributed_workspace_io() -> None:
    events = _a4_events(is_target=False, attribution="")
    report = run_detection(_report(events), rules=[WorkspaceExfilRule()])
    assert report.findings == []


def _a2_events(
    *,
    event_type: str,
    is_target: bool = True,
    attribution: str = "strong",
) -> list[dict[str, Any]]:
    rel_times = [0.8, 2.1, 3.8, 5.2]
    events: list[dict[str, Any]] = [
        {
            "event_id": "activation-0001",
            "kind": "extension_host",
            "rel_time_s": 0.0,
            "summary": "Activated extrace.target",
            "raw_context": {"event_class": "activation"},
        },
    ]
    for index, rel_time in enumerate(rel_times, start=1):
        events.append(
            {
                "event_id": f"network-{index:04d}",
                "kind": "network",
                "rel_time_s": rel_time,
                "protocol": "tls",
                "host": "pool.evil.invalid",
                "summary": "Outbound TLS beacon",
                "is_target_extension_event": is_target,
                "attribution_status": attribution,
                "raw_context": {
                    "event_class": "network",
                    "event_type": event_type,
                },
            }
        )
    return events


def test_a2_accepts_live_tls_client_hello_vocabulary() -> None:
    report = run_detection(
        _report(_a2_events(event_type="tls_client_hello")),
        rules=[StartupNetworkBeaconRule()],
    )
    assert any(
        finding.rule_id == "extrace.a2.startup_network_beacon"
        for finding in report.findings
    )


def test_a2_stays_silent_for_unattributed_tls_burst() -> None:
    events = _a2_events(event_type="tls_client_hello", is_target=False, attribution="")
    report = run_detection(_report(events), rules=[StartupNetworkBeaconRule()])
    assert report.findings == []
