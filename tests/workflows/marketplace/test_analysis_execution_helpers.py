"""Unit tests for workflows.marketplace.analysis_execution helpers."""

from __future__ import annotations

from executor.control import ExecutorError
from workflows.marketplace.analysis_execution import (
    install_failure_message,
    monitoring_failure_message,
)


def test_install_failure_message_without_output_returns_base_only() -> None:
    exc = ExecutorError("Command failed (rc=1): code --install-extension")
    message = install_failure_message(exc)
    assert message == "Extension installation failed inside the sandbox."


def test_install_failure_message_appends_stderr_tail() -> None:
    exc = ExecutorError(
        "Command failed (rc=1): code --install-extension",
        returncode=1,
        output="Error: singleton lock held by another process",
    )
    message = install_failure_message(exc)
    assert "Extension installation failed" in message
    assert "singleton lock held" in message


def test_install_failure_message_truncates_long_output_to_500_chars() -> None:
    big = "x" * 800 + "TAIL_MARKER"
    exc = ExecutorError("rc=1", returncode=1, output=big)
    message = install_failure_message(exc)
    assert "TAIL_MARKER" in message
    # First 300+ Xs from the head should NOT be in the tail slice.
    assert "x" * 600 not in message


def test_monitoring_failure_message_falls_back_when_detail_missing() -> None:
    exc = ExecutorError("")
    message = monitoring_failure_message(exc)
    assert message == (
        "Sandbox automation failed before the report could be finalized."
    )


def test_monitoring_failure_message_includes_detail_when_present() -> None:
    exc = ExecutorError("Command failed (rc=2): python3 entrypoint.py --monitor")
    message = monitoring_failure_message(exc)
    assert message.startswith(
        "Sandbox automation failed before the report could be finalized: "
    )
    assert "entrypoint.py" in message
