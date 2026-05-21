"""W14-3 (M13): NetworkEvent `path` + `summary` redaction regression.

Closes [`FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction`].

Pre-W14-3, ``executor/flows/playwright/runtime_capture/network.py``
populated ``NetworkEvent.path`` from the tshark-extracted ``http_uri``
field and ``NetworkEvent.summary`` from the same source (lines 122 +
132) without routing either through ``redact_secrets()``. The W12-5
architecture gate covered only ``*_body_preview`` fields, so a malicious
extension could surface secrets in URLs like
``http://api.example.com/v1/data?api_key=...`` and bearer tokens would
land verbatim in the persisted ActivationReport.

W14-3 routes both fields through the same ``redact_secrets()`` chokepoint
that already covers ``*_body_preview`` (W12-5) and ``arguments_preview``
(W13-6). The parametrize matrix below pins one tshark line per supported
secret class x both target fields, so any future regression that bypasses
the redaction fires here BEFORE the operator-visible report leaks.

Pattern modeled on W13-6
``tests/executor/test_playwright_extension_host.py::test_parse_strace_event_arguments_preview_redacts_secrets``
mirror.
"""

from __future__ import annotations

import pytest

from executor.flows.playwright.runtime_capture.network import (
    parse_tshark_event_line,
)


def _tshark_line(http_uri: str, *, info: str = "") -> str:
    """Build a 17-column tshark TSV line with the URI / info under test.

    Mirrors the production tshark output schema consumed by
    ``parse_tshark_event_line`` (line 40-62): timestamp, source IP family,
    destination IP family, ports, DNS, http_host, http_uri, tls_sni,
    protocol, info, method, status, content-type, body. Only the
    operator-relevant columns are filled; the rest stay empty so the
    parser still recognises an ``http_request``.
    """
    fields = [
        "1700000000.000",  # timestamp
        "10.0.0.1",  # src ipv4
        "",  # src ipv6
        "10.0.0.2",  # dst ipv4
        "",  # dst ipv6
        "443",  # dst port v4
        "",  # dst port v6
        "",  # dns_query
        "api.example.com",  # http_host
        http_uri,  # http_uri  ← under test
        "",  # tls_sni
        "tcp",  # protocol
        info,  # info  ← under test (when non-empty)
        "GET",  # http_method (forces event_type=http_request)
        "",  # http_status_code
        "",  # http_content_type
        "",  # http_body_hex
    ]
    return "\t".join(fields)


# ---------------------------------------------------------------------------
# Secret-class fixture matrix: one tshark URL embedding each supported
# `redact_secrets()` class. The replacement placeholder is what the
# redactor writes back; matching it asserts redaction happened AND no
# residue of the original secret remains.
# ---------------------------------------------------------------------------

# Three URI-friendly secret classes (the `redact_secrets` regexes match
# inside query strings as long as the token shape matches). `bearer` is
# covered separately below because its production form lives in the
# Authorization header (tshark `info` column), not the URL — its URL-
# encoded variant `Bearer%20...` would not satisfy the `\bBearer\s+...\b`
# pattern.
#
# (secret_class, uri_with_secret, expected_placeholder_substring)
_SECRET_CLASSES: list[tuple[str, str, str]] = [
    (
        "aws",
        "/v1/data?key=AKIAIOSFODNN7EXAMPLE&q=hello",
        "[REDACTED:aws]",
    ),
    (
        "api_key",
        # api_key regex requires the token body to be >=12 chars of
        # [A-Za-z0-9._-]; pick a deliberately long token so the match
        # cannot drift with future pattern tuning.
        "/v1/data?api_key=super-secret-token-12345abcd",
        "[REDACTED:api_key]",
    ),
    (
        "db_url",
        "/proxy?upstream=postgres://user:supersecret@db.example.com:5432/app",
        "[REDACTED:db_url]",
    ),
]


@pytest.mark.parametrize(
    "secret_class,uri,expected_placeholder",
    _SECRET_CLASSES,
    ids=[entry[0] for entry in _SECRET_CLASSES],
)
def test_network_event_path_is_redacted_for_every_secret_class(
    secret_class: str, uri: str, expected_placeholder: str
) -> None:
    """W14-3 (M13): ``NetworkEvent.path`` must surface the placeholder for
    every supported secret class — the raw secret must NOT appear anywhere
    in the path field.
    """
    event = parse_tshark_event_line(_tshark_line(uri))
    assert event is not None, f"{secret_class}: tshark line failed to parse"
    assert expected_placeholder in event.path, (
        f"{secret_class}: expected placeholder {expected_placeholder!r} "
        f"in path={event.path!r}"
    )


