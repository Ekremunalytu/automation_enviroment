"""Validated marketplace identity slugs for filesystem and argv use.

The helper enforces a single canonical token regex
(``MARKETPLACE_SLUG_TOKEN_RE``) for ``publisher``, ``name``, and ``version``
so adversarial inputs cannot smuggle path-traversal, shell metacharacters,
null bytes, or unicode confusables into a filesystem path or subprocess
argument. Call sites under ``workflows/``, ``packages/analysis_planner``,
and ``executor/`` all funnel through ``safe_marketplace_slug`` to produce
the canonical ``publisher.name-version`` form.

W8-5 will land ``appcore/contracts/validators.py::valid_extension_slug`` as
a Pydantic v2 ``@field_validator`` wrapping the same regex constant.
"""

from packages.marketplace_identity._slug import (
    MARKETPLACE_SLUG_TOKEN_RE,
    MarketplaceIdentityError,
    safe_marketplace_slug,
)

__all__ = [
    "MARKETPLACE_SLUG_TOKEN_RE",
    "MarketplaceIdentityError",
    "safe_marketplace_slug",
]
