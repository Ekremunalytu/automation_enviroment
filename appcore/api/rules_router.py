"""Operator-facing whitelist and editable blacklist rule configuration.

The effective denylist is the shipped seed file UNION the operator's DB-backed
additions; the detection rules (static ``s4`` once the static stage is wired, and
the live dynamic ``a7``) read that union. Edits here refresh the in-process
matcher override so ``a7`` reflects them on the next analysis without a restart.

- ``GET    /api/rules/blacklist-domains``        — seed + operator + effective list
- ``POST   /api/rules/blacklist-domains``        — add a domain (validated)
- ``DELETE /api/rules/blacklist-domains/{domain}`` — remove an operator-added domain
- ``GET    /api/rules/whitelist``                — curated trust catalog

Seed domains are the shipped baseline and are not removable here (an edit
augments the baseline), so a delete only affects operator-added domains.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from appcore.api.deps import get_db
from appcore.logging import get_extrace_logger
from workflows.detection_rules.blacklist_service import (
    BlacklistDomainValidationError,
    BlacklistView,
    add_domain,
    effective_blacklist,
    remove_domain,
)
from workflows.detection_rules.whitelist_service import (
    WhitelistView,
    effective_whitelist,
)

logger = get_extrace_logger("extrace.appcore.api.rules_router")

router = APIRouter(prefix="/api/rules", tags=["rules"])


class BlacklistDomainsResponse(BaseModel):
    """The configured blacklist: shipped seed, operator additions, and the union."""

    seed: list[str]
    operator: list[str]
    effective: list[str]
    count: int


class AddBlacklistDomainRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=253)
    added_by: str | None = Field(default=None, max_length=128)


class WhitelistDomainResponse(BaseModel):
    domain: str
    organization_id: str
    organization: str
    organization_kind: str
    purpose: str
    source_url: str | None


class WhitelistOrganizationResponse(BaseModel):
    id: str
    name: str
    kind: str
    publishers: list[str]
    extensions: list[str]


class WhitelistResponse(BaseModel):
    domains: list[WhitelistDomainResponse]
    organizations: list[WhitelistOrganizationResponse]
    extension_identities: list[str]
    domain_filtered_rule_ids: list[str]
    domain_count: int
    organization_count: int
    publisher_count: int
    extension_count: int


def _to_response(view: BlacklistView) -> BlacklistDomainsResponse:
    return BlacklistDomainsResponse(
        seed=view.seed,
        operator=view.operator,
        effective=view.effective,
        count=len(view.effective),
    )


def _to_whitelist_response(view: WhitelistView) -> WhitelistResponse:
    return WhitelistResponse(
        domains=[
            WhitelistDomainResponse(
                domain=entry.domain,
                organization_id=entry.organization_id,
                organization=entry.organization,
                organization_kind=entry.organization_kind,
                purpose=entry.purpose,
                source_url=entry.source_url,
            )
            for entry in view.domains
        ],
        organizations=[
            WhitelistOrganizationResponse(
                id=entry.id,
                name=entry.name,
                kind=entry.kind,
                publishers=entry.publishers,
                extensions=entry.extensions,
            )
            for entry in view.organizations
        ],
        extension_identities=view.extension_identities,
        domain_filtered_rule_ids=view.domain_filtered_rule_ids,
        domain_count=len(view.domains),
        organization_count=len(view.organizations),
        publisher_count=sum(len(entry.publishers) for entry in view.organizations),
        extension_count=len(view.extension_identities),
    )


@router.get("/whitelist", response_model=WhitelistResponse)
def get_whitelist() -> WhitelistResponse:
    """Return the reviewed, shipped trust catalog used by detection rules."""

    return _to_whitelist_response(effective_whitelist())


@router.get("/blacklist-domains", response_model=BlacklistDomainsResponse)
def get_blacklist_domains(db: Session = Depends(get_db)) -> BlacklistDomainsResponse:
    """Return the seed baseline, operator additions, and the effective denylist."""
    return _to_response(effective_blacklist(db))


@router.post("/blacklist-domains", response_model=BlacklistDomainsResponse)
def add_blacklist_domain(
    payload: Annotated[AddBlacklistDomainRequest, Body()],
    db: Session = Depends(get_db),
) -> BlacklistDomainsResponse:
    """Add an operator domain to the denylist (validated, idempotent)."""
    try:
        view = add_domain(db, domain=payload.domain, added_by=payload.added_by)
    except BlacklistDomainValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_blacklist_domain",
                "value": str(exc.value),
                "reason": exc.reason,
            },
        ) from exc
    logger.info("blacklist_domain_added domain=%r", payload.domain)
    return _to_response(view)


@router.delete("/blacklist-domains/{domain}", response_model=BlacklistDomainsResponse)
def delete_blacklist_domain(
    domain: str,
    db: Session = Depends(get_db),
) -> BlacklistDomainsResponse:
    """Remove an operator-added domain. 404 if it is not in the operator list."""
    removed, view = remove_domain(db, domain=domain)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "blacklist_domain_not_found",
                "value": domain,
                "reason": "not an operator-added domain (seed entries are fixed)",
            },
        )
    logger.info("blacklist_domain_removed domain=%r", domain)
    return _to_response(view)


__all__ = [
    "AddBlacklistDomainRequest",
    "BlacklistDomainsResponse",
    "WhitelistResponse",
    "router",
]
