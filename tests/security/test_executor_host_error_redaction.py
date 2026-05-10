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
