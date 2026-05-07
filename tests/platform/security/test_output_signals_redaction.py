"""W10-7 regression: extension-controlled text surfaces are routed
through ``redact_secrets`` at construction time.

Closes [FOLLOWUP w8-6-output-signals-redaction]. The W8-6 sweep
identified three surfaces that were carrying raw extension-derived
text past the redaction filter:

1. ``executor/flows/playwright/output_signals.py`` building
   ``OutputSignalEvent.text``.
2. ``workflows/marketplace/analysis_execution.py::install_failure_message``
   appending a 500-byte stderr/stdout tail to the operator-visible job
   log.
3. ``workflows/marketplace/analysis_service.py::map_executor_error``
   logging the raw executor exception text via ``logger.warning``.

W10-7 pipes each through ``redact_secrets`` at construction so API
keys, DB URLs, and OAuth tokens emitted by the target extension never
reach persistent storage / log aggregation. This test pins each
surface end-to-end with an adversarial sample.

W12-0 extends surface (1) to the file-backed
``read_output_channel_logs`` path: the 2026-05-07 audit pass surfaced
that VS Code 1.105+ persists OutputChannel content directly to
``output_logging_<ts>/<idx>-<channel>.log`` files and bypasses the
harness-marker shim, so the file-side construction must redact too.
Closes [FOLLOWUP w8-6-output-signals-file-backed-redaction].
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from executor.control import ExecutorError
from packages.analysis_contracts import redact_secrets
from workflows.marketplace.analysis_execution import install_failure_message
from workflows.marketplace.analysis_service import map_executor_error

_BEARER_SAMPLE = "Authorization: Bearer abcdef0123456789ABCDEF.token-x"
_DB_URL_SAMPLE = "postgresql://admin:supersecret@db.internal:5432/prod"
_AWS_SAMPLE = "AKIAIOSFODNN7EXAMPLE"


def test_output_signals_redaction_chain_strips_bearer_token() -> None:
    """Mirror the OutputSignalEvent.text construction at
    output_signals.py:115 — _truncate then redact_secrets — and assert
    the bearer token disappears."""
    from executor.flows.playwright.output_signals import (
        _truncate,  # type: ignore[attr-defined]
    )

    raw = f"target log line: {_BEARER_SAMPLE}"
    text = redact_secrets(_truncate(raw))
    assert "abcdef0123456789ABCDEF.token-x" not in text
    assert "[REDACTED:bearer]" in text


def test_install_failure_message_redacts_db_url_in_tail() -> None:
    raw_tail = f"connect failed url={_DB_URL_SAMPLE} retries=3"
    exc = ExecutorError("install failed rc=1", returncode=1, output=raw_tail)
    msg = install_failure_message(exc)
    assert "supersecret" not in msg
    assert "[REDACTED:db_url]" in msg


def test_install_failure_message_benign_tail_unchanged() -> None:
    """Empty/no-secret payloads must round-trip unchanged so this
    redaction layer cannot introduce semantic drift on benign output."""
    exc = ExecutorError(
        "install failed rc=1", returncode=1, output="benign single line"
    )
    msg = install_failure_message(exc)
    assert "benign single line" in msg


def test_install_failure_message_no_output_unchanged() -> None:
    exc = ExecutorError("install failed rc=1", returncode=1, output="")
    msg = install_failure_message(exc)
    assert msg == "Extension installation failed inside the sandbox."


def test_map_executor_error_logger_warning_redacts_aws_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Pre-W8-7 the HTTP response leaked raw exception text; that close
    routed only a generic public detail to the response while still
    logging the raw text. W10-7 closes the remaining log-side leak by
    redacting before logger.warning."""
    raw = f"executor blew up because {_AWS_SAMPLE} expired"
    exc = ExecutorError("install failed rc=1", returncode=1, output=raw)
    # ExecutorError's str() uses output; force the str(exc) raw text to
    # contain the AWS key sample.
    exc.args = (raw,)

    with caplog.at_level(
        logging.WARNING, logger="workflows.marketplace.analysis_service"
    ):
        map_executor_error(exc)

    joined = " ".join(record.getMessage() for record in caplog.records)
    assert _AWS_SAMPLE not in joined
    assert "[REDACTED:aws]" in joined


