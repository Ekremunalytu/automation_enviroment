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
