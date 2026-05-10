"""Runtime tests for ``_bounded_body_metadata`` body-preview redaction (W12-5).

The W12-5 architecture gate
``tests/architecture/test_network_body_preview_redaction.py`` is structural
— it walks the AST and refuses any ``*_body_preview`` assignment that does
not flow through ``redact_secrets`` or ``_bounded_body_metadata``. These
runtime tests pin the corresponding *behaviour*: the preview surface really
does redact tokens, honor the textual content-type filter, and clip at the
byte budget.
"""

from __future__ import annotations

from executor.flows.playwright.runtime_capture.network import (
    _HTTP_BODY_PREVIEW_BYTES,
    _bounded_body_metadata,
    parse_tshark_event_line,
)


def test_bounded_body_metadata_handles_empty_payload() -> None:
    """Empty payload short-circuits to the canonical empty-metadata shape."""
    metadata = _bounded_body_metadata("", "text/plain")

    assert metadata == {"sha256": "", "preview": "", "truncated": False}


def test_bounded_body_metadata_skips_preview_for_non_textual_content_type() -> None:
    """Binary payloads keep the sha256 fingerprint but no readable preview."""
    payload = "deadbeef"  # valid hex, decodes to 4 bytes

    metadata = _bounded_body_metadata(payload, "application/octet-stream")

    assert metadata["preview"] == ""
    assert metadata["truncated"] is True
    assert len(metadata["sha256"]) == 64  # sha256 hex digest


def test_bounded_body_metadata_truncates_textual_payload_past_budget() -> None:
    """Textual payload longer than the preview byte budget is marked truncated."""
    body = "A" * (_HTTP_BODY_PREVIEW_BYTES + 50)

    metadata = _bounded_body_metadata(body, "text/plain")

    assert metadata["truncated"] is True
    assert len(metadata["preview"]) == _HTTP_BODY_PREVIEW_BYTES
    # Within-budget payload must NOT be marked truncated.
    short = _bounded_body_metadata("hello", "text/plain")
    assert short["truncated"] is False
    assert short["preview"] == "hello"


def test_bounded_body_metadata_redacts_bearer_token_in_textual_preview() -> None:
    """The W12-5 defense: a bearer token in a JSON body is redacted in preview."""
    body = '{"user":"a","token":"Bearer abc123def456ghi789xyz0123456789","note":"hi"}'

    metadata = _bounded_body_metadata(body, "application/json")

    assert "[REDACTED:bearer]" in metadata["preview"]
    assert "abc123def456ghi789xyz" not in metadata["preview"]


def test_parse_tshark_event_line_redacts_aws_key_in_request_body_preview() -> None:
    """End-to-end: a tshark TSV line with an AWS key in the body lands redacted."""
    # Tshark TSV layout: 17 tab-separated fields. Field 13 is http_method,
    # field 15 is http_content_type, field 16 is http_body_hex.
    body = "AKIAIOSFODNN7EXAMPLE leaked"
    # tshark emits hex with byte separators (matches ``_HEX_SEPARATORS``).
    body_hex = ":".join(f"{b:02x}" for b in body.encode("utf-8"))
    fields = [
        "1700000000.500",  # 0  timestamp
        "10.0.0.1",  # 1  source_ip (ipv4)
        "",  # 2  source_ip (ipv6)
        "10.0.0.2",  # 3  destination_ip (ipv4)
        "",  # 4  destination_ip (ipv6)
        "443",  # 5  destination_port
        "",  # 6  destination_port (alt)
        "",  # 7  dns_query
        "example.com",  # 8  http_host
        "/api",  # 9  http_uri
        "",  # 10 tls_sni
        "tcp",  # 11 protocol
        "",  # 12 info
        "POST",  # 13 http_method
        "",  # 14 http_status_code
        "text/plain",  # 15 http_content_type
        body_hex,  # 16 http_body_hex
    ]

    event = parse_tshark_event_line("\t".join(fields))

    assert event is not None
    assert event.event_type == "http_request"
    # The AWS key constant must be redacted; the surrounding marker text is
    # preserved so analysts still see context.
    assert "[REDACTED:aws]" in event.request_body_preview
    assert "AKIAIOSFODNN7EXAMPLE" not in event.request_body_preview
