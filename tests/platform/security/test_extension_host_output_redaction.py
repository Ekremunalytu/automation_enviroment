"""W11 companion regression: ``ActivationReport.extension_host_output``
is routed through ``redact_secrets`` at the serialization boundary.

Closes ``[FOLLOWUP w8-6-extension-host-output-redaction]``. The
``executor/flows/playwright/report_builder.py::build_report_data``
serializer copies the last 500 lines of Extension Host stdout/stderr into
the persisted ``ActivationReport.extension_host_output`` string. Until
this companion landed, that text reached disk raw — extension
``console.log`` output, ``OutputChannel.appendLine`` writes, or runtime
exception stacks could carry AKIA tokens, bearer headers, or Postgres
DSNs straight through the pipeline.

This test pins the redaction at the dict-emission level (the value the
report writer hands off to ``save_report_payload``) and at the JSON
encoding boundary (raw byte form on disk). The W8-9 P2
``_bounded_body_metadata`` precedent established the same pattern for
HTTP body previews; this test mirrors that surface for the Extension Host
output channel.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from executor.flows.playwright.report_builder import build_report_data

_BEARER_SAMPLE = "Authorization: Bearer abcdef0123456789ABCDEF.token-x"
_DB_URL_SAMPLE = "postgresql://admin:supersecret@db.internal:5432/prod"
_AWS_SAMPLE = "AKIAIOSFODNN7EXAMPLE"
_API_KEY_SAMPLE = "api_key=verysecret-api-token-9988"
_PEM_BODY_LINE = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDAAAAAA"


def _build_minimal_report(extension_host_output: str) -> SimpleNamespace:
    """Return a minimal ``report``-shaped object accepted by
    ``build_report_data``. Every other field falls through to the
    ``getattr(..., default)`` paths in the serializer."""

    return SimpleNamespace(extension_host_output=extension_host_output)


def _build_payload(extension_host_output: str) -> dict[str, object]:
    return build_report_data(
        _build_minimal_report(extension_host_output),
        evidence_events=[],
        evidence_links=[],
        risk_signals=[],
        risk_summary={},
        run_quality="unknown",
        automation_health={},
        log_health={},
        attribution_summary={},
        summary={},
    )


def test_extension_host_output_redacts_aws_bearer_db_url() -> None:
    """An adversarial Extension Host log tail carrying AWS, bearer, and
    Postgres DSN samples reaches the serializer dict in the redacted
    form only — the W8-6 ``redact_secrets`` filter is wired."""

    raw = (
        "ext-host stdout: api_key="
        f"{_AWS_SAMPLE}\n"
        f"ext-host stderr: {_BEARER_SAMPLE}\n"
        f"ext-host stdout: connect url={_DB_URL_SAMPLE} retries=3"
    )
    payload = _build_payload(raw)

    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)
    # Raw forms must not appear at the dict emit level.
    assert _AWS_SAMPLE not in eh_emitted
    assert "abcdef0123456789ABCDEF.token-x" not in eh_emitted
    assert "supersecret" not in eh_emitted
    # Redaction tags from the W8-6 pattern set are present.
    assert "[REDACTED:aws]" in eh_emitted
    assert "[REDACTED:bearer]" in eh_emitted
    assert "[REDACTED:db_url]" in eh_emitted


def test_extension_host_output_redacted_at_json_disk_boundary(
    tmp_path: Path,
) -> None:
    """The on-disk JSON form (the artifact analysts and the API consume)
    contains only the redacted value. The check is byte-exact so a
    future encoding change cannot silently re-leak the secret."""

    raw = (
        f"ext-host stdout: {_BEARER_SAMPLE}\n"
        f"ext-host stderr: api_key={_AWS_SAMPLE}\n"
        f"ext-host stderr: connect url={_DB_URL_SAMPLE} pool=2"
    )
    payload = _build_payload(raw)

    out = tmp_path / "activation_report.json"
    out.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    on_disk_bytes = out.read_bytes()
    assert _AWS_SAMPLE.encode("utf-8") not in on_disk_bytes
    assert b"abcdef0123456789ABCDEF.token-x" not in on_disk_bytes
    assert b"supersecret" not in on_disk_bytes
    assert b"[REDACTED:aws]" in on_disk_bytes
    assert b"[REDACTED:bearer]" in on_disk_bytes
    assert b"[REDACTED:db_url]" in on_disk_bytes

    # Round-trip the JSON back to confirm the redacted form survives the
    # encode/decode cycle (catches future codec drift).
    reloaded = json.loads(on_disk_bytes.decode("utf-8"))
    assert "[REDACTED:aws]" in reloaded["extension_host_output"]
    assert "[REDACTED:bearer]" in reloaded["extension_host_output"]
    assert "[REDACTED:db_url]" in reloaded["extension_host_output"]


def test_extension_host_output_empty_round_trips_unchanged() -> None:
    """Empty payloads must pass through cleanly — the redaction layer
    cannot introduce semantic drift on benign output."""

    payload = _build_payload("")
    assert payload["extension_host_output"] == ""
    assert payload["extension_host_output_lines"] == 0


def test_extension_host_output_benign_payload_preserved() -> None:
    """A multi-line Extension Host log with no secrets round-trips
    unchanged — redaction must be content-preserving outside the
    pattern matches."""

    raw = "ext-host: starting Python language server\nextension activated"
    payload = _build_payload(raw)
    assert payload["extension_host_output"] == raw


def test_extension_host_output_trailing_newline_preserved_on_short_input() -> None:
    """Short captures pass straight through ``redact_secrets`` without
    any line-stream rebuild, so a trailing ``\\n`` on the raw input
    survives onto the persisted dict. Pinned so a future refactor that
    routes the short branch through ``splitlines()/join`` does not
    silently strip the trailing byte."""

    raw = "ext-host: line 1\next-host: line 2\n"
    payload = _build_payload(raw)
    assert payload["extension_host_output"] == raw
    assert payload["extension_host_output"].endswith("\n")


def test_extension_host_output_trailing_newline_preserved_on_truncated_input() -> None:
    """The truncated branch rebuilds the window via ``splitlines()`` +
    ``"\\n".join(...)``, which would silently drop a trailing newline.
    The reattachment branch in ``build_report_data`` keeps the round-
    trip uniform with the short-input branch — pin it so the two
    branches cannot drift apart on this trailing-byte invariant."""

    benign_prefix = "\n".join(f"benign line {i}" for i in range(600))
    raw = f"{benign_prefix}\nfinal trailing\n"
    assert raw.endswith("\n")  # sanity on the fixture itself

    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)
    assert eh_emitted.endswith("\n")
    # And the cap still ran — head benign prefix dropped, trailing
    # line retained (proves the trailing-newline pin is not just a
    # by-product of skipping the trim branch entirely).
    assert "benign line 0" not in eh_emitted
    assert "final trailing" in eh_emitted


def test_extension_host_output_500_line_truncation_preserves_redaction() -> None:
    """The 500-line tail window in ``build_report_data`` is computed on
    the raw line stream first; ``redact_secrets`` is applied second on
    the (possibly expanded) window. Confirm that an adversarial payload
    placed at the very end of a >500-line buffer lands in redacted form
    on the persisted dict — independent of the orphaned-PEM ordering
    invariant pinned by the dedicated PEM cases below."""

    benign_prefix = "\n".join(f"benign line {i}" for i in range(600))
    raw = f"{benign_prefix}\nfinal: api_key={_AWS_SAMPLE}"
    payload = _build_payload(raw)

    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)
    # Tail-only retention: the very-early benign prefix is truncated,
    # the trailing secret-bearing line is retained AND redacted.
    assert _AWS_SAMPLE not in eh_emitted
    assert "[REDACTED:aws]" in eh_emitted
    assert "benign line 0" not in eh_emitted  # head dropped by tail-trim
    assert "benign line 599" in eh_emitted  # final benign line kept


def test_extension_host_output_redact_secrets_idempotent_at_boundary() -> None:
    """``redact_secrets`` is idempotent (W8-6 invariant). Re-running the
    same already-redacted text through ``build_report_data`` is a
    no-op on the emitted field — guards against double-tag regression
    if a caller pre-redacts."""

    pre_redacted = (
        "ext-host: token=[REDACTED:bearer]\n"
        "ext-host: url=[REDACTED:db_url]\n"
        "ext-host: key=[REDACTED:aws]"
    )
    payload = _build_payload(pre_redacted)
    assert payload["extension_host_output"] == pre_redacted


@pytest.mark.parametrize(
    ("sample", "expected_tag"),
    [
        (f"key={_AWS_SAMPLE}", "[REDACTED:aws]"),
        (_BEARER_SAMPLE, "[REDACTED:bearer]"),
        (f"url={_DB_URL_SAMPLE}", "[REDACTED:db_url]"),
        (_API_KEY_SAMPLE, "[REDACTED:api_key]"),
    ],
)
def test_extension_host_output_individual_pattern_classes(
    sample: str, expected_tag: str
) -> None:
    """Surface-by-surface coverage so a future regression that drops
    one pattern class still surfaces here. Covers four of the five
    ``SECRET_CLASSES`` (``aws`` / ``bearer`` / ``db_url`` /
    ``api_key``); ``private_key`` needs the multi-line BEGIN/END span
    and is exercised by the dedicated PEM cases below."""

    payload = _build_payload(f"ext-host: {sample}")
    assert expected_tag in payload["extension_host_output"]


def _pem_block(body_lines: int) -> str:
    """A multi-line PEM private-key block. The ``private_key`` redaction
    pattern matches the ``-----BEGIN ... PRIVATE KEY-----`` …
    ``-----END ... PRIVATE KEY-----`` span as a unit; if the BEGIN
    marker is trimmed away the orphaned body bypasses redaction."""

    return "\n".join(
        ["-----BEGIN PRIVATE KEY-----"]
        + [_PEM_BODY_LINE] * body_lines
        + ["-----END PRIVATE KEY-----"]
    )


def test_extension_host_output_orphaned_pem_body_does_not_leak() -> None:
    """Reviewer-flagged regression: the tail truncation must not strand
    a PEM private-key body without its BEGIN marker.

    Layout: 100 benign prefix lines, then BEGIN @100, 500 body lines
    @101-600, END @601, then 50 benign suffix lines (652 total). The
    last-500-lines window starts at line 152 - BEGIN is dropped while
    the body and END remain. The naive ``tail-then-redact`` order would
    leave the orphaned body unmatched (the ``private_key`` pattern is a
    BEGIN…END span, not a per-line match) and persist the raw key
    bytes. Redaction must run on the full input *before* the tail
    truncation."""

    prefix = "\n".join(f"benign prefix {i}" for i in range(100))
    suffix = "\n".join(f"benign suffix {i}" for i in range(50))
    raw = f"{prefix}\n{_pem_block(500)}\n{suffix}"

    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)

    # Raw key body bytes never reach the persisted dict, even though
    # the tail trim drops the BEGIN marker that keys the regex.
    assert _PEM_BODY_LINE not in eh_emitted
    # The redaction tag survives the trim because the span collapsed
    # to a single token before truncation.
    assert "[REDACTED:private_key]" in eh_emitted

    # Tail-window invariant (Codex review #3, 2026-05-05): the original
    # 500-line cutoff means lines 0..151 (benign prefix 0..99 plus the
    # BEGIN + first 51 PEM body lines) live BEFORE the retained tail.
    # Even though redaction collapses the 500-line PEM body to a
    # single token, none of those head benign lines may slip past the
    # cap via collapse-driven inflation.
    assert "benign prefix 0" not in eh_emitted
    assert "benign prefix 99" not in eh_emitted
    # Suffix lives inside the original raw tail window — must persist.
    assert "benign suffix 0" in eh_emitted
    assert "benign suffix 49" in eh_emitted


def test_extension_host_output_pem_block_fully_inside_tail_redacted() -> None:
    """Sanity: a PEM block that lives entirely within the retained
    500-line window is redacted exactly the same way as in the
    orphaned case — same persisted form, no leak."""

    raw = f"{_pem_block(20)}\nbenign trailing"
    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]

    assert _PEM_BODY_LINE not in eh_emitted
    assert "[REDACTED:private_key]" in eh_emitted


def test_extension_host_output_multiple_well_formed_pem_blocks_redacted() -> None:
    """Multiple back-to-back PEM spans in the same buffer each collapse
    independently to ``[REDACTED:private_key]``. Pins the BEGIN-
    expansion detector's ``in_pem`` toggle: BEGIN sets True, END
    resets False; a *second* BEGIN must enter the True state again,
    not be skipped. A future refactor that treats ``in_pem`` as a
    one-shot latch (not a toggle) would silently drop the second
    span's redaction — caught here."""

    raw = f"prefix line\n{_pem_block(10)}\nmiddle line\n{_pem_block(15)}\ntrailing line"
    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)

    # Both spans collapse independently — exactly two tokens.
    assert eh_emitted.count("[REDACTED:private_key]") == 2
    assert _PEM_BODY_LINE not in eh_emitted
    # Benign framing lines around and between the spans survive.
    assert "prefix line" in eh_emitted
    assert "middle line" in eh_emitted
    assert "trailing line" in eh_emitted


