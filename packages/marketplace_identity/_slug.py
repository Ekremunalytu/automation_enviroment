"""Implementation of ``safe_marketplace_slug`` and supporting types."""

from __future__ import annotations

import re

MARKETPLACE_SLUG_TOKEN_RE: re.Pattern[str] = re.compile(
    r"^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$"
)


class MarketplaceIdentityError(ValueError):
    """Raised when ``publisher``/``name``/``version`` violate slug discipline."""

    def __init__(self, field: str, value: str, reason: str) -> None:
        super().__init__(f"Invalid marketplace identity {field!r}: {reason}.")
        self.field = field
        self.value = value
        self.reason = reason


def _validate_token(field: str, value: str) -> str:
    if not isinstance(value, str):
        raise MarketplaceIdentityError(
            field, str(value), f"expected str, got {type(value).__name__}"
        )
    if not value:
        raise MarketplaceIdentityError(field, value, "empty token")
    if MARKETPLACE_SLUG_TOKEN_RE.fullmatch(value) is None:
        raise MarketplaceIdentityError(
            field,
            value,
            "must match ^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$",
        )
    return value


def safe_marketplace_slug(publisher: str, name: str, version: str) -> str:
    """Return canonical ``"publisher.name-version"`` slug after strict validation.

    Each token must satisfy ``MARKETPLACE_SLUG_TOKEN_RE``: a single leading
    alphanumeric followed by 0-64 ``[-_.A-Za-z0-9]`` characters. The regex
    fully rejects path-traversal sequences (``..``), shell metacharacters
    (``;``, ``$``, backtick, pipe, redirect), null bytes, leading dots or
    hyphens, whitespace, and unicode confusables. Tokens longer than 65
    characters are rejected so a single field cannot saturate a path budget.

    Raises ``MarketplaceIdentityError`` (a ``ValueError`` subclass) on the
    first offending token; the exception carries the field name, the
    rejected value, and the rule that fired so callers can surface a
    structured error.
    """
    safe_publisher = _validate_token("publisher", publisher)
    safe_name = _validate_token("name", name)
    safe_version = _validate_token("version", version)
    return f"{safe_publisher}.{safe_name}-{safe_version}"
