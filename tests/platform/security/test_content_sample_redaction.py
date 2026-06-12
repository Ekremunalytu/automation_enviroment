"""W8-6 — ContentSample secret redaction tests.

ContentSample.value goes through ``redact_secrets`` on construction and
on every assignment. These tests pin the five secret classes called out
in ADR 0003 §6.1 (aws, bearer, private_key, api_key, db_url) plus the
hardening cases (multi-secret value, idempotence, legitimate text
pass-through, validate_assignment re-entry).
"""

from __future__ import annotations

import pytest

from packages.analysis_contracts.evidence import (
    SECRET_CLASSES,
    ContentSample,
    redact_secrets,
)


def _sample(value: str) -> ContentSample:
    return ContentSample(value=value, source_location="test", sample_kind="line")


@pytest.mark.parametrize(
    "raw,must_contain,must_not_contain",
    [
        (
            "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "[REDACTED:aws]",
            "wJalrXUtnFEMI",
        ),
        (
            "spotted AKIAIOSFODNN7EXAMPLE in env",
            "[REDACTED:aws]",
            "AKIAIOSFODNN7EXAMPLE",
        ),
        (
            "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig",
            "[REDACTED:bearer]",
            "eyJhbGciOiJIUzI1NiJ9",
        ),
        (
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIB...\n-----END RSA PRIVATE KEY-----",
            "[REDACTED:private_key]",
            "MIIEpAIB",
        ),
        (
            'api_key="abcd1234efgh5678ijkl"',
            "[REDACTED:api_key]",
            "abcd1234efgh5678ijkl",
        ),
        (
            "postgres://admin:hunter2@db.internal:5432/prod",
            "[REDACTED:db_url]",
            "hunter2",
        ),
    ],
)
def test_secret_class_redacted(
    raw: str, must_contain: str, must_not_contain: str
) -> None:
    sample = _sample(raw)
    assert must_contain in sample.value
    assert must_not_contain not in sample.value


def test_multiple_secrets_in_same_value() -> None:
    raw = (
        "Authorization: Bearer eyJabc.def.ghi\n"
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        "DATABASE_URL=postgres://u:p@db.internal/x"
    )
    sample = _sample(raw)
    assert "[REDACTED:bearer]" in sample.value
    assert "[REDACTED:aws]" in sample.value
    assert "[REDACTED:db_url]" in sample.value
    assert "wJalrXUtnFEMI" not in sample.value
    assert "eyJabc" not in sample.value


def test_redact_idempotent() -> None:
    raw = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    once = redact_secrets(raw)
    twice = redact_secrets(once)
    assert once == twice


@pytest.mark.parametrize(
    "raw",
    [
        "the bearer of bad news",
        "api_key set in keyring",
        "https://docs.example.com/path",
        "the user typed AKIA into the search bar",
        "-----BEGIN COMMENT-----\nnot a key\n-----END COMMENT-----",
    ],
)
def test_legitimate_text_passes_through(raw: str) -> None:
    assert redact_secrets(raw) == raw


def test_empty_value() -> None:
    sample = ContentSample()
    assert sample.value == ""


def test_none_value_coerced_to_empty() -> None:
    sample = ContentSample(value=None)  # type: ignore[arg-type]
    assert sample.value == ""


def test_value_redacted_on_reassignment() -> None:
    sample = _sample("benign")
    sample.value = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert "[REDACTED:aws]" in sample.value
    assert "wJalrXUtnFEMI" not in sample.value


def test_extra_field_rejected() -> None:
    with pytest.raises(ValueError):
        ContentSample(value="x", unknown_field="y")  # type: ignore[call-arg]


def test_content_sample_re_exported_from_package() -> None:
    from packages import analysis_contracts

    assert analysis_contracts.ContentSample is ContentSample
    assert analysis_contracts.SECRET_CLASSES == SECRET_CLASSES
    assert analysis_contracts.redact_secrets is redact_secrets


# --- v1 finding F-1: redact_secrets itself is bounded + collapses any span ---
#
# W13-7 bounded ``redact_multiline_secrets`` (the per-line pre-pass), but
# ``redact_secrets`` -- the shared chokepoint used by report assembly,
# static-rule evidence (``static_runtime/rules/_common.py``),
# ``ContentSample``, and ``output_signals`` -- still ran the lazy
# ``BEGIN(?:.|\n)*?END`` private_key regex, which retries forward from each
# BEGIN. These pin the linear marker-pairing scanner at the
# ``redact_secrets`` level so every consumer (not just the report path) is
# protected, and that no span-length cap was introduced.

_PEM_BODY = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDAAAAAA"


def _pem(body_lines: int) -> str:
    return "\n".join(
        ["-----BEGIN PRIVATE KEY-----"]
        + [_PEM_BODY] * body_lines
        + ["-----END PRIVATE KEY-----"]
    )


def test_redact_secrets_bounded_on_unmatched_begin_flood() -> None:
    """F-1: ``redact_secrets`` stays linear on an adversarial flood of
    unmatched BEGIN markers. The pre-fix lazy regex retried forward from
    each BEGIN (~360 ms on this 200-marker / ~200 KB payload); the linear
    marker-pairing scanner finishes in a single pass per marker class. The
    100 ms ceiling fails the quadratic path with comfortable CI margin."""
    import time

    adversarial = ("-----BEGIN PRIVATE KEY-----\n" + "x" * 1000 + "\n") * 200

    start = time.perf_counter()
    result = redact_secrets(adversarial)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.100, (
        f"redact_secrets took {elapsed * 1000:.1f} ms on the 200-unmatched-"
        "BEGIN payload; the linear scanner must keep it bounded (pre-fix "
        "lazy regex runs ~360 ms and degrades super-linearly)."
    )
    # No END marker -> no span collapses; BEGIN markers stay literal.
    assert "[REDACTED:private_key]" not in result


def test_redact_secrets_collapses_multiple_well_formed_pem_blocks() -> None:
    """Each BEGIN..END span collapses independently to one token -- the
    scanner pairs each BEGIN with the next END, matching the legacy lazy
    regex's left-to-right ``sub`` behaviour."""
    raw = f"head\n{_pem(4)}\nmiddle\n{_pem(6)}\ntail"
    out = redact_secrets(raw)
    assert out.count("[REDACTED:private_key]") == 2
    assert _PEM_BODY not in out
    assert "head" in out and "middle" in out and "tail" in out


def test_redact_secrets_oversize_pem_span_fully_redacted() -> None:
    """The scanner imposes no span-length cap, so a PEM block far larger
    than the 16 KB ``redact_multiline_secrets`` window still collapses
    fully -- key bytes never survive in any ``redact_secrets`` consumer.
    ``_pem(2000)`` is a ~114 KB span (~7x the per-line-scanner cap)."""
    out = redact_secrets(_pem(2000))
    assert out == "[REDACTED:private_key]"
    assert _PEM_BODY not in out


def test_redact_secrets_unterminated_pem_left_literal() -> None:
    """A BEGIN with no following END is left literal (no false collapse),
    matching the lazy regex's no-match behaviour on an open span."""
    raw = "-----BEGIN PRIVATE KEY-----\n" + _PEM_BODY + "\nno end here"
    out = redact_secrets(raw)
    assert "[REDACTED:private_key]" not in out
    assert "-----BEGIN PRIVATE KEY-----" in out
