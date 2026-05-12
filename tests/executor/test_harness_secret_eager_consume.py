"""W13-11 behavioral regression: host-side eager-consume + env var threading.

Codex F1 close-pass for W13-1 H6. Pre-W13-11 the HMAC python secret at
``/results/_extrace_harness_python_secret`` (0600 executor:executor) was
consumed inside the container by ``setup_monitor`` only AFTER
``install_extension`` admitted the target VSIX. A same-UID target could read
the file during that window and forge HMAC-signed harness completion markers
that satisfied the W13-1 nonce check, re-opening the spoofing surface.

W13-11 closes this by reading + unlinking the secret on the host (between
``_reset_sandbox`` and ``_install_extension``) and threading it through
``run_playwright_automation`` as the ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE``
docker exec env var. By the time ``install_extension`` admits the target
VSIX, the file no longer exists.

These behavioral cases pin the consume helper and the env-var threading.
Pair with:

- ``tests/architecture/test_harness_secret_eager_consume.py`` (AST-level
  call sequence + env-var literal invariants).
- ``tests/executor/test_playwright_health_reconciliation.py`` (env-priority
  unit cases inside ``load_harness_python_secret``).
- ``tests/security/test_executor_host_error_redaction.py`` (E4 mitigation:
  env var value masked in ExecutorError exception messages).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


def test_eager_consume_returns_secret_and_unlinks_file(tmp_path: Path) -> None:
    """Happy path: 0600 file is read, returned, and unlinked atomically (best-effort)."""
    from executor import host as host_module

    secret_value = (
        "deadbeefcafe1234" * 4
    )  # 64 chars, mirrors launch_vscode.sh hex output.
    secret_path = tmp_path / "_extrace_harness_python_secret"
    secret_path.write_text(secret_value, encoding="utf-8")
    secret_path.chmod(0o600)

    result = host_module.consume_harness_python_secret_eager(host_path=secret_path)

    assert result == secret_value, (
        "eager-consume must return the exact secret string written by "
        "launch_vscode.sh; the value flows into EXECUTOR_HARNESS_PYTHON_SECRET_VALUE "
        "and ultimately becomes the HMAC key for harness completion markers."
    )
    assert not secret_path.exists(), (
        "eager-consume must unlink the file after reading so the target VSIX "
        "cannot read it during the subsequent install_extension window. "
        "This is the core W13-11 invariant — read-and-unlink atomically on "
        "the host before admit."
    )


def test_target_read_attempt_after_consume_raises_filenotfound(
    tmp_path: Path,
) -> None:
    """Race window closed: post-consume, any subsequent read on the bind-mounted path raises FileNotFoundError."""
    from executor import host as host_module

    secret_path = tmp_path / "_extrace_harness_python_secret"
    secret_path.write_text("secret-to-be-consumed", encoding="utf-8")
    secret_path.chmod(0o600)

    host_module.consume_harness_python_secret_eager(host_path=secret_path)

    with pytest.raises(FileNotFoundError):
        # This simulates the target VSIX (or any same-UID reader) attempting
        # to read the secret after install_extension admits it. Pre-W13-11
        # the file would still be present and readable; W13-11 ensures it
        # is gone before the target gets a chance.
        secret_path.read_text(encoding="utf-8")


def test_consume_returns_none_on_missing_file(tmp_path: Path) -> None:
    """Fresh boot / file never written: consume returns ``None``; downstream env var stays unset."""
    from executor import host as host_module

    # No secret file pre-written; tmp_path is empty.
    secret_path = tmp_path / "_extrace_harness_python_secret"

    result = host_module.consume_harness_python_secret_eager(host_path=secret_path)

    assert result is None, (
        "eager-consume must return None when the secret file is absent "
        "(launch_vscode.sh has not run yet, or a prior consume already "
        "reaped it). The caller in execute_analysis_request will then "
        "pass harness_python_secret=None to run_playwright_automation, "
        "and the env var is omitted so reconciliation falls back to its "
        "legacy file path (which is also absent → empty secret → W13-12 "
        "fail-closed enforcement). Worst case is pre-W13-11 status quo."
    )


def test_consume_rejects_wrong_mode_and_unlinks_anyway(tmp_path: Path) -> None:
    """Defense-in-depth: a file with mode != 0600 is rejected (returns None) AND best-effort unlinked.

    ``launch_vscode.sh:51`` writes the secret at chmod 0600. Anything else is
    suspicious — the file may have been touched by an unexpected actor.
    W13-11 declines to read it but still removes it so the malformed file
    cannot linger into the next launch cycle.
    """
    from executor import host as host_module

    secret_path = tmp_path / "_extrace_harness_python_secret"
    secret_path.write_text("would-be-secret-with-wrong-perms", encoding="utf-8")
    secret_path.chmod(0o644)  # wrong: launch_vscode.sh writes 0o600.

    result = host_module.consume_harness_python_secret_eager(host_path=secret_path)

    assert result is None, (
        "eager-consume must reject a file with mode 0o644 — only 0o600 is "
        "accepted (matches launch_vscode.sh's chmod). A looser mode means "
        "the file may already be readable by the target user via a "
        "different attack path."
    )
    assert not secret_path.exists(), (
        "eager-consume must best-effort unlink even on mode reject so the "
        "malformed file does not linger into the next reset cycle."
    )


def test_run_playwright_automation_threads_secret_to_docker_exec_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: ``run_playwright_automation(..., harness_python_secret=X)`` adds ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=X`` to the docker exec env."""
    from executor import host as host_module

    captured: dict[str, object] = {}
    report_host_path = tmp_path / "r.json"

    def fake_docker_exec_allow_partial(
        cmd: list[str], timeout: int | None = None, **kwargs: object
    ) -> SimpleNamespace:
        captured["cmd"] = cmd
        captured["timeout"] = timeout
        captured["extra_env"] = kwargs.get("extra_env")
        # Simulate a successful run that produced the requested report so
        # the ``report_host_path.exists()`` guard inside
        # run_playwright_automation passes without raising.
        report_host_path.write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    # ``settings.project`` is a frozen dataclass; route the host-side path
    # resolution through a mocked ``_docker_exec_target_path`` instead.
    monkeypatch.setattr(
        host_module,
        "_docker_exec_target_path",
        lambda _container_path: report_host_path,
    )
    monkeypatch.setattr(
        host_module, "_docker_exec_allow_partial", fake_docker_exec_allow_partial
    )
    # cleanup_trigger_file is invoked in finally; with trigger_container_path
    # set to None it returns immediately, so no extra mocking needed.

    secret_value = "abcdef0123456789" * 4  # 64 chars hex.
    host_module.run_playwright_automation(
        report_path="/results/r.json",
        harness_python_secret=secret_value,
    )

    extra_env = captured.get("extra_env")
    assert isinstance(extra_env, dict), (
        "run_playwright_automation must call _docker_exec_allow_partial "
        "with the new ``extra_env`` kw-arg so the secret can be injected "
        "as a docker exec ``-e KEY=VALUE`` env var. A None default keeps "
        "the rest of the call sites backwards-compatible."
    )
    assert extra_env.get("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE") == secret_value, (
        "The threaded secret must reach the entrypoint container under "
        "the exact env var name EXECUTOR_HARNESS_PYTHON_SECRET_VALUE — "
        "this is the contract reconciliation.load_harness_python_secret() "
        "reads on the container side. Any drift breaks the close-pass."
    )


