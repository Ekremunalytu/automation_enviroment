"""Engine-level tests for the in-house + Semgrep static runner (ES-3a/ES-4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pytest

from packages.analysis_contracts.detection.enums import (
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticDetectionReport,
    StaticToolExecutionRecord,
)
from static_runtime import static_runner
from static_runtime.semgrep_runner import SemgrepRunResult
from static_runtime.static_runner import run_static_detection_engine


def _inhouse_only(
    *, vsix_dir: str, rules_version: str, timeout_budget_s: int
) -> StaticDetectionReport:
    """Run the in-house pass only; the Semgrep combine is covered separately
    (fake runner below + the container smoke test)."""
    return run_static_detection_engine(
        vsix_dir=vsix_dir,
        rules_version=rules_version,
        timeout_budget_s=timeout_budget_s,
        semgrep_enabled=False,
    )


def test_runner_emits_inhouse_tool_record_for_empty_tree(tmp_path: Path) -> None:
    report = _inhouse_only(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    assert report.findings == []
    assert len(report.tool_executions) == 1
    record = report.tool_executions[0]
    assert record.tool == "inhouse"
    assert record.version == "1.0.0"
    assert record.rules_loaded == 26
    assert record.findings_emitted == 0
    assert record.status == "partial"
    assert report.partial is True
    assert "manifest_missing" in report.coverage.coverage_reasons
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
                "capabilities": {"untrustedWorkspaces": {"supported": True}},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "addon.node").write_bytes(b"\x7fELF\x00binary")

    report = _inhouse_only(
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
    report = _inhouse_only(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    # Survives a JSON serialize -> validate round-trip (extra="forbid" contract).
    doc = json.loads(report.model_dump_json())
    StaticDetectionReport.model_validate(doc)
    assert doc["schema_version"] == "2"
    assert any(f["rule_id"] == "extrace.s2.typosquat" for f in doc["findings"])


def test_runner_zero_budget_runs_all_rules(tmp_path: Path) -> None:
    # timeout_budget_s == 0 means "no soft budget" -> every rule still runs.
    report = _inhouse_only(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=0
    )
    assert report.tool_executions[0].rules_loaded == 26


# --------------------------------------------------------------------------
# ES-4 in-house degraded-coverage observability — a swallowed rule error or an
# early soft-budget break must surface as a `partial` record (never a silent
# clean ALLOW). The production-rule list is monkeypatched so the test owns the
# rule set without disturbing the module-global builtin registry.
# --------------------------------------------------------------------------


def _finding(rule_id: str) -> StaticDetectionFinding:
    return StaticDetectionFinding(
        rule_id=rule_id,
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["attack.T1059", "extrace.ext.dynamic_code_exec"],
        severity=Severity.LOW,
        confidence=Confidence.LOW,
        title="t",
        description="d",
    )


class _EmittingRule:
    """A minimal in-house rule that always emits one finding."""

    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id

    def evaluate(self, _context: object) -> list[StaticDetectionFinding]:
        return [_finding(self.rule_id)]


class _RaisingRule:
    """An in-house rule that raises one of `_RULE_EVALUATION_ERRORS`."""

    rule_id = "extrace.test.bad"

    def evaluate(self, _context: object) -> list[StaticDetectionFinding]:
        raise ValueError("rule blew up")


def test_inhouse_rule_error_degrades_to_partial_and_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A rule that raises must degrade to no finding, be recorded in
    # `errored_rule_ids`, and flip the record (and report) to `partial` — the
    # healthy rule still contributes.
    monkeypatch.setattr(
        static_runner,
        "get_production_rules",
        lambda: [_EmittingRule("extrace.test.good"), _RaisingRule()],
    )
    report = _inhouse_only(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    record = report.tool_executions[0]
    assert record.status == "partial"
    assert record.error_count == 1
    assert record.errored_rule_ids == ["extrace.test.bad"]
    assert "tool_error" in record.coverage.coverage_reasons
    assert report.partial is True
    assert record.findings_emitted == 1
    assert [f.rule_id for f in report.findings] == ["extrace.test.good"]


def test_inhouse_budget_trip_marks_partial_and_stops_early(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The soft budget is checked between rules. Drive `time.monotonic` so the
    # check trips before the second rule. The first three reads (the outer
    # `run_static_detection_engine` start, the `_run_inhouse` start, and rule-1's
    # pre-eval check) sit at 0.0 so rule-1 runs; every later read is past the
    # 30s budget so rule-2's check breaks the loop before it evaluates.
    monkeypatch.setattr(
        static_runner,
        "get_production_rules",
        lambda: [
            _EmittingRule("extrace.test.first"),
            _EmittingRule("extrace.test.second"),
        ],
    )
    reads = {"n": 0}

    def _fake_monotonic() -> float:
        reads["n"] += 1
        return 0.0 if reads["n"] <= 3 else 100.0

    monkeypatch.setattr(static_runner.time, "monotonic", _fake_monotonic)
    report = _inhouse_only(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    record = report.tool_executions[0]
    # The break is the budget, not a rule error: `partial` with no error count.
    assert record.status == "partial"
    assert report.partial is True
    assert record.error_count == 0
    assert record.errored_rule_ids == []
    assert "budget_stop" in record.coverage.coverage_reasons
    # Only the first rule ran before the budget tripped.
    assert record.findings_emitted == 1
    assert [f.rule_id for f in report.findings] == ["extrace.test.first"]


# --------------------------------------------------------------------------
# ES-4 combine seam — the Semgrep pass is faked (no wheel / container needed).
# --------------------------------------------------------------------------


def _fake_semgrep_result(
    findings: list[StaticDetectionFinding] | None = None,
    *,
    status: Literal["ok", "partial", "error", "timeout"] = "ok",
) -> SemgrepRunResult:
    findings = findings or []
    return SemgrepRunResult(
        findings=findings,
        record=StaticToolExecutionRecord(
            tool="semgrep",
            version="1.164.0",
            rules_loaded=4,
            findings_emitted=len(findings),
            duration_ms=1,
            status=status,
        ),
    )


def _semgrep_finding() -> StaticDetectionFinding:
    return StaticDetectionFinding(
        rule_id="extrace.sg.eval",
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["attack.T1059", "extrace.ext.dynamic_code_exec"],
        severity=Severity.MEDIUM,
        confidence=Confidence.MEDIUM,
        title="t",
        description="d",
    )


def test_runner_combines_inhouse_and_semgrep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "extension.js"}),
        encoding="utf-8",
    )
    (tmp_path / "extension.js").write_text("module.exports = {};", encoding="utf-8")
    monkeypatch.setattr(
        static_runner,
        "run_semgrep",
        lambda **_kw: _fake_semgrep_result([_semgrep_finding()]),
    )
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    # Inhouse-first ordering keeps tool_executions[0] == inhouse.
    assert [r.tool for r in report.tool_executions] == ["inhouse", "semgrep"]
    assert any(f.rule_id == "extrace.sg.eval" for f in report.findings)
    # The rollup sums findings across both tools.
    assert sum(report.severity_counts.model_dump().values()) == len(report.findings)
    assert report.partial is False


def test_runner_partial_when_semgrep_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        static_runner,
        "run_semgrep",
        lambda **_kw: _fake_semgrep_result(status="timeout"),
    )
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path), rules_version="1.0.0", timeout_budget_s=30
    )
    assert report.partial is True
    assert report.tool_executions[1].tool == "semgrep"
    assert report.tool_executions[1].status == "timeout"
