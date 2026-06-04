"""Fire / silent unit tests for the A8 runtime reverse-shell rule.

Synthetic ActivationReports (no live sample): a target-owned shell-spawn process
event plus a target-owned outbound socket event reproduce the runtime reverse-
shell shape. The C2 literal is the RFC 5737 documentation range ``203.0.113.10``.
"""

from __future__ import annotations

from packages.analysis_contracts import ActivationReport
from packages.analysis_engine.rules.a8_reverse_shell import ReverseShellRule
from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def _process_event(
    event_id: str,
    command: str,
    rel_time_s: float,
    *,
    target: bool = True,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "kind": "process",
        "rel_time_s": rel_time_s,
        "operation": "exec",
        "is_target_extension_event": target,
        "attribution_status": "strong" if target else "unattributed",
        "raw_context": {
            "event_class": "process",
            "pid": 4321,
            "ppid": 1000,
            "command": command,
            "arguments_preview": "",
            "cwd": "/workspace",
        },
    }


def _network_event(
    event_id: str,
    host: str,
    rel_time_s: float,
    *,
    target: bool = True,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "kind": "network",
        "rel_time_s": rel_time_s,
        "protocol": "tcp",
        "host": host,
        "destination_ip": host,
        "destination_port": 4444,
        "is_target_extension_event": target,
        "attribution_status": "strong" if target else "unattributed",
        "raw_context": {"event_class": "network", "event_type": "connect"},
    }


def _report(*events: dict[str, object]) -> ActivationReport:
    return ActivationReport.model_validate(
        {
            "report_version": 2,
            "target_extension_expected": "extrace.unit",
            "automation_health": {"status": "healthy", "reasons": []},
            "signal_summary": {},
            "summary": {"target_extension_version": "0.0.1"},
            "scenario_traces": [],
            "evidence_events": list(events),
            "network_events": [],
            "file_events": [],
            "log_streams": {"automation": []},
        }
    )


def test_a8_unit_fires_on_shell_spawn_with_outbound() -> None:
    report = _report(
        _process_event("p1", "/bin/sh", 0.5),
        _network_event("n1", "203.0.113.10", 0.9),
    )
    findings = ReverseShellRule().evaluate(report)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.a8.reverse_shell"
    assert finding.severity.value == "high"
    assert finding.confidence.value == "medium"
    assert finding.adversary_class is not None
    assert finding.adversary_class.value == "A8"
    assert "attack.T1059" in finding.categories
    assert "extrace.host.reverse_shell" in finding.categories


def test_a8_unit_silent_without_outbound() -> None:
    report = _report(_process_event("p1", "/bin/sh", 0.5))
    assert ReverseShellRule().evaluate(report) == []


def test_a8_unit_silent_without_shell_spawn() -> None:
    report = _report(_network_event("n1", "203.0.113.10", 0.9))
    assert ReverseShellRule().evaluate(report) == []


def test_a8_unit_silent_for_non_shell_process() -> None:
    # A language-server / build spawn (node, git) is not a shell and must not
    # enter the correlation, even alongside an outbound socket.
    report = _report(
        _process_event("p1", "/usr/bin/node", 0.5),
        _process_event("p2", "/usr/bin/git", 0.6),
        _network_event("n1", "203.0.113.10", 0.9),
    )
    assert ReverseShellRule().evaluate(report) == []


def test_a8_unit_silent_for_benign_outbound() -> None:
    # A shell spawn paired with an allowlisted destination (github.com) is not
    # convicted — the outbound must be to a non-benign endpoint.
    report = _report(
        _process_event("p1", "/bin/bash", 0.5),
        _network_event("n1", "github.com", 0.9),
    )
    assert ReverseShellRule().evaluate(report) == []


def test_a8_unit_silent_when_outside_correlation_window() -> None:
    report = _report(
        _process_event("p1", "/bin/sh", 0.5),
        _network_event("n1", "203.0.113.10", 100.0),
    )
    assert ReverseShellRule().evaluate(report) == []


def test_a8_unit_silent_for_untargeted_spawn() -> None:
    # A shell spawned by some other process (not attributed to the target
    # extension) does not count.
    report = _report(
        _process_event("p1", "/bin/sh", 0.5, target=False),
        _network_event("n1", "203.0.113.10", 0.9),
    )
    assert ReverseShellRule().evaluate(report) == []


def test_a8_fires_for_reverse_shell_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a8-reverse-shell-canary"
    )
    assert "extrace.a8.reverse_shell" in production_rule_ids(bundle)