def test_extension_host_output_pem_block_fully_outside_tail_no_residue() -> None:
    """When the entire PEM span is older than the 500-line tail
    cutoff, the redaction collapses it to ``[REDACTED:private_key]``
    on the full input first; the tail then drops the whole token along
    with the rest of the head. No raw key bytes survive in either
    direction."""

    pem = _pem_block(20)  # 22 lines including markers
    suffix = "\n".join(f"benign tail line {i}" for i in range(800))
    raw = f"{pem}\n{suffix}"

    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]

    # Body bytes never persist.
    assert _PEM_BODY_LINE not in eh_emitted
    # Token also dropped because the trim leaves only the suffix.
    assert "[REDACTED:private_key]" not in eh_emitted
    # Last benign suffix line is retained - proves the trim ran.
    assert "benign tail line 799" in eh_emitted


def test_extension_host_output_lines_metric_uses_raw_capture() -> None:
    """``extension_host_output_lines`` reports the line count of the
    *raw* captured output, not the redacted form, so analysts can see
    how much log was originally captured even when redaction collapses
    multi-line spans (PEM blocks) into a single token. Pin this so a
    future "consistency" refactor that switches the metric to the
    persisted text would surface here.

    Construction: a 22-line PEM block plus a benign trailing line (23
    raw newlines, 24 raw lines). After redaction the PEM collapses to
    a single ``[REDACTED:private_key]`` token, so the persisted form
    holds far fewer lines - but the metric must still reflect the
    original capture length."""

    pem = _pem_block(20)  # BEGIN + 20 body + END = 22 lines
    raw = f"{pem}\nbenign trailing"  # 23 lines total, 22 newlines
    payload = _build_payload(raw)

    # Metric is the raw newline count (\n in the original capture).
    assert payload["extension_host_output_lines"] == raw.count("\n")
    # The persisted form is collapsed; if the metric leaked through
    # the redacted form, it would report ~1 instead of 22.
    assert payload["extension_host_output_lines"] == 22

    # And the persisted form is genuinely collapsed - sanity check
    # that we are testing a real divergence, not a coincidence.
    persisted_lines = str(payload["extension_host_output"]).count("\n")
    assert persisted_lines < payload["extension_host_output_lines"]


