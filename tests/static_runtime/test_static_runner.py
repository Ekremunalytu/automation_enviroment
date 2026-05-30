"""Engine-level tests for the in-house static runner (ES-3a, ADR 0016)."""

from __future__ import annotations

import json
from pathlib import Path

from packages.analysis_contracts.static_detection import StaticDetectionReport
from static_runtime.static_runner import run_static_detection_engine


def test_runner_emits_inhouse_tool_record_for_empty_tree(tmp_path: Path) -> None:
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    assert report.findings == []
    assert len(report.tool_executions) == 1
    record = report.tool_executions[0]
    assert record.tool == "inhouse"
    assert record.version == "1.0.0"
    assert record.rules_loaded == 6
    assert record.findings_emitted == 0
    assert report.severity_counts.model_dump() == {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }


def test_runner_rolls_up_findings_for_malicious_tree(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "publisher": "",
                "name": "thing",
                "activationEvents": ["*"],
                "scripts": {"postinstall": "node steal.js"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "addon.node").write_bytes(b"\x7fELF\x00binary")

    report = run_static_detection_engine(
        vsix_dir=str(tmp_path), rules_version="2.0.0", timeout_budget_s=30
    )
    rule_ids = {finding.rule_id for finding in report.findings}
    assert {
        "extrace.s1.activation_wildcard",
        "extrace.s1.generic_publisher",
        "extrace.s1.suspicious_capabilities",
        "extrace.s3.embedded_native_binary",
    } <= rule_ids
    # The rollup + the tool record agree with the findings list.
    counts = report.severity_counts.model_dump()
    assert sum(counts.values()) == len(report.findings)
    assert report.tool_executions[0].findings_emitted == len(report.findings)


def test_runner_report_round_trips_through_contract(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "ms-pyton", "name": "python"}), encoding="utf-8"
    )
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    # Survives a JSON serialize -> validate round-trip (extra="forbid" contract).
    doc = json.loads(report.model_dump_json())
    StaticDetectionReport.model_validate(doc)
    assert doc["schema_version"] == "1"
    assert any(f["rule_id"] == "extrace.s2.typosquat" for f in doc["findings"])


def test_runner_zero_budget_runs_all_rules(tmp_path: Path) -> None:
    # timeout_budget_s == 0 means "no soft budget" -> every rule still runs.
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=0
    )
    assert report.tool_executions[0].rules_loaded == 6
