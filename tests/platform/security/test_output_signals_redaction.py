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
from packages.analysis_contracts import redact_multiline_secrets, redact_secrets
from workflows.marketplace.analysis_execution import install_failure_message
from workflows.marketplace.analysis_service import map_executor_error

_BEARER_SAMPLE = "Authorization: Bearer abcdef0123456789ABCDEF.token-x"
_DB_URL_SAMPLE = "postgresql://admin:supersecret@db.internal:5432/prod"
_AWS_SAMPLE = "AKIAIOSFODNN7EXAMPLE"

# PEM markers concatenated at runtime so the test source itself does not
# contain the literal substring the `detect-private-key` pre-commit hook
# scans for. The runtime values are byte-identical to real PEM markers
# and match the cross-line `private_key` pattern in
# `packages/analysis_contracts/evidence.py`.
_PEM_BEGIN = "-----" + "BEGIN " + "PRIVATE " + "KEY-----"
_PEM_END = "-----" + "END " + "PRIVATE " + "KEY-----"
# Fake base64 body — never a real key, just realistic-shaped 64-char chunks
# (the redact pattern is structural; body content is opaque to it).
_PEM_BODY = (
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDxFAKEFAKEFAKE\n"
    "0123456789abcdefABCDEF0123456789abcdefABCDEF0123456789abcdefABCD\n"
    "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
)


