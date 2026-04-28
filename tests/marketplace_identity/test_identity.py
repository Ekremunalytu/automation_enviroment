"""W8-2 ``safe_marketplace_slug`` adversarial-input regression tests.

Mirrors the pattern in ``tests/workflows/marketplace/test_vsix_hardening.py``
(W8-1): one happy path + parametrized adversarial inputs that the helper
must reject before any filesystem path or subprocess argument is built.
"""

from __future__ import annotations

import pytest

from packages.marketplace_identity import (
    MARKETPLACE_SLUG_TOKEN_RE,
    MarketplaceIdentityError,
    safe_marketplace_slug,
)


def test_canonical_slug_for_realistic_publisher_name_version() -> None:
    assert (
        safe_marketplace_slug("ms-python", "python", "2026.5.2026042602")
        == "ms-python.python-2026.5.2026042602"
    )


@pytest.mark.parametrize(
    ("publisher", "name", "version"),
    [
        ("ms-python", "python", "1.0.0"),
        ("github", "copilot", "1.105.0"),
        ("Anthropic_Inc", "claude.code", "0.0.1-rc.1"),
        ("a", "b", "c"),
    ],
)
def test_helper_accepts_valid_tokens(publisher: str, name: str, version: str) -> None:
    slug = safe_marketplace_slug(publisher, name, version)
    assert slug == f"{publisher}.{name}-{version}"


@pytest.mark.parametrize(
    ("field", "publisher", "name", "version"),
    [
        # Path traversal — the canonical W8-2 attack vector.
        ("publisher", "../etc", "python", "1.0.0"),
        ("name", "ms-python", "../passwd", "1.0.0"),
        ("version", "ms-python", "python", "../1.0.0"),
        # Shell metacharacters — terminal/argv injection.
        ("publisher", ";rm -rf /", "python", "1.0.0"),
        ("name", "ms-python", "python$(whoami)", "1.0.0"),
        ("version", "ms-python", "python", "1.0.0|cat"),
        # Null byte — C-string truncation.
        ("publisher", "ms-python\x00evil", "python", "1.0.0"),
        # Empty token — ambiguous canonical form.
        ("publisher", "", "python", "1.0.0"),
        ("name", "ms-python", "", "1.0.0"),
        ("version", "ms-python", "python", ""),
        # Leading hyphen — argv-style flag injection (e.g. `--install`).
        ("publisher", "-evil", "python", "1.0.0"),
        ("version", "ms-python", "python", "-evil"),
        # Leading dot — hidden-file or relative-path injection.
        ("publisher", ".hidden", "python", "1.0.0"),
        # Unicode bidi override — visible identifier mismatch.
        ("publisher", "pub‮evil", "python", "1.0.0"),
        # Whitespace — argv-splitting / log-line injection.
        ("name", "ms-python", "py thon", "1.0.0"),
        # Slash — path-component split.
        ("publisher", "ms/python", "python", "1.0.0"),
        ("name", "ms-python", "python/lib", "1.0.0"),
        # Backslash — Windows path separator.
        ("name", "ms-python", "python\\lib", "1.0.0"),
        # Overlong token (>65 chars) — path-budget exhaustion.
        ("publisher", "a" * 66, "python", "1.0.0"),
        ("name", "ms-python", "b" * 66, "1.0.0"),
        ("version", "ms-python", "python", "c" * 66),
    ],
)
def test_helper_rejects_adversarial_token(
    field: str, publisher: str, name: str, version: str
) -> None:
    with pytest.raises(MarketplaceIdentityError) as exc_info:
        safe_marketplace_slug(publisher, name, version)
    assert exc_info.value.field == field


def test_error_carries_structured_diagnostic_fields() -> None:
    with pytest.raises(MarketplaceIdentityError) as exc_info:
        safe_marketplace_slug("../etc", "python", "1.0.0")
    err = exc_info.value
    assert err.field == "publisher"
    assert err.value == "../etc"
    assert err.reason  # non-empty rule description
    assert "publisher" in str(err)


def test_token_regex_pins_canonical_shape() -> None:
    """The exposed ``MARKETPLACE_SLUG_TOKEN_RE`` constant is the contract
    W8-5's ``valid_extension_slug`` validator will re-import; pin the shape
    so the regex cannot drift between W8-2 and W8-5 without breaking this
    test."""
    assert MARKETPLACE_SLUG_TOKEN_RE.pattern == r"^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$"
    assert MARKETPLACE_SLUG_TOKEN_RE.fullmatch("ms-python") is not None
    assert MARKETPLACE_SLUG_TOKEN_RE.fullmatch("../etc") is None


def test_non_string_token_is_rejected_with_clear_field_label() -> None:
    with pytest.raises(MarketplaceIdentityError) as exc_info:
        safe_marketplace_slug("ms-python", 1234, "1.0.0")  # type: ignore[arg-type]
    assert exc_info.value.field == "name"
    assert "expected str" in str(exc_info.value)
