"""ES-2 smoke acceptance: static-analyzer container bring-up + stub run.

``@pytest.mark.smoke`` — runs under ``make test-smoke`` (``-m smoke``); skipped
by the default lane / ``make check-all`` (``-m "not smoke"``). Requires the
``static_analyzer`` container running (``make static-up``); skips cleanly
otherwise (pattern from ``tests/architecture/test_container_entrypoint.py``).
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from executor.config import settings

pytestmark = [pytest.mark.smoke, pytest.mark.integration]

_CONTAINER = settings.static_analyzer.CONTAINER_NAME


def _docker_or_skip() -> str:
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        pytest.skip("docker unavailable; static smoke acceptance skipped")
    result = subprocess.run(  # noqa: S603
        [docker_bin, "inspect", "-f", "{{.State.Running}}", _CONTAINER],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        pytest.skip(f"{_CONTAINER} not running; run `make static-up` first")
    return docker_bin


def test_static_runtime_imports_in_container() -> None:
    """``import static_runtime`` succeeds inside the minimal hardened image."""
    docker_bin = _docker_or_skip()
    result = subprocess.run(  # noqa: S603
        [docker_bin, "exec", _CONTAINER, "python3", "-c", "import static_runtime"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"static_runtime import failed in container (rc={result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def _exec(docker_bin: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [docker_bin, "exec", _CONTAINER, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_static_runner_emits_inhouse_record_for_clean_tree() -> None:
    """The ES-3a runner writes a valid report (no findings, inhouse tool record).

    Runs over an empty container-side dir so the result is deterministic
    regardless of what is mounted at ``/extensions-input``.
    """
    docker_bin = _docker_or_skip()
    empty_dir = "/tmp/es3a_empty"  # noqa: S108 — container-side tmp
    report_path = "/tmp/es3a_clean_report.json"  # noqa: S108
    assert _exec(docker_bin, "mkdir", "-p", empty_dir).returncode == 0

    run = _exec(
        docker_bin,
        "python3",
        "-m",
        "static_runtime",
        "--vsix-dir",
        empty_dir,
        "--report-path",
        report_path,
        "--rules-version",
        "0.0.0",
        "--timeout-budget-s",
        "30",
    )
    assert run.returncode == 0, f"runner failed:\nstderr: {run.stderr}"

    cat = _exec(docker_bin, "cat", report_path)
    assert cat.returncode == 0, f"could not read report:\nstderr: {cat.stderr}"
    doc = json.loads(cat.stdout)
    assert doc["schema_version"] == "2"
    assert doc["findings"] == []
    # ES-4: inhouse first, then semgrep. Over an empty (no-JS) tree semgrep runs
    # offline and reports a clean record (status ok, no findings) — live proof the
    # wheel is installed and runs under network_mode: none, not an error.
    tool_records = {record["tool"]: record for record in doc["tool_executions"]}
    assert doc["tool_executions"][0]["tool"] == "inhouse"
    # Production in-house static rule count (s1-s18, incl. multi-rule modules).
    # Bump in lockstep with EXPECTED_STATIC_PRODUCTION_RULE_IDS / test_static_runner.
    assert tool_records["inhouse"]["rules_loaded"] == 22
    assert "semgrep" in tool_records
    assert tool_records["semgrep"]["status"] == "ok"
    assert tool_records["semgrep"]["findings_emitted"] == 0


def test_static_runner_fires_rules_in_container() -> None:
    """Live evidence the in-house rules actually fire inside the hardened image."""
    docker_bin = _docker_or_skip()
    mal_dir = "/tmp/es3a_mal"  # noqa: S108 — container-side tmp
    report_path = "/tmp/es3a_mal_report.json"  # noqa: S108
    # Stage a red-flag manifest using the container's own python (avoids shell
    # quoting); writes {publisher:"", activationEvents:["*"]} into mal_dir.
    stage = _exec(
        docker_bin,
        "python3",
        "-c",
        (
            "import json,pathlib;"
            f"p=pathlib.Path({mal_dir!r});p.mkdir(parents=True,exist_ok=True);"
            "(p/'package.json').write_text("
            "json.dumps({'publisher':'','name':'thing','activationEvents':['*']}))"
        ),
    )
    assert stage.returncode == 0, f"could not stage manifest:\nstderr: {stage.stderr}"

    run = _exec(
        docker_bin,
        "python3",
        "-m",
        "static_runtime",
        "--vsix-dir",
        mal_dir,
        "--report-path",
        report_path,
        "--rules-version",
        "1.0.0",
        "--timeout-budget-s",
        "30",
    )
    assert run.returncode == 0, f"runner failed:\nstderr: {run.stderr}"

    cat = _exec(docker_bin, "cat", report_path)
    assert cat.returncode == 0, f"could not read report:\nstderr: {cat.stderr}"
    doc = json.loads(cat.stdout)
    rule_ids = {finding["rule_id"] for finding in doc["findings"]}
    assert any(rule_id.startswith("extrace.s1.") for rule_id in rule_ids), (
        f"expected S1 manifest red-flag findings, got: {sorted(rule_ids)}"
    )


def test_semgrep_fires_on_malicious_js_in_container() -> None:
    """Live evidence the Semgrep JS rules fire inside the hardened image (ES-4).

    Stages a JS file exercising ``eval`` + ``child_process`` and asserts both
    ``extrace.sg.*`` rules fire — proof the real wheel + custom YAML rules run
    offline in the ``network_mode: none`` container.
    """
    docker_bin = _docker_or_skip()
    js_dir = "/tmp/es4_js"  # noqa: S108 — container-side tmp
    report_path = "/tmp/es4_js_report.json"  # noqa: S108
    # Stage manifest + a JS payload using the container's own python (no shell
    # quoting): writes extension/out/ext.js with eval(...) and child_process.
    stage = _exec(
        docker_bin,
        "python3",
        "-c",
        (
            "import json,pathlib;"
            f"p=pathlib.Path({js_dir!r});"
            "(p/'extension'/'out').mkdir(parents=True,exist_ok=True);"
            "(p/'extension'/'package.json').write_text("
            "json.dumps({'name':'x','publisher':'p'}));"
            "(p/'extension'/'out'/'ext.js').write_text("
            "'eval(userInput);\\nrequire(\"child_process\").exec(cmd);\\n')"
        ),
    )
    assert stage.returncode == 0, f"could not stage JS:\nstderr: {stage.stderr}"

    run = _exec(
        docker_bin,
        "python3",
        "-m",
        "static_runtime",
        "--vsix-dir",
        js_dir,
        "--report-path",
        report_path,
        "--rules-version",
        "1.0.0",
        "--timeout-budget-s",
        "30",
    )
    assert run.returncode == 0, f"runner failed:\nstderr: {run.stderr}"

    cat = _exec(docker_bin, "cat", report_path)
    assert cat.returncode == 0, f"could not read report:\nstderr: {cat.stderr}"
    doc = json.loads(cat.stdout)
    rule_ids = {finding["rule_id"] for finding in doc["findings"]}
    assert "extrace.sg.eval" in rule_ids, (
        f"expected extrace.sg.eval to fire, got: {sorted(rule_ids)}"
    )
    assert "extrace.sg.child_process" in rule_ids, (
        f"expected extrace.sg.child_process to fire, got: {sorted(rule_ids)}"
    )
    tool_records = {record["tool"]: record for record in doc["tool_executions"]}
    assert tool_records["semgrep"]["findings_emitted"] >= 2
