"""Regression tests for ``executor.host`` exception-message redaction.

The retry-path branches in ``install_extension_in_executor`` and
``reload_vscode_window`` historically embedded raw subprocess output into
``ExecutorError`` messages. That message is the same string that reaches
``workflows/marketplace/analysis_service.py::_run_marketplace_analysis``
via ``str(exc)`` and lands on the persisted ``job.error_detail`` field
through ``appcore/storage/crud_ops/analysis_jobs/lifecycle.py``. A leak
along that path would expose any extension-controlled secrets that
showed up in the failed subprocess's stderr (PEM blocks, bearer tokens,
AKIA-style AWS keys, database URLs with credentials).

These tests pin the redaction behavior so the bypass cannot regress.
Mutation-verified during landing: removing the ``redact_secrets()`` wrap
in either site causes the corresponding test to fail.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from executor import host as host_module
from executor.host import ExecutorError


def test_install_extension_retry_redacts_bearer_in_first_attempt_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Bearer token in the first-attempt subprocess output must be redacted."""
    leaked_secret = "abc123def456ghi789xyz0123456789"  # noqa: S105 — test fixture
    first_attempt_output = (
        "VS Code extension install failed at lock\n"
        "ipc handle stale; singleton already running\n"
        f"Authorization: Bearer {leaked_secret}"
    )
    docker_calls: list[list[str]] = []

    def fake_docker_exec(cmd: list[str], timeout: int | None = None) -> Any:
        docker_calls.append(cmd)
        if len(docker_calls) == 1:
            raise ExecutorError(
                "Command failed (rc=1): code --install-extension",
                returncode=1,
                output=first_attempt_output,
            )
        raise ExecutorError(
            "Command failed (rc=1): code --install-extension",
            returncode=1,
            output="other clean failure on retry",
        )

    monkeypatch.setattr(host_module, "_docker_exec", fake_docker_exec)
    monkeypatch.setattr(host_module, "reload_vscode_window", lambda: "")
    monkeypatch.setattr(host_module.time, "sleep", lambda _s: None)

    with pytest.raises(ExecutorError) as info:
        host_module.install_extension_in_executor("publisher", "name", "1.0.0")

    message = str(info.value)
    assert "first attempt output:" in message  # carrier preserved
    assert "[REDACTED:bearer]" in message
    assert leaked_secret not in message