def test_extension_host_output_orphaned_pem_at_json_disk_boundary(
    tmp_path: Path,
) -> None:
    """Reviewer-flagged regression continued: pin the orphaned-PEM
    redaction at the on-disk JSON byte level too, not just the dict
    emit. A future encoding change (e.g. switching to base64 wrapping
    or a serializer that re-escapes) cannot silently re-leak the key
    body bytes through the persisted artifact."""

    prefix = "\n".join(f"benign prefix {i}" for i in range(100))
    suffix = "\n".join(f"benign suffix {i}" for i in range(50))
    raw = f"{prefix}\n{_pem_block(500)}\n{suffix}"

    payload = _build_payload(raw)

    out = tmp_path / "activation_report.json"
    out.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    on_disk_bytes = out.read_bytes()
    # Raw key body bytes must never appear in the persisted artifact.
    assert _PEM_BODY_LINE.encode("utf-8") not in on_disk_bytes
    # The redaction tag survives the encode/decode cycle.
    assert b"[REDACTED:private_key]" in on_disk_bytes


def test_extension_host_output_tail_window_resists_pem_collapse_inflation() -> None:
    """Codex review #3 (2026-05-05): an adversarial extension can plant
    a multi-line block surrounded by ``BEGIN/END PRIVATE KEY`` markers
    so the redaction collapses thousands of attacker-controlled lines
    into a single token. If the 500-line cap is computed AFTER
    redaction, the cap silently slips and lines that lived FAR before
    the original raw tail window survive into the persisted dict —
    the extension can effectively choose which prefix lines reach the
    analyst.

    Layout: 800 attacker-controlled prefix lines, then a synthetic
    PEM block (BEGIN + 5000 body lines + END), then 100 suffix lines.
    The original-raw 500-line tail cutoff falls deep inside the body;
    none of the prefix lines should reach the persisted dict.
    """

    prefix = "\n".join(f"attacker prefix {i}" for i in range(800))
    suffix = "\n".join(f"benign suffix {i}" for i in range(100))
    raw = f"{prefix}\n{_pem_block(5000)}\n{suffix}"

    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)

    # PEM span collapses to a single redaction token; raw body bytes
    # never reach the persisted dict.
    assert "[REDACTED:private_key]" in eh_emitted
    assert _PEM_BODY_LINE not in eh_emitted

    # Attacker-controlled prefix lines lived BEFORE the original raw
    # 500-line tail cutoff (which fell inside the PEM body). Even
    # though redaction collapses ~5002 lines into one, the cap is
    # computed on raw lines first, so none of the prefix can slip
    # past via collapse-driven inflation.
    assert "attacker prefix 0" not in eh_emitted
    assert "attacker prefix 799" not in eh_emitted

    # Suffix lines sat inside the original raw tail window and must
    # persist — proves the cap is correctly anchored, not too tight.
    assert "benign suffix 0" in eh_emitted
    assert "benign suffix 99" in eh_emitted