def test_run_playwright_automation_success_path_does_not_leak_secret_in_returned_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W13-11 (c) defense-in-depth — happy-path stream no-leak invariant.

    The existing redaction test
    (``tests/security/test_executor_host_error_redaction.py::
    test_run_playwright_automation_redacts_harness_secret_env_var_in_error_message``)
    covers the exception path only — it asserts that on ``TimeoutExpired``
    the masking helper rewrites ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>``
    in the resulting ``ExecutorError`` message.

    This case pins the complementary success-path invariant: when
    ``_docker_exec_allow_partial`` returns rc=0 with arbitrary captured
    stdout / stderr, ``run_playwright_automation`` MUST return the
    subprocess stdout unchanged — it must not inject the threaded secret
    value (or the full docker exec argv) into its return value. A future
    regression that, say, logs ``full_cmd`` and concatenates it with
    ``result.stdout`` would surface here.
    """
    from executor import host as host_module

    secret_value = "feedface0badc0de" * 4  # 64 chars hex, mirrors launch_vscode.sh.
    report_host_path = tmp_path / "r.json"

    benign_stdout = "automation completed; 3 scenarios executed; 0 failures"
    benign_stderr = "[playwright] launched chromium; closed cleanly"

    def fake_docker_exec_allow_partial(
        cmd: list[str], timeout: int | None = None, **kwargs: object
    ) -> SimpleNamespace:
        # Sanity guard: the helper must receive the secret env via
        # extra_env (the threading invariant covered by the e2e test above).
        # If this is wrong the no-leak assertion below is meaningless.
        extra_env = kwargs.get("extra_env")
        assert isinstance(extra_env, dict)
        assert extra_env.get("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE") == secret_value
        # Simulate a clean run: report present, rc=0, benign streams.
        report_host_path.write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout=benign_stdout, stderr=benign_stderr)

    monkeypatch.setattr(
        host_module,
        "_docker_exec_target_path",
        lambda _container_path: report_host_path,
    )
    monkeypatch.setattr(
        host_module, "_docker_exec_allow_partial", fake_docker_exec_allow_partial
    )

    returned_stdout = host_module.run_playwright_automation(
        report_path="/results/r.json",
        harness_python_secret=secret_value,
    )

    assert returned_stdout == benign_stdout, (
        "W13-11 (c): run_playwright_automation must return the "
        "subprocess result.stdout unchanged on the success path. "
        "Production currently does this (``return result.stdout`` at "
        "executor/host.py:464). If a future regression splices "
        "``full_cmd`` or other env-bearing argv into the return value, "
        "this assertion catches it before the value lands on "
        "operator-visible job.automation_output."
    )
    assert secret_value not in returned_stdout, (
        "W13-11 (c) defense-in-depth: returned stdout must not contain "
        "the threaded EXECUTOR_HARNESS_PYTHON_SECRET_VALUE hex. The "
        "value reaches subprocess via docker exec ``-e`` and the "
        "container is responsible for not echoing it; this test pins "
        "that the host wrapper does not re-introduce the leak surface "
        "by accidentally concatenating argv or env into the return path."
    )
