"""Service layer for the operator-editable ``blacklist_domains`` field.

Composes the shipped seed denylist
(``packages.analysis_contracts.domain_indicators``) with the operator's
DB-backed additions, and keeps the in-process matcher override in sync so the
dynamic ``extrace.a7.blacklisted_domain`` rule sees edits live (the API process
and the analysis worker thread share one process — ``API_WORKERS=1``).

- ``effective_blacklist(db)``: seed + operator + effective union (for the UI/API).
- ``add_domain`` / ``remove_domain``: validate, write, then refresh the override.
- ``refresh_operator_override(db)``: load operator rows -> set the matcher override
  (called at app startup and after every write).

The seed entries are the shipped baseline and are NOT removable here — an edit
augments the baseline (removal applies only to operator-added domains), so a
mistaken delete can never silently drop a known-bad domain from the seed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from appcore.storage.crud import (
    add_blacklist_domain_and_commit,
    list_blacklist_domains,
    remove_blacklist_domain_and_commit,
)
from packages.analysis_contracts.domain_indicators import (
    seed_domains,
    set_operator_blacklist,
)

# Registrable-domain shape: 1+ labels then a 2-63 char alpha TLD, <= 253 chars.
# Lowercase-only because the service normalizes before validating.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class BlacklistDomainValidationError(ValueError):
    """Raised when an operator-supplied blacklist domain is malformed."""

    def __init__(self, value: object, reason: str) -> None:
        super().__init__(f"{value!r}: {reason}")
        self.value = value
        self.reason = reason


@dataclass(frozen=True, slots=True)
class BlacklistView:
    """The seed baseline, operator additions, and their effective union."""

    seed: list[str]
    operator: list[str]
    effective: list[str]


def normalize_domain(domain: str) -> str:
    """Lowercase + strip a candidate domain (no validation)."""
    return domain.strip().lower().rstrip(".")


def validate_domain(domain: str) -> str:
    """Return the normalized domain or raise ``BlacklistDomainValidationError``."""
    normalized = normalize_domain(domain)
    if not normalized:
        raise BlacklistDomainValidationError(domain, "domain must not be empty")
    if not _DOMAIN_RE.match(normalized):
        raise BlacklistDomainValidationError(
            domain,
            "must be a valid domain name (e.g. 'evil.example'), not a URL or IP",
        )
    return normalized


def effective_blacklist(db: Session) -> BlacklistView:
    """Return the seed baseline, operator additions, and the effective union."""
    seed = sorted(seed_domains())
    operator = list_blacklist_domains(db)
    effective = sorted(set(seed) | set(operator))
    return BlacklistView(seed=seed, operator=operator, effective=effective)


def refresh_operator_override(db: Session) -> None:
    """Sync the in-process matcher override from the operator DB rows.

    Called at app startup and after every write so the dynamic ``a7`` rule's
    matcher reflects the current operator list without a process restart.
    """
    set_operator_blacklist(list_blacklist_domains(db))


def add_domain(db: Session, domain: str, added_by: str | None = None) -> BlacklistView:
    """Validate + persist a domain, refresh the override, return the new view."""
    normalized = validate_domain(domain)
    add_blacklist_domain_and_commit(db, domain=normalized, added_by=added_by)
    refresh_operator_override(db)
    return effective_blacklist(db)


def remove_domain(db: Session, domain: str) -> tuple[bool, BlacklistView]:
    """Remove an operator-added domain; refresh the override.

    Returns ``(removed, view)`` — ``removed`` is False when the domain was not in
    the operator list (e.g. a seed-only domain, which is not removable here).
    """
    normalized = normalize_domain(domain)
    removed = remove_blacklist_domain_and_commit(db, domain=normalized)
    refresh_operator_override(db)
    return removed, effective_blacklist(db)


__all__ = [
    "BlacklistDomainValidationError",
    "BlacklistView",
    "add_domain",
    "effective_blacklist",
    "normalize_domain",
    "refresh_operator_override",
    "remove_domain",
    "validate_domain",
]