def test_extension_host_output_mixed_secret_classes_in_single_buffer() -> None:
    """A single capture commonly carries several secret classes (an
    extension that logs a request might emit a Bearer header, a DB
    URL, and an AWS key in the same trace). Pin that the redaction
    patterns compose - applying them in sequence redacts every class
    without one matcher consuming text the next one needed."""

    raw = (
        "ext-host: starting request\n"
        f"ext-host: header={_BEARER_SAMPLE}\n"
        f"ext-host: env AWS_ACCESS_KEY_ID={_AWS_SAMPLE}\n"
        f"ext-host: dsn={_DB_URL_SAMPLE}\n"
        f"ext-host: cred {_API_KEY_SAMPLE}\n"
        f"{_pem_block(8)}\n"
        "ext-host: done"
    )
    payload = _build_payload(raw)
    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)

    # All four single-line classes redacted.
    assert "[REDACTED:aws]" in eh_emitted
    assert "[REDACTED:bearer]" in eh_emitted
    assert "[REDACTED:db_url]" in eh_emitted
    assert "[REDACTED:api_key]" in eh_emitted
    # Multi-line PEM span redacted.
    assert "[REDACTED:private_key]" in eh_emitted

    # No raw token forms survive in any class.
    assert _AWS_SAMPLE not in eh_emitted
    assert "abcdef0123456789ABCDEF.token-x" not in eh_emitted
    assert "supersecret" not in eh_emitted
    assert "verysecret-api-token-9988" not in eh_emitted
    assert _PEM_BODY_LINE not in eh_emitted

    # Benign framing lines preserved - confirms redaction did not
    # over-match and eat surrounding context.
    assert "ext-host: starting request" in eh_emitted
    assert "ext-host: done" in eh_emitted