def test_install_extension_retry_redacts_aws_key_in_first_attempt_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An AWS access key in the first-attempt output must be redacted."""
    aws_key = "AKIAIOSFODNN7EXAMPLE"
    first_attempt_output = (
        "extension host crashed\n"
        f"env dump: AWS_ACCESS_KEY_ID={aws_key}; renderer process gone"
    )
    docker_calls: list[list[str]] = []

    def fake_docker_exec(cmd: list[str], timeout: int | None = None) -> Any:
        docker_calls.append(cmd)
        if len(docker_calls) == 1:
            raise ExecutorError(
                "Command failed", returncode=1, output=first_attempt_output
            )
        raise ExecutorError("Command failed again", returncode=1, output="benign")

    monkeypatch.setattr(host_module, "_docker_exec", fake_docker_exec)
    monkeypatch.setattr(host_module, "reload_vscode_window", lambda: "")
    monkeypatch.setattr(host_module.time, "sleep", lambda _s: None)

    with pytest.raises(ExecutorError) as info:
        host_module.install_extension_in_executor("publisher", "name", "1.0.0")

    message = str(info.value)
    assert "[REDACTED:aws]" in message
    assert aws_key not in message


def test_reload_error_message_redacts_secret_in_last_output_line() -> None:
    """``_reload_error_message`` redacts the appended last-output-line carrier."""
    raw_output = (
        "[reload] starting\nAuthorization: Bearer abc123def456ghi789xyz0123456789"
    )
    exc = ExecutorError(
        "Command failed (rc=1): reload_vscode",
        returncode=1,
        output=raw_output,
    )

    message = host_module._reload_error_message(exc)

    assert "last reload output:" in message
    assert "[REDACTED:bearer]" in message
    assert "abc123def456ghi789xyz" not in message


def test_reload_error_message_redacts_db_url_in_last_output_line() -> None:
    """A postgres URL with credentials in the reload-tail must be redacted."""
    raw_output = (
        "[reload] settle wait\n"
        "tried connecting to postgres://app:supersecret@db.internal:5432/db"
    )
    exc = ExecutorError(
        "Command failed (rc=1): reload_vscode",
        returncode=1,
        output=raw_output,
    )

    message = host_module._reload_error_message(exc)

    assert "[REDACTED:db_url]" in message
    assert "supersecret" not in message


def test_reload_vscode_window_propagates_redacted_message_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: ``reload_vscode_window`` raises ExecutorError with redacted str().

    PEM-block coverage is intentionally exercised through
    ``test_output_signals_redaction.py`` instead — repeating the real
    private-key marker literal here would trip the
    ``detect-private-key`` pre-commit hook. Bearer is a sufficient
    proxy for the carrier-redaction contract this test pins.
    """
    leaked = "abc123def456ghi789xyz0123456789"
    raw_output = (
        "[reload] crashed mid-run\n"
        f"env dump: Authorization: Bearer {leaked}; renderer process gone"
    )

    def fake_docker_exec(cmd: list[str], timeout: int | None = None) -> Any:
        raise ExecutorError(
            "Command failed (rc=1): reload_vscode",
            returncode=1,
            output=raw_output,
        )

    def fake_docker_exec_allow_partial(
        cmd: list[str], timeout: int | None = None
    ) -> Any:
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(host_module, "_docker_exec", fake_docker_exec)
    monkeypatch.setattr(
        host_module, "_docker_exec_allow_partial", fake_docker_exec_allow_partial
    )

    with pytest.raises(ExecutorError) as info:
        host_module.reload_vscode_window()

    message = str(info.value)
    assert "last reload output:" in message
    assert "[REDACTED:bearer]" in message
    assert leaked not in message


# ---------------------------------------------------------------------------
# W13-11 — env var value masking in docker exec exception messages
# ---------------------------------------------------------------------------
#
# E4 from the W13-11 design catalog: ``_run_docker_exec`` builds
# ``full_cmd = [docker_path(), "exec", "-e", "PYTHONUNBUFFERED=1", container, *cmd]``
# and embeds ``' '.join(cmd)`` into the ExecutorError message on rc != 0 or
# timeout. Once W13-11 lands the EXECUTOR_HARNESS_PYTHON_SECRET_VALUE env
# var, the 64-char raw hex would also appear in that argv when docker exec
# is invoked with ``-e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>``. The
# generic ``_REDACTION_PATTERNS`` (aws/bearer/private_key/api_key/db_url)
# do not catch pure hex — so a targeted masking helper inside
# ``_run_docker_exec`` (or the run_playwright_automation wrapper) must
# rewrite that segment to ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***`` before
# the message reaches str(exc) and persists onto job.error_detail.


