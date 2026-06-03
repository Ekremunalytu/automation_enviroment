from __future__ import annotations

from packages.analysis_contracts import ActivationReport
from packages.analysis_engine.rules.a5_workspace_file_tamper import (
    WorkspaceFileTamperRule,
)
from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def _file_event(
    event_id: str, operation: str, path: str, rel_time_s: float, *, target: bool = True
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "kind": "file",
        "rel_time_s": rel_time_s,
        "operation": operation,
        "path": path,
        "is_target_extension_event": target,
        "attribution_status": "strong" if target else "unattributed",
        "raw_context": {"event_class": "file"},
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


def _fires(report: ActivationReport) -> bool:
    return bool(WorkspaceFileTamperRule().evaluate(report))


def test_a5_unit_fires_on_read_then_write_same_path() -> None:
    report = _report(
        _file_event("f1", "read", "/workspace/wallet.txt", 5.0),
        _file_event("f2", "write", "/workspace/wallet.txt", 9.0),
    )
    findings = WorkspaceFileTamperRule().evaluate(report)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.a5.workspace_file_tamper"
    assert findings[0].adversary_class is not None
    assert findings[0].adversary_class.value == "A5"


def test_a5_unit_silent_when_write_precedes_read() -> None:
    # A write that happens before the only read of that path is not a
    # scan-then-rewrite — it must not fire.
    report = _report(
        _file_event("f1", "write", "/workspace/wallet.txt", 5.0),
        _file_event("f2", "read", "/workspace/wallet.txt", 9.0),
    )
    assert not _fires(report)


def test_a5_unit_silent_for_write_to_unread_path() -> None:
    # Reading one file and writing a *different* file is normal codegen, not a
    # rewrite-in-place of scanned content.
    report = _report(
        _file_event("f1", "read", "/workspace/a.txt", 5.0),
        _file_event("f2", "write", "/workspace/b.txt", 9.0),
    )
    assert not _fires(report)


def test_a5_unit_silent_when_not_target_owned() -> None:
    # Read+write of the same path by a non-target actor is out of scope.
    report = _report(
        _file_event("f1", "read", "/workspace/wallet.txt", 5.0, target=False),
        _file_event("f2", "write", "/workspace/wallet.txt", 9.0, target=False),
    )
    assert not _fires(report)


def test_a5_unit_silent_for_write_outside_workspace() -> None:
    # A read+write outside /workspace/ (e.g. the extension's own storage) is not
    # tampering with the user's project files.
    report = _report(
        _file_event("f1", "read", "/home/dev/.cache/wallet.txt", 5.0),
        _file_event("f2", "write", "/home/dev/.cache/wallet.txt", 9.0),
    )
    assert not _fires(report)


def test_a5_rule_fires_for_workspace_file_tamper_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a5-file-tamper-canary"
    )

    assert "extrace.a5.workspace_file_tamper" in production_rule_ids(bundle)


def test_a5_rule_is_silent_for_workspace_exfil_canary() -> None:
    # The A4 canary reads a workspace file but exfiltrates over the network; it
    # never writes back, so the integrity/clipper rule must stay silent.
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a4-workspace-exfil-canary"
    )

    assert "extrace.a5.workspace_file_tamper" not in production_rule_ids(bundle)
