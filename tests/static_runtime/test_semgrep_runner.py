"""Container-free unit tests for the Semgrep runner + mapper (ES-4, ADR 0016).

Mocks ``subprocess.run`` and feeds canned Semgrep ``--json`` output, so no real
Semgrep wheel or container is needed (the live-fire path is the container smoke
test). Locks the JSON -> ``StaticDetectionFinding`` mapping, the exit-code
taxonomy, and the redact+clamp evidence path.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from packages.analysis_contracts.detection.enums import Confidence, Severity
from static_runtime import semgrep_runner

_VSIX = "/abs/vsix"


def _result(
    check_id: str,
    *,
    path: str | None = None,
    line: int = 5,
    lines: str = "eval(x)",
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "path": path or f"{_VSIX}/extension/out/ext.js",
        "start": {"line": line, "col": 1},
        "end": {"line": line, "col": 20},
        "extra": {"lines": lines, "message": "m", "severity": "WARNING"},
    }


def _fake_semgrep(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returncode: int = 1,
    results: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    raise_timeout: bool = False,
    stdout: str | None = None,
) -> None:
    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if raise_timeout:
            raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout"))
        body = stdout
        if body is None:
            body = json.dumps({"results": results or [], "errors": errors or []})
        return subprocess.CompletedProcess(
            args=argv, returncode=returncode, stdout=body, stderr=""
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)


def _run(monkeypatch: pytest.MonkeyPatch, **kw: Any) -> semgrep_runner.SemgrepRunResult:
    _fake_semgrep(monkeypatch, **kw)
    return semgrep_runner.run_semgrep(vsix_dir=_VSIX, wall_timeout_s=20)


def test_semgrep_argv_pins_memory_below_container_ceiling() -> None:
    argv = semgrep_runner._build_argv(
        targets=("/target.js",),
        per_rule_timeout_s=5,
        exclude_inventory_only=False,
    )

    assert argv[argv.index("--max-memory") + 1] == "1536"


@pytest.mark.parametrize(
    ("bare_id", "expected_rule_id"),
    [
        ("eval", "extrace.sg.eval"),
        ("function_constructor", "extrace.sg.function_constructor"),
        ("child_process", "extrace.sg.child_process"),
        ("vm_runincontext", "extrace.sg.vm_runincontext"),
        ("outbound_net_module", "extrace.sg.outbound_net_module"),
        ("dynamic_require", "extrace.sg.dynamic_require"),
        ("base64_decode_exec", "extrace.sg.base64_decode_exec"),
        ("sensitive_file_read", "extrace.sg.sensitive_file_read"),
    ],
)
def test_each_rule_maps_to_its_contract_finding(
    monkeypatch: pytest.MonkeyPatch, bare_id: str, expected_rule_id: str
) -> None:
    check_id = f"semgrep_rules.extrace-vsix-js.{bare_id}"
    res = _run(monkeypatch, returncode=1, results=[_result(check_id)])
    assert len(res.findings) == 1
    finding = res.findings[0]
    assert finding.rule_id == expected_rule_id
    assert finding.severity is Severity.MEDIUM
    assert finding.confidence is Confidence.MEDIUM
    evidence = finding.evidence[0]
    assert evidence.tool == "semgrep"
    assert evidence.type == "source_file"
    assert evidence.line_number == 5
    assert evidence.rule_match_id == check_id
    assert res.record.tool == "semgrep"
    assert res.record.findings_emitted == 1
    assert res.record.status == "ok"


def test_path_made_relative_to_vsix_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(
        monkeypatch,
        results=[_result("x.eval", path=f"{_VSIX}/extension/out/ext.js")],
    )
    assert res.findings[0].evidence[0].relative_path == "extension/out/ext.js"


def test_path_outside_root_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, results=[_result("x.eval", path="/somewhere/else/ext.js")])
    assert res.findings == []


def test_unknown_check_id_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, results=[_result("semgrep_rules.other.not_ours")])
    assert res.findings == []


def test_snippet_is_redacted_and_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    secret_line = "const k = 'AKIAIOSFODNN7EXAMPLE'; " + "x" * 1000
    res = _run(monkeypatch, results=[_result("x.eval", lines=secret_line)])
    snippet = res.findings[0].evidence[0].snippet
    assert snippet is not None
    assert "AKIA" not in snippet
    assert "[REDACTED:aws]" in snippet
    assert len(snippet) <= 400


def test_rc0_no_findings_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, returncode=0, results=[])
    assert res.findings == []
    assert res.record.status == "ok"
    assert res.record.findings_emitted == 0


def test_inventory_only_exclusion_does_not_mark_tool_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory_only_paths = (
        "node_modules/pkg/index.js",
        "vendor/client.ts",
        "vendors/client.cjs",
        "dist/client.min.mjs",
    )
    for relative_path in inventory_only_paths:
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("eval(payload)", encoding="utf-8")
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=json.dumps({"results": [], "errors": []}),
            stderr="",
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)

    result = semgrep_runner.run_semgrep(vsix_dir=str(tmp_path), wall_timeout_s=20)

    assert result.record.status == "ok"
    assert result.record.coverage.files_skipped_by_reason == {
        "excluded_inventory_only": len(inventory_only_paths)
    }
    assert result.record.coverage.coverage_reasons == []
    excluded_patterns = {
        calls[0][index + 1]
        for index, value in enumerate(calls[0][:-1])
        if value == "--exclude"
    }
    assert {"node_modules", "vendor", "vendors", "*.min.mjs"} <= excluded_patterns


def test_selected_dependency_gets_bounded_second_pass_and_dedupes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vendor = tmp_path / "node_modules" / "vendor"
    vendor.mkdir(parents=True)
    selected = vendor / "index.js"
    selected.write_text("eval(payload)", encoding="utf-8")
    first_party = tmp_path / "extension.js"
    first_party.write_text("eval(payload)", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        path = str(selected) if "--exclude" not in argv else str(first_party)
        payload = {"results": [_result("x.eval", path=path)], "errors": []}
        return subprocess.CompletedProcess(
            args=argv,
            returncode=1,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    result = semgrep_runner.run_semgrep(
        vsix_dir=str(tmp_path),
        wall_timeout_s=20,
        deep_scan_targets=(str(selected),),
    )

    assert len(calls) == 2
    exclude_index = calls[0].index("--exclude")
    assert calls[0][exclude_index : exclude_index + 2] == [
        "--exclude",
        "node_modules",
    ]
    assert "--exclude" not in calls[1]
    assert calls[1][-1] == str(selected)
    assert {finding.evidence[0].relative_path for finding in result.findings} == {
        "extension.js",
        "node_modules/vendor/index.js",
    }
    assert result.record.coverage.files_skipped_by_reason == {}
    assert result.record.coverage.files_scanned == 2


def test_duplicate_result_across_semgrep_passes_is_emitted_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "bundle.min.js"
    selected.write_text("eval(payload)", encoding="utf-8")

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        payload = {"results": [_result("x.eval", path=str(selected))], "errors": []}
        return subprocess.CompletedProcess(
            args=argv,
            returncode=1,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    result = semgrep_runner.run_semgrep(
        vsix_dir=str(tmp_path),
        wall_timeout_s=20,
        deep_scan_targets=(str(selected),),
    )
    assert len(result.findings) == 1


def test_same_match_shape_on_distinct_lines_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        monkeypatch,
        results=[
            _result("x.eval", line=5, lines="eval(payload)"),
            _result("x.eval", line=9, lines="eval(payload)"),
        ],
    )

    assert [finding.evidence[0].line_number for finding in result.findings] == [5, 9]


def test_deep_target_cap_marks_semgrep_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")
    _fake_semgrep(monkeypatch, returncode=0, results=[])

    result = semgrep_runner.run_semgrep(
        vsix_dir=str(tmp_path),
        wall_timeout_s=20,
        deep_scan_target_cap_reached=True,
    )

    assert result.record.status == "partial"
    assert "deep_scan_target_cap" in result.record.coverage.coverage_reasons


def test_second_pass_timeout_is_partial_and_accounts_for_selected_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "node_modules/vendor/index.js"
    selected.parent.mkdir(parents=True)
    selected.write_text("eval(payload)", encoding="utf-8")
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")
    calls = 0

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout"))
        return subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=json.dumps({"results": [], "errors": []}),
            stderr="",
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    result = semgrep_runner.run_semgrep(
        vsix_dir=str(tmp_path),
        wall_timeout_s=20,
        deep_scan_targets=(str(selected),),
    )

    assert calls == 2
    assert result.record.status == "partial"
    assert result.record.coverage.coverage_reasons == ["tool_timeout"]
    assert result.record.coverage.files_skipped_by_reason == {"tool_timeout": 1}
    assert result.record.coverage.skipped_paths_by_reason == {
        "tool_timeout": ["node_modules/vendor/index.js"]
    }


def test_second_pass_tool_error_is_partial_and_accounts_for_selected_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "vendor/client.ts"
    selected.parent.mkdir(parents=True)
    selected.write_text("eval(payload)", encoding="utf-8")
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")
    calls = 0

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(
            args=argv,
            returncode=2 if calls == 2 else 0,
            stdout=json.dumps({"results": [], "errors": []}),
            stderr="",
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    result = semgrep_runner.run_semgrep(
        vsix_dir=str(tmp_path),
        wall_timeout_s=20,
        deep_scan_targets=(str(selected),),
    )

    assert calls == 2
    assert result.record.status == "partial"
    assert result.record.coverage.coverage_reasons == ["tool_error"]
    assert result.record.coverage.files_skipped_by_reason == {"tool_error": 1}
    assert result.record.coverage.skipped_paths_by_reason == {
        "tool_error": ["vendor/client.ts"]
    }


def test_first_pass_priority_turns_unspent_deep_target_into_budget_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "node_modules/vendor/index.js"
    selected.parent.mkdir(parents=True)
    selected.write_text("eval(payload)", encoding="utf-8")
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")
    calls = 0

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=json.dumps({"results": [], "errors": []}),
            stderr="",
        )

    monotonic_values = iter((0.0, 16.0, 17.0))
    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        semgrep_runner.time, "monotonic", lambda: next(monotonic_values)
    )
    result = semgrep_runner.run_semgrep(
        vsix_dir=str(tmp_path),
        wall_timeout_s=20,
        deep_scan_targets=(str(selected),),
    )

    assert calls == 1
    assert result.record.status == "partial"
    assert result.record.coverage.coverage_reasons == ["budget_stop"]
    assert result.record.coverage.files_skipped_by_reason == {"budget_stop": 1}


def test_rc2_is_tool_error(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, returncode=2, results=[])
    assert res.findings == []
    assert res.record.status == "error"
    assert res.record.coverage.coverage_reasons == ["tool_error"]


def test_timeout_yields_timeout_record(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, raise_timeout=True)
    assert res.findings == []
    assert res.record.status == "timeout"
    assert res.record.coverage.coverage_reasons == ["tool_timeout"]


def test_unparseable_stdout_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, returncode=0, stdout="not json at all")
    assert res.findings == []
    assert res.record.status == "error"


def test_errors_array_marks_partial_and_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors = [
        {"rule_id": "semgrep_rules.extrace-vsix-js.eval", "message": "parse error"},
        {"message": "unattributed error"},
    ]
    res = _run(monkeypatch, returncode=1, results=[_result("x.eval")], errors=errors)
    assert res.record.status == "partial"
    assert res.record.error_count == 2
    assert "extrace.sg.eval" in res.record.errored_rule_ids
    assert "parser_error" in res.record.coverage.coverage_reasons
    # Findings are still mapped despite the per-file errors (degrade, not fail).
    assert len(res.findings) == 1


def test_findings_are_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    many = [
        _result("x.eval", line=i + 1, lines=f"eval(value_{i})")
        for i in range(semgrep_runner._MAX_FINDINGS + 50)
    ]
    res = _run(monkeypatch, results=many)
    assert len(res.findings) == semgrep_runner._MAX_FINDINGS
    assert res.record.coverage.finding_cap_reached is True
    assert "finding_cap" in res.record.coverage.coverage_reasons


def test_missing_semgrep_binary_degrades_to_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    res = semgrep_runner.run_semgrep(vsix_dir=_VSIX, wall_timeout_s=20)
    assert res.findings == []
    assert res.record.status == "error"


def test_non_object_payload_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Well-formed JSON that is not an object (e.g. a bare list) is malformed
    # Semgrep output -> degraded error record, never raised out of the pass.
    res = _run(monkeypatch, returncode=0, stdout='["not", "an", "object"]')
    assert res.findings == []
    assert res.record.status == "error"


def test_non_list_results_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # An object whose `results` is not a list is malformed -> degraded error.
    res = _run(
        monkeypatch, returncode=0, stdout=json.dumps({"results": "nope", "errors": []})
    )
    assert res.findings == []
    assert res.record.status == "error"


def test_relative_path_with_parent_traversal_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Defense-in-depth pre-filter: a result path with a `..` segment is skipped
    # (never reaching the contract validator), so an extension-controlled path
    # cannot point evidence outside the scanned tree.
    res = _run(monkeypatch, results=[_result("x.eval", path="extension/../escape.js")])
    assert res.findings == []