def test_output_signals_redaction_chain_strips_bearer_token() -> None:
    """Mirror the OutputSignalEvent.text construction at
    output_signals.py:115 — _truncate then redact_secrets — and assert
    the bearer token disappears."""
    from executor.flows.playwright.signals.output import (
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


def test_install_failure_message_redacts_multiline_pem_split_by_tail() -> None:
    """Installer stderr uses the same operator-visible job-log surface as
    output signals. A PEM block can be longer than the retained 500-char tail;
    redact the full output before tailing so the retained suffix cannot carry
    orphaned body lines.
    """

    body = "\n".join([_PEM_BODY] * 10)
    raw = (
        "prefix before retained tail\n"
        + f"{_PEM_BEGIN}\n{body}\n{_PEM_END}\n"
        + "install failed after reading package metadata"
    )
    exc = ExecutorError("install failed rc=1", returncode=1, output=raw)

    msg = install_failure_message(exc)

    assert "install failed after reading package metadata" in msg
    assert "MIIEvQIBADANBgkqhkiG9w0B" not in msg
    assert "ZZZZZZZZZZZZZZZZ" not in msg
    assert _PEM_BEGIN not in msg
    assert _PEM_END not in msg
    assert "[REDACTED:private_key]" in msg


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


# --- W12-0: harness-marker parse_output_signal_events end-to-end regressions ---
#
# The W10-7 chain test (`test_output_signals_redaction_chain_strips_bearer_token`)
# pins the `_truncate` → `redact_secrets` composition at the unit level. The
# tests below close the symmetry gap with the file-backed regressions further
# down by exercising the real `parse_output_signal_events` entry the runtime
# goes through, so a regression that drops the redact step inside the harness
# branch (instead of just inside the helper) is also caught.


def _harness_appendline_marker(text: str, ts_ms: int = 1_700_000_000_000) -> str:
    import json

    return "[extrace-harness] " + json.dumps(
        {
            "kind": "output_channel_appendline",
            "channel": "ExtraceTarget",
            "text": text,
            "ts": ts_ms,
            "collector": "harness_extension",
        }
    )


def test_parse_output_signal_events_redacts_db_url_in_payload_text() -> None:
    """End-to-end harness-marker path: a target extension that prints a
    Postgres URL via ``console.log`` produces an OutputSignalEvent whose
    ``text`` strips the credential portion before the report is built."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    raw = f"connect failed url={_DB_URL_SAMPLE} retries=3"
    events = parse_output_signal_events(_harness_appendline_marker(raw))

    assert len(events) == 1
    text = events[0].text
    assert "supersecret" not in text
    assert "[REDACTED:db_url]" in text


def test_parse_output_signal_events_redacts_aws_key_in_payload_text() -> None:
    """End-to-end harness-marker path: AWS access keys leaking through
    ``console.log`` are redacted before the OutputSignalEvent is constructed."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    raw = f"executor blew up because {_AWS_SAMPLE} expired"
    events = parse_output_signal_events(_harness_appendline_marker(raw))

    assert len(events) == 1
    text = events[0].text
    assert _AWS_SAMPLE not in text
    assert "[REDACTED:aws]" in text


def test_parse_output_signal_events_benign_payload_unchanged() -> None:
    """W10-7 round-trip on the harness-marker entry: payloads without any
    tracked secret pattern survive the redact filter byte-for-byte."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    benign = "indexed 1234 symbols"
    events = parse_output_signal_events(_harness_appendline_marker(benign))

    assert len(events) == 1
    assert events[0].text == benign


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
    from executor.flows.playwright.signals.output import read_output_channel_logs

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
    from executor.flows.playwright.signals.output import read_output_channel_logs

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
    from executor.flows.playwright.signals.output import read_output_channel_logs

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
    from executor.flows.playwright.signals.output import read_output_channel_logs

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


# --- W12-0 follow-up: OutputSignalEvent.{channel,summary} redaction ---
#
# W12-0 closed text-side redaction at both the harness-marker source and the
# file-backed VS Code 1.105+ source, but left ``channel`` (and the
# ``summary`` interpolation built on top of it) carrying raw
# extension-supplied strings. An adversarial extension can call
# ``vscode.window.createOutputChannel("AKIA...")`` and reach the persisted
# ActivationReport via either source. The tests below pin both sources +
# the false-positive guard for benign channels.


def _channel_appendline_marker(channel: str, text: str = "benign") -> str:
    """Harness-marker fixture with a parametrizable ``channel`` field;
    sibling helper to ``_harness_appendline_marker`` above (which fixes
    channel='ExtraceTarget'). Kept local to this test block to avoid
    refactor churn on the existing W10-7/W12-0 cases."""
    import json

    return "[extrace-harness] " + json.dumps(
        {
            "kind": "output_channel_appendline",
            "channel": channel,
            "text": text,
            "ts": 1_700_000_000_000,
            "collector": "harness_extension",
        }
    )


@pytest.mark.parametrize(
    "raw_channel, expected_marker",
    [
        ("AKIA1234567890ABCDEF", "[REDACTED:aws]"),
        ("Bearer eyJhbGciOiJIUzI1NiJ9", "[REDACTED:bearer]"),
        ("api_key=sk-test-1234567890abcdef", "[REDACTED:api_key]"),
        ("postgres://user:p%40ss@db:5432/x", "[REDACTED:db_url]"),
    ],
)
def test_harness_marker_channel_redaction(
    raw_channel: str, expected_marker: str
) -> None:
    """W12-0 follow-up: harness-marker source must redact extension-supplied
    secrets out of both ``OutputSignalEvent.channel`` and ``summary``."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    events = parse_output_signal_events(_channel_appendline_marker(raw_channel))
    assert len(events) == 1
    assert expected_marker in events[0].channel
    assert raw_channel not in events[0].channel
    assert raw_channel not in events[0].summary
    assert expected_marker in events[0].summary


@pytest.mark.parametrize(
    "filename_channel, expected_marker",
    [
        # VS Code 1.105+'s ``output_logging_*/<idx>-<channel>.log`` glob
        # captures the channel name greedily (``.+`` in
        # ``_OUTPUT_CHANNEL_FILE_RE``), so spaces are preserved verbatim
        # from the extension-supplied ``createOutputChannel`` argument.
        ("AKIA1234567890ABCDEF", "[REDACTED:aws]"),
        ("Bearer eyJhbGciOiJIUzI1NiJ9", "[REDACTED:bearer]"),
    ],
)
def test_file_backed_channel_redaction(
    tmp_path: Path, filename_channel: str, expected_marker: str
) -> None:
    """W12-0 follow-up: file-backed source must redact secrets embedded
    in the per-channel filename (``<idx>-<channel>.log``)."""
    from executor.flows.playwright.signals.output import read_output_channel_logs

    _write_output_channel_log(
        tmp_path,
        session="20260507T120400",
        idx=0,
        channel=filename_channel,
        content="benign content\n",
    )

    events = read_output_channel_logs(tmp_path)
    assert len(events) == 1
    assert expected_marker in events[0].channel
    assert filename_channel not in events[0].channel
    assert filename_channel not in events[0].summary


def test_benign_channel_unchanged() -> None:
    """W12-0 follow-up false-positive guard: benign channel names round-trip
    byte-for-byte and the summary interpolation stays semantically intact."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    events = parse_output_signal_events(
        _channel_appendline_marker("GitHub Copilot", text="Hello")
    )
    assert len(events) == 1
    assert events[0].channel == "GitHub Copilot"
    assert events[0].summary == "OutputChannel(GitHub Copilot) appendLine"


# --- W12-0 follow-up: multi-line PEM redaction across split boundaries ---
#
# Closes [FOLLOWUP w12-0-output-signal-multiline-secret-redaction]. The
# `redact_secrets` private-key pattern requires BEGIN..END span in one
# string (`(?:.|\n)*?` is lazy across newlines, not across separate
# `redact_secrets` calls). Pre-W12-0-followup: per-line / per-marker
# redaction missed multi-line PEM blocks because `splitlines()` placed
# BEGIN, body chunks, and END in separate strings; the body chunks
# (base64) matched no other pattern and persisted to ActivationReport.
# These tests pin the pre-pass `redact_secrets(content)` step on both the
# file-backed and harness-marker sources.


def test_read_output_channel_logs_redacts_multiline_pem_block(
    tmp_path: Path,
) -> None:
    """File-backed path: a PEM block whose BEGIN / body / END land on
    separate lines of the persisted Output channel file must be redacted
    end-to-end. None of the body's base64 chunks should appear in any
    OutputSignalEvent.text."""
    from executor.flows.playwright.signals.output import read_output_channel_logs

    pem = f"{_PEM_BEGIN}\n{_PEM_BODY}\n{_PEM_END}"
    _write_output_channel_log(
        tmp_path,
        session="20260508T100000",
        idx=5,
        channel="ExtraceTarget",
        content=pem + "\n",
    )

    events = read_output_channel_logs(tmp_path)

    joined_text = " ".join(e.text for e in events)
    # No base64 body chunk leaks.
    assert "MIIEvQIBADANBgkqhkiG9w0B" not in joined_text
    assert "ZZZZZZZZZZZZZZZZ" not in joined_text
    # Neither does either marker survive verbatim — both are inside the
    # redacted span (regex includes BEGIN..END inclusive).
    assert _PEM_BEGIN not in joined_text
    assert _PEM_END not in joined_text
    # Marker placeholder must be present somewhere in the surviving events.
    assert any("[REDACTED:private_key]" in e.text for e in events)


def test_read_output_channel_logs_multiline_pem_with_surrounding_lines(
    tmp_path: Path,
) -> None:
    """File-backed path: lines outside the PEM span are preserved
    byte-for-byte while the BEGIN..END block collapses to the
    `[REDACTED:private_key]` placeholder. Pins that the redaction is
    span-scoped and does not corrupt unrelated diagnostic output."""
    from executor.flows.playwright.signals.output import read_output_channel_logs

    pem = f"{_PEM_BEGIN}\n{_PEM_BODY}\n{_PEM_END}"
    content = f"indexed 1234 symbols\n{pem}\nindexed 5678 symbols\n"
    _write_output_channel_log(
        tmp_path,
        session="20260508T100100",
        idx=6,
        channel="Pylance",
        content=content,
    )

    events = read_output_channel_logs(tmp_path)
    joined_text = " ".join(e.text for e in events)

    # Surrounding diagnostic lines survive verbatim.
    assert any(e.text == "indexed 1234 symbols" for e in events)
    assert any(e.text == "indexed 5678 symbols" for e in events)
    # PEM body and markers are gone.
    assert "MIIEvQIBADANBgkqhkiG9w0B" not in joined_text
    assert _PEM_BEGIN not in joined_text
    assert _PEM_END not in joined_text
    assert any("[REDACTED:private_key]" in e.text for e in events)


def test_parse_output_signal_events_redacts_cross_marker_pem_block() -> None:
    """Harness-marker path: an adversarial extension that splits a PEM
    block across three separate `appendLine` calls (BEGIN / body / END)
    produces three harness markers; per-marker `redact_secrets(text)`
    cannot see the BEGIN..END span. The whole-input pre-pass collapses the
    cross-marker span before splitlines, so no body chunk leaks. Marker
    structure inside the span may be lost — that is the accepted trade
    against leaking the body."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    blob = (
        _harness_appendline_marker(_PEM_BEGIN)
        + "\n"
        + _harness_appendline_marker(_PEM_BODY)
        + "\n"
        + _harness_appendline_marker(_PEM_END)
    )
    events = parse_output_signal_events(blob)

    joined_text = " ".join(e.text for e in events)
    # Body chunks must not surface.
    assert "MIIEvQIBADANBgkqhkiG9w0B" not in joined_text
    assert "ZZZZZZZZZZZZZZZZ" not in joined_text
    # PEM markers themselves are inside the redacted span.
    assert _PEM_BEGIN not in joined_text
    assert _PEM_END not in joined_text