# --- v1 finding F-1: redact_secrets on the report path is un-hangable ---
#
# W13-7 bounded ``redact_multiline_secrets`` (the per-line pre-pass), but
# ``build_report_data`` redacts the Extension-Host tail through
# ``redact_secrets`` — which still ran the lazy ``BEGIN(?:.|\n)*?END``
# regex. An adversarial extension that floods stdout with unmatched BEGIN
# markers therefore drove report assembly into the same catastrophic
# O(N*L) backtracking on the verdict-producing path. The v1
# ``reliability-self-defense`` stream routes ``redact_secrets``'s
# private_key class through a linear marker-pairing scanner; these two
# tests pin the fix at the report-build boundary.


def test_extension_host_output_unbounded_pem_redact_is_bounded() -> None:
    """F-1 timing regression: a tail stuffed with 200 unmatched
    ``-----BEGIN PRIVATE KEY-----`` markers (no END) must not stall
    ``build_report_data``.

    The pre-fix lazy ``private_key`` regex retries forward from each
    BEGIN — empirically ~360 ms on this 200-marker / ~240 KB payload and
    worse as the buffer grows. The linear scanner finishes in a single
    pass per marker class (<10 ms expected). The 100 ms ceiling fails the
    quadratic path while leaving comfortable CI margin."""

    import time

    # BEGIN marker + ~1 KB body, no terminating END, x200. 400 lines, so
    # the whole buffer sits inside the 500-line tail window and reaches
    # redact_secrets via the report-build path.
    line = "-----BEGIN PRIVATE KEY-----\n" + "x" * 1000 + "\n"
    raw = line * 200

    start = time.perf_counter()
    payload = _build_payload(raw)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.100, (
        f"build_report_data took {elapsed * 1000:.1f} ms redacting a "
        "200-unmatched-BEGIN Extension-Host tail (~240 KB). redact_secrets "
        "must route private_key through the linear scanner; the pre-fix "
        "lazy regex runs ~360 ms and degrades super-linearly."
    )

    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)
    # No END marker means no span collapses; the scanner leaves the BEGIN
    # markers literal rather than swallowing them (matches the lazy
    # regex's no-match behaviour on an unterminated span).
    assert "[REDACTED:private_key]" not in eh_emitted


def test_extension_host_output_oversize_pem_span_fully_redacted() -> None:
    """F-1 companion: the linear scanner imposes no span-length cap, so a
    well-formed PEM block far larger than the 16 KB
    ``_redact_private_key_bounded`` window still collapses fully through
    ``redact_secrets`` on the report path.

    Guards against a future refactor that routes ``redact_secrets``
    through the capped per-line scanner and silently leaves >16 KB of key
    bytes in the persisted report. ``_pem_block(2000)`` is a ~114 KB span
    — ~7x the bounded-scanner cap."""

    raw = _pem_block(2000)
    payload = _build_payload(raw)

    eh_emitted = payload["extension_host_output"]
    assert isinstance(eh_emitted, str)
    # Body bytes never persist and the whole span collapses to one token,
    # even though the span dwarfs the 16 KB per-line-scanner window.
    assert _PEM_BODY_LINE not in eh_emitted
    assert eh_emitted.count("[REDACTED:private_key]") == 1
