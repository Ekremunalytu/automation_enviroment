"""ES-2 executor: static-analyzer host orchestration + control facade.

Exercises ``executor/static_host.py`` + ``executor/static_control.py`` WITHOUT a
live container: ``subprocess.run`` is monkeypatched so the docker-exec argv,
timeout, and no-shell properties can be asserted (pattern from
``tests/executor/security/test_uri_trigger_injection.py``). Also pins the
``static_runtime`` argparse required-flag contract.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

from executor import binary_paths, static_host
from executor.binary_paths import STATIC_ANALYZER_PYTHON3_PATH
from executor.config import settings
from executor.static_control import StaticAnalyzerError, default_static_analyzer_control


@pytest.fixture
def fake_docker(monkeypatch: pytest.MonkeyPatch) -> str:
    """Pin ``docker_path()`` to a deterministic absolute value for argv asserts."""
    fake = "/fake/abs/docker"
    binary_paths._reset_docker_path_cache()
    monkeypatch.setattr(binary_paths.shutil, "which", lambda _name: fake)
    return fake


def test_run_static_analysis_builds_expected_docker_exec_argv(
    fake_docker: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout="ok", stderr=""
        )

    monkeypatch.setattr(static_host.subprocess, "run", fake_run)

    out = default_static_analyzer_control.run_static_analysis(
        vsix_dir="/extensions-input/x",
        report_path="/results/r.json",
        rules_version="1.2.3",
        timeout_budget_s=30,
    )

    assert out == "ok"
    argv = captured["argv"]
    # Host docker CLI is the absolute cached docker_path().
    assert argv[0] == fake_docker
    assert argv[0].startswith("/")
    assert argv[1:5] == [
        "exec",
        "-e",
        "PYTHONUNBUFFERED=1",
        settings.static_analyzer.CONTAINER_NAME,
    ]
    # Container command starts with the absolute python + the runtime module.
    assert argv[5] == STATIC_ANALYZER_PYTHON3_PATH
    assert argv[5].startswith("/")
    assert argv[6:8] == ["-m", settings.static_analyzer.ENTRYPOINT_MODULE]
    # The four-flag invocation contract is threaded through verbatim.
    for flag, value in (
        ("--vsix-dir", "/extensions-input/x"),
        ("--report-path", "/results/r.json"),
        ("--rules-version", "1.2.3"),
        ("--timeout-budget-s", "30"),
    ):
        assert flag in argv, f"missing flag {flag}"
        assert argv[argv.index(flag) + 1] == value
    # Never shell=True (argv-list invocation only).
    assert captured["kwargs"].get("shell", False) is False
    assert captured["kwargs"].get("timeout") is not None


def test_run_static_analysis_nonzero_returncode_raises(
    fake_docker: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=argv, returncode=2, stdout="", stderr="boom"
        )

    monkeypatch.setattr(static_host.subprocess, "run", fail_run)

    with pytest.raises(StaticAnalyzerError) as exc:
        default_static_analyzer_control.run_static_analysis(
            vsix_dir="/x",
            report_path="/r.json",
            rules_version="1",
            timeout_budget_s=5,
        )
    assert exc.value.returncode == 2


def test_run_static_analysis_timeout_raises(
    fake_docker: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def timeout_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout"))

    monkeypatch.setattr(static_host.subprocess, "run", timeout_run)

    with pytest.raises(StaticAnalyzerError):
        default_static_analyzer_control.run_static_analysis(
            vsix_dir="/x",
            report_path="/r.json",
            rules_version="1",
            timeout_budget_s=5,
        )


def test_static_runtime_argparse_requires_all_flags() -> None:
    from static_runtime.entrypoint import build_parser

    args = build_parser().parse_args(
        [
            "--vsix-dir",
            "/x",
            "--report-path",
            "/r.json",
            "--rules-version",
            "1.0.0",
            "--timeout-budget-s",
            "30",
        ]
    )
    assert args.timeout_budget_s == 30
    # Missing required flags -> argparse SystemExit.
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_static_runtime_writes_valid_report_for_empty_tree(tmp_path: Any) -> None:
    """Container-free lock on the ES-3a runner's on-disk JSON contract.

    The live smoke variant (``tests/smoke/test_static_container_smoke.py``) is
    gated behind a running container and skipped under ``make check-all``; this
    runs in the default lane and pins the ``StaticDetectionReport`` shape the
    host orchestration (ES-3b) deserializes: an analysed-but-clean tree has no
    findings but DOES carry the ``inhouse`` tool-execution record (the ES-2 stub
    emitted no tool records — that is the behaviour change ES-3a introduces).
    """
    from packages.analysis_contracts.static_detection import StaticDetectionReport
    from static_runtime.entrypoint import run_static_detection

    report_path = tmp_path / "nested" / "report.json"  # parent created by runner
    returned = run_static_detection(
        vsix_dir=str(tmp_path),  # empty tree: no manifest, no files
        report_path=str(report_path),
        rules_version="0.0.0",
        timeout_budget_s=30,
    )

    assert isinstance(returned, StaticDetectionReport)
    assert report_path.is_file()
    doc = json.loads(report_path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == "2"
    assert doc["findings"] == []
    # ES-4: two tool records now — inhouse first, then semgrep. In this default
    # lane the Semgrep wheel is absent, so its record degrades to status="error";
    # the container smoke test exercises the real-Semgrep path. The inhouse-first
    # ordering and the clean inhouse record are what this lane pins.
    tools = [record["tool"] for record in doc["tool_executions"]]
    assert tools[0] == "inhouse"
    assert "semgrep" in tools
    assert doc["tool_executions"][0]["findings_emitted"] == 0
    # Round-trips back through the contract (validates, not just JSON-parses).
    StaticDetectionReport.model_validate(doc)


def test_static_runtime_main_writes_report_and_returns_zero(tmp_path: Any) -> None:
    """``main(argv)`` threads the argparse flags into a written report, rc 0."""
    from static_runtime.entrypoint import main

    report_path = tmp_path / "report.json"
    rc = main(
        [
            "--vsix-dir",
            "/extensions-input/x",
            "--report-path",
            str(report_path),
            "--rules-version",
            "0.0.0",
            "--timeout-budget-s",
            "30",
        ]
    )
    assert rc == 0
    assert report_path.is_file()


def test_static_analysis_feature_flag_defaults_on() -> None:
    """ES-5 close-out (ADR 0016 §Operational): the static pre-check stage is ON
    by default once smoke evidence passed at the stream close-out.

    The flag flipped from OFF to ON at ES-5 (``STATIC_ANALYSIS_ENABLED``); this
    pins the new default so an accidental revert to OFF — which would silently
    drop the pre-execution gate from the live pipeline — surfaces here.
    """
    assert settings.static_analysis.ENABLED is True


def test_cancel_static_analysis_builds_pkill_argv(
    fake_docker: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ES-3b cancel: argv is ``docker exec <container> pkill -f static_runtime``,
    argv[0] the absolute cached docker_path(), never shell=True."""
    captured: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(static_host.subprocess, "run", fake_run)
    static_host.cancel_static_analysis_in_container()

    argv = captured["argv"]
    assert argv[0] == fake_docker
    assert argv[0].startswith("/")
    assert argv[1:3] == ["exec", settings.static_analyzer.CONTAINER_NAME]
    assert argv[-3:] == ["pkill", "-f", "static_runtime"]
    assert captured["kwargs"].get("shell", False) is False


def test_cancel_static_analysis_is_best_effort_swallows_errors(
    fake_docker: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A subprocess failure (no matching process / pkill absent in the minimal
    image) must NOT raise — the off-thread coordinator's cancel is authoritative.
    """

    def boom_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.SubprocessError("pkill not found")

    monkeypatch.setattr(static_host.subprocess, "run", boom_run)
    static_host.cancel_static_analysis_in_container()  # must NOT raise


def test_control_cancel_delegates_to_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """``StaticAnalyzerControl.cancel()`` delegates to the host kill helper."""
    calls: list[int] = []
    monkeypatch.setattr(
        "executor.static_control._cancel_static_analysis_in_container",
        lambda: calls.append(1),
    )
    default_static_analyzer_control.cancel()
    assert calls == [1]
