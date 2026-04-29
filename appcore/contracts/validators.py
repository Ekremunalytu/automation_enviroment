"""Validators consumed by API routers and Pydantic schemas (W8-5).

Single source-of-truth for the marketplace slug pattern. The regex constant
itself lives in ``packages.marketplace_identity._slug`` so the
framework-agnostic helper does not depend on Pydantic; this module
re-imports and wraps it for FastAPI/Pydantic surface use.

``ACTIVATION_REPORT_NAME_RE`` sandwiches the slug body between the
``activation_report_`` prefix and the ``.json`` suffix so a single
``Path(..., pattern=...)`` constraint on the activation-report router
covers both validation layers.
"""

from __future__ import annotations

import re

from packages.marketplace_identity import MARKETPLACE_SLUG_TOKEN_RE

assert MARKETPLACE_SLUG_TOKEN_RE.pattern.startswith("^") and (
    MARKETPLACE_SLUG_TOKEN_RE.pattern.endswith("$")
), "MARKETPLACE_SLUG_TOKEN_RE must remain anchored for slug-body extraction"

_SLUG_BODY = MARKETPLACE_SLUG_TOKEN_RE.pattern[1:-1]

ACTIVATION_REPORT_NAME_RE: re.Pattern[str] = re.compile(
    rf"^activation_report_{_SLUG_BODY}\.json$"
)


class InvalidExtensionSlugError(ValueError):
    """Raised when a slug fails marketplace identity validation."""


def valid_extension_slug(value: str) -> str:
    """Return ``value`` unchanged if it matches the marketplace slug pattern."""
    if not isinstance(value, str) or not value:
        raise InvalidExtensionSlugError(f"empty or non-string slug: {value!r}")
    if MARKETPLACE_SLUG_TOKEN_RE.fullmatch(value) is None:
        raise InvalidExtensionSlugError(
            f"slug rejected (must match {MARKETPLACE_SLUG_TOKEN_RE.pattern}): "
            f"{value!r}"
        )
    return value


__all__ = [
    "ACTIVATION_REPORT_NAME_RE",
    "InvalidExtensionSlugError",
    "valid_extension_slug",
]
