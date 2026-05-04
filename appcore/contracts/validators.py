"""Validators consumed by API routers and Pydantic schemas (W8-5).

Single source-of-truth for the marketplace slug pattern. The regex constant
itself lives in ``packages.marketplace_identity._slug`` so the
framework-agnostic helper does not depend on Pydantic; this module
re-imports and wraps it for FastAPI/Pydantic surface use.

``ACTIVATION_REPORT_NAME_RE`` sandwiches the slug body between the
``activation_report_`` prefix and the ``.json`` suffix so a single
``Path(..., pattern=...)`` constraint on the activation-report router
covers both listing and path-param layers.

The body length is bounded to fit the widest name
``workflows.marketplace.job_service.build_report_name`` can emit:
``{publisher}.{name}-{version}-{run_id_12hex}`` where each
``safe_marketplace_slug`` token is bounded by
``MARKETPLACE_SLUG_TOKEN_RE`` at 65 characters. The producer body
therefore reaches at most ``3*65 + 2 (slug separators) + 1 + 12 = 210``
characters; we pin the regex at the same ceiling so a completed
analysis is never silently dropped from ``/api/activations`` or
``/api/activations/latest`` for a long extension name. The character
class stays identical to the per-token allowed set so widening the
length does not open any path-traversal vector.
"""

from __future__ import annotations

import re

from packages.marketplace_identity import MARKETPLACE_SLUG_TOKEN_RE

ACTIVATION_REPORT_NAME_RE: re.Pattern[str] = re.compile(
    r"^activation_report_[A-Za-z0-9][-_.A-Za-z0-9]{0,209}\.json$"
)


class InvalidExtensionSlugError(ValueError):
    """Raised when a slug fails marketplace identity validation."""


def valid_extension_slug(value: str) -> str:
    """Return ``value`` unchanged if it matches the marketplace slug pattern."""
    if not isinstance(value, str) or not value:
        raise InvalidExtensionSlugError(f"empty or non-string slug: {value!r}")
    if MARKETPLACE_SLUG_TOKEN_RE.fullmatch(value) is None:
        raise InvalidExtensionSlugError(
            f"slug rejected (must match {MARKETPLACE_SLUG_TOKEN_RE.pattern}): {value!r}"
        )
    return value


__all__ = [
    "ACTIVATION_REPORT_NAME_RE",
    "InvalidExtensionSlugError",
    "valid_extension_slug",
]
