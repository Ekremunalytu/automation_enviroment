"""Container-free unit tests for the Semgrep runner + mapper (ES-4, ADR 0016).

Mocks ``subprocess.run`` and feeds canned Semgrep ``--json`` output, so no real
Semgrep wheel or container is needed (the live-fire path is the container smoke
test). Locks the JSON -> ``StaticDetectionFinding`` mapping, the exit-code
taxonomy, and the redact+clamp evidence path.
"""

from __future__ import annotations

import json
import subprocess
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


@pytest.mark.parametrize(
    ("bare_id", "expected_rule_id"),
    [
        ("eval", "extrace.sg.eval"),
        ("function_constructor", "extrace.sg.function_constructor"),
        ("child_process", "extrace.sg.child_process"),
        ("vm_runincontext", "extrace.sg.vm_runincontext"),
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


def test_rc2_is_tool_error(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, returncode=2, results=[])
    assert res.findings == []
    assert res.record.status == "error"


def test_timeout_yields_timeout_record(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _run(monkeypatch, raise_timeout=True)
    assert res.findings == []
    assert res.record.status == "timeout"


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
    # Findings are still mapped despite the per-file errors (degrade, not fail).
    assert len(res.findings) == 1


def test_findings_are_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    many = [
        _result("x.eval", line=i + 1) for i in range(semgrep_runner._MAX_FINDINGS + 50)
    ]
    res = _run(monkeypatch, results=many)
    assert len(res.findings) == semgrep_runner._MAX_FINDINGS


def test_missing_semgrep_binary_degrades_to_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    res = semgrep_runner.run_semgrep(vsix_dir=_VSIX, wall_timeout_s=20)
    assert res.findings == []
    assert res.record.status == "error"