def test_run_playwright_automation_redacts_harness_secret_env_var_in_error_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E4 mitigation: the harness secret env var value must be masked in ExecutorError.__str__.

    Drives ``run_playwright_automation`` end-to-end with a mocked
    ``subprocess.run`` that raises ``TimeoutExpired`` so the production
    ``_run_docker_exec`` exception path applies the masking helper to a
    real ``full_cmd`` containing the env arg. Mutation-verified during
    landing: removing the masking helper leaks the raw 64-char hex into
    ``str(exc)`` and fails this assertion.
    """
    import subprocess

    secret_hex = "deadbeefcafe0123" * 4  # 64 chars, mirrors launch_vscode.sh.

    def fake_subprocess_run(
        cmd: list[str], *_args: Any, timeout: int | None = None, **_kwargs: Any
    ) -> Any:
        # Sanity: production must have built the docker exec argv with the
        # harness env-var BEFORE we raise. The test relies on this for the
        # masking helper to have something to redact.
        assert any(
            f"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE={secret_hex}" == arg for arg in cmd
        ), (
            "production failed to thread harness_python_secret into the "
            "docker exec argv via the EXECUTOR_HARNESS_PYTHON_SECRET_VALUE "
            "env arg — pre-W13-11 contract."
        )
        raise subprocess.TimeoutExpired(cmd, timeout or 0)

    monkeypatch.setattr(host_module.subprocess, "run", fake_subprocess_run)
    # _cleanup_stale_entrypoint_processes also calls _docker_exec_allow_partial
    # (which would hit the mocked subprocess.run and raise again). No-op it.
    monkeypatch.setattr(
        host_module, "_cleanup_stale_entrypoint_processes", lambda: None
    )

    with pytest.raises(ExecutorError) as info:
        host_module.run_playwright_automation(
            report_path="/results/r.json",
            harness_python_secret=secret_hex,
        )

    message = str(info.value)
    assert secret_hex not in message, (
        "ExecutorError.__str__ leaked the harness secret hex into the "
        "operator-visible error message — the masking helper failed. "
        "This leak lands on the persisted job.error_detail surface and "
        "is the E4 attack vector W13-11 commits to closing alongside "
        "the eager-consume itself."
    )
    assert "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***" in message, (
        "the masking helper must rewrite the env arg to "
        "``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***`` so the operator "
        "can still see *which* env was passed (debug-ability) without "
        "seeing the value (security)."
    )


# ---------------------------------------------------------------------------
# W13-11 defense-in-depth (a) — E4 redaction completeness.
#
# The exception path inside ``_run_docker_exec`` has THREE distinct error
# sites that embed ``' '.join(full_cmd)`` into the resulting
# ``ExecutorError`` message:
#
#   1. ``subprocess.TimeoutExpired`` (executor/host.py:114-121)
#      — covered by the existing
#      ``test_run_playwright_automation_redacts_harness_secret_env_var_in_error_message``
#      above.
#   2. ``returncode != 0 and not allow_partial`` (executor/host.py:132-139)
#      — non-retryable rc-fail path, exercised when ``_docker_exec`` (not
#      ``_docker_exec_allow_partial``) sees a failed container with a
#      stderr that does NOT match the retryable-transport markers.
#   3. ``returncode != 0 and _is_retryable_docker_transport_error(output)``
#      (executor/host.py:141-148) — retryable rc-fail path, exercised
#      after all ``_DOCKER_MAX_RETRIES`` attempts still surface a
#      transport error (e.g. ``docker.sock`` unavailable).
#
# All three call ``_mask_harness_secret_in_message`` before constructing
# the ``ExecutorError``. The cases below pin the masking on sites (2) and
# (3) so a future refactor cannot accidentally strip the helper from one
# of the three paths and re-open the E4 surface while the timeout test
# stays green.
# ---------------------------------------------------------------------------


def test_run_playwright_automation_redacts_harness_secret_env_var_on_non_retryable_rc_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E4 mitigation — rc != 0 non-retryable path masks the harness env var.

    Drives ``run_playwright_automation`` (which calls
    ``_docker_exec_allow_partial``) into the partial-success branch where
    the container exits non-zero AND no report file was written, so
    ``run_playwright_automation`` then raises its own ``ExecutorError``
    with the captured output. ``_docker_exec_allow_partial`` itself
    short-circuits on ``allow_partial=True`` so the ``rc != 0 and not
    allow_partial`` site at host.py:132-139 is NOT reachable through
    that wrapper.

    To exercise site (2) directly we drive ``_docker_exec`` (the
    non-partial wrapper) end-to-end with a benign stderr that does not
    match the retryable-transport markers.
    """

    secret_hex = "feedfaceb16b00b5" * 4  # 64 chars hex, distinct from other cases.
    benign_failure_stderr = "extension activation handler crashed: invalid manifest"
    captured_full_cmd: list[list[str]] = []

    class _FakeCompleted:
        def __init__(self) -> None:
            self.returncode = 1
            self.stdout = ""
            self.stderr = benign_failure_stderr

    def fake_subprocess_run(
        cmd: list[str], *_args: Any, timeout: int | None = None, **_kwargs: Any
    ) -> Any:
        captured_full_cmd.append(list(cmd))
        return _FakeCompleted()

    monkeypatch.setattr(host_module.subprocess, "run", fake_subprocess_run)

    with pytest.raises(ExecutorError) as info:
        host_module._docker_exec(
            ["true"],
            extra_env={"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE": secret_hex},
        )

    # Sanity: the harness env-var made it into full_cmd so the masking
    # helper has something to redact.
    assert captured_full_cmd, "fake subprocess.run must have been invoked"
    assert any(
        f"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE={secret_hex}" == arg
        for arg in captured_full_cmd[0]
    ), (
        "_docker_exec must thread extra_env into the docker exec argv via "
        "``-e KEY=VALUE`` — without this the masking assertion below is "
        "vacuously true."
    )

    message = str(info.value)
    assert secret_hex not in message, (
        "E4 completeness (rc != 0 non-retryable path, host.py:132-139): "
        "ExecutorError.__str__ leaked the harness secret hex. The "
        "non-retryable rc-fail path also applies _mask_harness_secret_in_message; "
        "if this asserts the helper was stripped from that path while the "
        "timeout test stayed green."
    )
    assert "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***" in message, (
        "E4 completeness: the redacted env arg must be present as "
        "``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***`` so operators retain "
        "debug-ability over which env was passed."
    )