def test_map_executor_error_public_detail_stays_generic() -> None:
    """Defends against W8-7 regression: the HTTP response detail must
    stay generic regardless of what raw text we redact for the log."""
    # Use a non-install exception path so the public detail uses the
    # generic "Automation failed in sandbox." branch.
    exc = ExecutorError("automation rc=1", returncode=1, output=_DB_URL_SAMPLE)
    http_exc = map_executor_error(exc)
    detail = str(http_exc.detail)
    assert "supersecret" not in detail
    assert "admin:" not in detail
    assert detail.startswith("Automation failed in sandbox.")


# --- W12-0: file-backed read_output_channel_logs redaction regressions ---


def _write_output_channel_log(
    base: Path, session: str, idx: int, channel: str, content: str
) -> Path:
    """Mirror the directory layout VS Code 1.105+ writes so
    ``read_output_channel_logs`` discovers the per-channel file via its
    ``**/output_logging_*/*-*.log`` glob. Sibling helper to the same
    fixture in ``tests/executor/test_output_signal_capture.py``; kept
    local here to avoid a cross-suite import dependency for a leaf
    fixture."""
    target_dir = base / session / "window1" / "exthost" / f"output_logging_{session}"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{idx}-{channel}.log"
    file_path.write_text(content)
    return file_path


def test_read_output_channel_logs_redacts_bearer_token(tmp_path: Path) -> None:
    """W12-0 regression: VS Code 1.105+ Output channel files are the
    primary post-W8-0 source. ``read_output_channel_logs`` must apply
    ``redact_secrets`` at construction so OAuth tokens emitted by the
    target extension never reach the persisted ActivationReport."""
    from executor.flows.playwright.output_signals import read_output_channel_logs

    _write_output_channel_log(
        tmp_path,
        session="20260507T120000",
        idx=1,
        channel="ExtraceTarget",
        content=f"target log line: {_BEARER_SAMPLE}\n",
    )

    events = read_output_channel_logs(tmp_path)

    assert len(events) == 1
    text = events[0].text
    assert "abcdef0123456789ABCDEF.token-x" not in text
    assert "[REDACTED:bearer]" in text


def test_read_output_channel_logs_redacts_db_url(tmp_path: Path) -> None:
    """W12-0 regression: connection strings emitted via console.log →
    Output channel file are scrubbed before reaching ``OutputSignalEvent.text``."""
    from executor.flows.playwright.output_signals import read_output_channel_logs

    _write_output_channel_log(
        tmp_path,
        session="20260507T120100",
        idx=2,
        channel="Pylance",
        content=f"connect failed url={_DB_URL_SAMPLE} retries=3\n",
    )

    events = read_output_channel_logs(tmp_path)

    assert len(events) == 1
    text = events[0].text
    assert "supersecret" not in text
    assert "[REDACTED:db_url]" in text


def test_read_output_channel_logs_redacts_aws_key_in_json_payload(
    tmp_path: Path,
) -> None:
    """W12-0 regression: the file-backed path also handles JSON-payload
    lines (the harness emits diagnostic appendLines as JSON). Redaction
    must run on the full line text post-JSON parse so AWS access keys
    embedded in stringified diagnostics never persist."""
    from executor.flows.playwright.output_signals import read_output_channel_logs

    json_payload = (
        '{"phase":"activate_enter","ts":1700000001000,'
        f'"detail":"executor blew up because {_AWS_SAMPLE} expired"}}'
    )
    _write_output_channel_log(
        tmp_path,
        session="20260507T120200",
        idx=3,
        channel="ExTrace Harness",
        content=f"{json_payload}\n",
    )

    events = read_output_channel_logs(tmp_path)

    assert len(events) == 1
    text = events[0].text
    assert _AWS_SAMPLE not in text
    assert "[REDACTED:aws]" in text


def test_read_output_channel_logs_benign_line_unchanged(tmp_path: Path) -> None:
    """W12-0 round-trip: the file-backed redaction layer must not
    introduce semantic drift on non-secret payloads — diagnostic lines
    without any tracked pattern survive byte-for-byte."""
    from executor.flows.playwright.output_signals import read_output_channel_logs

    benign = "indexed 1234 symbols"
    _write_output_channel_log(
        tmp_path,
        session="20260507T120300",
        idx=4,
        channel="Pylance",
        content=f"{benign}\n",
    )

    events = read_output_channel_logs(tmp_path)

    assert len(events) == 1
    assert events[0].text == benign