@pytest.mark.parametrize(
    "secret_class,uri,expected_placeholder",
    _SECRET_CLASSES,
    ids=[entry[0] for entry in _SECRET_CLASSES],
)
def test_network_event_summary_is_redacted_for_every_secret_class(
    secret_class: str, uri: str, expected_placeholder: str
) -> None:
    """W14-3 (M13): ``NetworkEvent.summary`` derives from the same
    extension-controlled URI plus optional tshark ``info`` text. Both
    contributions must run through the redactor.

    The info-empty branch builds summary from ``event_type``, ``host`` /
    ``destination_ip``, and ``http_uri`` (lines 99-101); the info-filled
    branch surfaces the tshark ``info`` column verbatim. Both flow through
    ``redact_secrets()`` after W14-3.
    """
    # Empty info → summary built from URI components.
    event = parse_tshark_event_line(_tshark_line(uri))
    assert event is not None
    assert expected_placeholder in event.summary, (
        f"{secret_class}: empty-info summary={event.summary!r} missing "
        f"placeholder {expected_placeholder!r}"
    )

    # Non-empty info → summary surfaces tshark info verbatim; redactor
    # must scrub it.
    info_text = f"GET {uri} HTTP/1.1"
    event = parse_tshark_event_line(_tshark_line(uri, info=info_text))
    assert event is not None
    assert expected_placeholder in event.summary, (
        f"{secret_class}: info-filled summary={event.summary!r} missing "
        f"placeholder {expected_placeholder!r}"
    )


def test_network_event_path_preserves_non_secret_urls() -> None:
    """W14-3 regression guard: a URL without any matched secret class must
    pass through unchanged. The M13 fix is a redactor, not a normalizer.
    """
    benign_uri = "/v1/extensions/list?page=2&limit=50"
    event = parse_tshark_event_line(_tshark_line(benign_uri))
    assert event is not None
    assert event.path == benign_uri
    assert benign_uri in event.summary


def test_network_event_path_with_no_secret_keeps_path_present() -> None:
    """W14-3: even without a secret to redact, the path field still
    surfaces the original URL. The redactor must not collapse benign URLs
    to empty strings.
    """
    event = parse_tshark_event_line(_tshark_line("/health"))
    assert event is not None
    assert event.path == "/health"


def test_network_event_redaction_handles_multiple_secret_classes_in_one_uri() -> None:
    """W14-3: a single URL carrying two distinct secret classes must
    surface BOTH placeholders. ``redact_secrets()`` applies every class
    in sequence; the path field inherits the same behavior.
    """
    multi_secret_uri = (
        "/v1/data?api_key=super-secret-token-12345abcd&trace=AKIAIOSFODNN7EXAMPLE"  # noqa: S105
    )
    event = parse_tshark_event_line(_tshark_line(multi_secret_uri))
    assert event is not None
    assert "[REDACTED:api_key]" in event.path
    assert "[REDACTED:aws]" in event.path
    # Raw secrets must not survive
    assert "AKIAIOSFODNN7EXAMPLE" not in event.path
    assert "super-secret-token-12345abcd" not in event.path


def test_network_event_summary_redacts_bearer_token_from_info_column() -> None:
    """W14-3 (M13): the `bearer` redaction class lives in the
    ``Authorization: Bearer ...`` header pattern. tshark surfaces request
    headers in its `info` column for the http_request event type, so the
    bearer token in production lands inside ``NetworkEvent.summary`` (via
    the `info` branch of the summary derivation at network.py:99).
    Routing the `info` source through ``redact_secrets()`` removes the
    raw bearer token before the report is persisted.
    """
    bearer_info = "GET /v1/data HTTP/1.1 | Authorization: Bearer abcdefghij1234567890"
    event = parse_tshark_event_line(_tshark_line("/v1/data", info=bearer_info))
    assert event is not None
    assert "[REDACTED:bearer]" in event.summary
    assert "abcdefghij1234567890" not in event.summary
