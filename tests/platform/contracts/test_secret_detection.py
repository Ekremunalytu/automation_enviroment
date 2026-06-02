"""Unit tests for the secret-detection helpers used by the s7 static rule.

``detect_secret_classes`` / ``find_secret_offsets`` are the read side of the same
secret taxonomy ``redact_secrets`` scrubs; the static ``s7_secret_exposure`` rule
flags credentials shipped in extension source with them. High precision matters:
ordinary source must stay silent.
"""

from __future__ import annotations

from packages.analysis_contracts.evidence import (
    detect_secret_classes,
    find_secret_offsets,
)

_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
_GH_TOKEN = "ghp_" + "a" * 36
_PEM = "-----BEGIN RSA PRIVATE KEY-----\nMII...\n-----END RSA PRIVATE KEY-----"


def test_detects_high_confidence_classes() -> None:
    assert detect_secret_classes(f'const k = "{_AWS_KEY}"') == ["aws"]
    assert detect_secret_classes(f"token = {_GH_TOKEN}") == ["github_token"]
    assert "private_key" in detect_secret_classes(_PEM)


def test_silent_on_ordinary_source() -> None:
    assert detect_secret_classes("const x = 1; // just code, no secrets") == []
    assert detect_secret_classes("") == []


def test_find_secret_offsets_points_without_leaking() -> None:
    text = f"line one\nconst key = '{_AWS_KEY}'\n"
    offsets = find_secret_offsets(text)
    assert offsets, "expected an AWS key offset"
    klass, offset = offsets[0]
    assert klass == "aws"
    # The offset lands on the second line (after the first newline).
    assert offset > text.index("\n")