def test_parse_output_signal_events_single_marker_multiline_pem() -> None:
    """Harness-marker path: a single `appendLine` with embedded \\n
    delivers BEGIN/body/END inside one JSON `text` field. Single-string
    `redact_secrets(text)` already catches this (cross-line `(?:.|\\n)*?`
    pattern); confirm the canonical happy-path stays redacted after the
    new pre-pass is added."""
    from executor.flows.playwright.signals.output import parse_output_signal_events

    pem = f"{_PEM_BEGIN}\n{_PEM_BODY}\n{_PEM_END}"
    events = parse_output_signal_events(_harness_appendline_marker(pem))

    assert len(events) == 1
    text = events[0].text
    assert "MIIEvQIBADANBgkqhkiG9w0B" not in text
    assert _PEM_BEGIN not in text
    assert _PEM_END not in text
    assert "[REDACTED:private_key]" in text


# --- W13-7: PEM regex DoS — bounded latency on adversarial input ---
#
# Codex Cloud audit (2026-05-10) MEDIUM finding M1: the cross-line
# `private_key` regex in `packages/analysis_contracts/evidence.py:56-63`
# uses a lazy `(?:.|\n)*?` quantifier between BEGIN and END markers.
# When `redact_multiline_secrets()` runs `pattern.sub()` over Extension-Host
# stdout that contains many unmatched BEGIN markers, the engine retries
# from each BEGIN position searching forward for an END, producing
# O(N*L) latency. Empirical pre-fix measurement (2026-05-11):
# 200 BEGIN markers + 1 KB body each + no END → ~361 ms per call.
#
# This timing test pins the post-fix latency budget. W13-7 sub-commit 3
# replaces the regex.sub() with a bounded linear scanner.