def test_run_playwright_automation_redacts_harness_secret_env_var_on_retryable_transport_rc_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E4 mitigation — rc != 0 retryable-transport path masks the harness env var.

    Drives ``_docker_exec_allow_partial`` (which short-circuits on the
    ``allow_partial`` branch only when transport is healthy) into the
    retryable-transport path by returning a stderr that matches one of
    ``_DOCKER_RETRYABLE_ERROR_MARKERS``. After ``_DOCKER_MAX_RETRIES``
    attempts the third raise at host.py:141-148 fires and the masking
    helper must apply.
    """

    secret_hex = "0123456789abcdef" * 4  # 64 chars hex, distinct.
    transport_stderr = (
        "error during connect: Get http://%2Fvar%2Frun%2Fdocker.sock/... "
        "Cannot connect to the Docker daemon"
    )
    captured_full_cmd: list[list[str]] = []

    class _FakeCompleted:
        def __init__(self) -> None:
            self.returncode = 1
            self.stdout = ""
            self.stderr = transport_stderr

    def fake_subprocess_run(
        cmd: list[str], *_args: Any, timeout: int | None = None, **_kwargs: Any
    ) -> Any:
        captured_full_cmd.append(list(cmd))
        return _FakeCompleted()

    # ``_run_docker_exec`` retries ``_DOCKER_MAX_RETRIES`` times with
    # exponential ``time.sleep(2**attempt)`` backoff between attempts; the
    # sleeps add ~5 s in real time. No-op them so the test stays fast.
    monkeypatch.setattr(host_module.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(host_module.time, "sleep", lambda _s: None)

    with pytest.raises(ExecutorError) as info:
        host_module._docker_exec_allow_partial(
            ["true"],
            extra_env={"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE": secret_hex},
        )

    assert len(captured_full_cmd) == host_module._DOCKER_MAX_RETRIES, (
        "the retryable-transport path must have been entered "
        "_DOCKER_MAX_RETRIES times before raising — otherwise the test "
        "exercised a different branch and the masking assertion below is "
        "not about site (3) at host.py:141-148."
    )

    message = str(info.value)
    assert secret_hex not in message, (
        "E4 completeness (rc != 0 retryable-transport-after-retries "
        "path, host.py:141-148): ExecutorError.__str__ leaked the "
        "harness secret hex. If this asserts the masking helper was "
        "stripped from the post-retry transport-error raise while the "
        "timeout and non-retryable tests stayed green."
    )
    assert "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***" in message, (
        "E4 completeness: the redacted env arg must be present as "
        "``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=***`` even after the "
        "retry exhaustion path fires."
    )