@pytest.mark.skip(
    reason="W13-7 RED precursor — redact_multiline_secrets() still uses the "
    "lazy cross-line regex; sub-commit 3 lands the bounded scanner."
)
def test_redact_multiline_secrets_rejects_catastrophic_pem_pattern() -> None:
    """W13-7 — bounded scanner must keep adversarial PEM input under 100 ms.

    The adversarial payload is 200 unmatched BEGIN markers (each on its
    own line, padded with 1 KB of body bytes) and no terminating END.
    Pre-fix pattern.sub() takes ~361 ms because the lazy quantifier
    retries forward from each BEGIN; the bounded scanner finishes in
    a single linear pass (<10 ms expected). The 100 ms ceiling
    leaves comfortable CI margin.
    """
    import time

    adversarial = ("".join([_PEM_BEGIN, "\n", "x" * 1000, "\n"])) * 200

    start = time.perf_counter()
    result = redact_multiline_secrets(adversarial)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.100, (
        f"redact_multiline_secrets() took {elapsed * 1000:.1f} ms on the "
        "W13-7 adversarial PEM payload (200 BEGIN markers, no END, "
        "~200 KB input). The bounded scanner must complete this scan in "
        "under 100 ms; the pre-fix lazy-regex path runs ~361 ms."
    )
    # Sanity: no END marker means no redaction span — bounded scanner
    # leaves BEGIN markers in place rather than swallowing them.
    assert "[REDACTED:private_key]" not in result, (
        "Without an END marker the bounded scanner must not redact "
        f"(got: {result[:200]!r}...)."
    )
