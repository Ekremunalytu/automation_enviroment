"""Curated trusted network and marketplace identities.

The catalog is shared by the dynamic detection engine and the Rules API. Domain
entries suppress only the existing ``unknown outbound`` correlations; publisher
names are operator-facing provenance metadata and never suppress a behavioral
finding by themselves. Exact extension identifiers remain owned by
``typosquat_match.popular_extensions``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

_TRUST_CATALOG_PATH = Path(__file__).resolve().parent / "data" / "trusted_entities.json"


class TrustedDomain(BaseModel):
    """A host suffix with an explicit owner and operational purpose."""

    model_config = ConfigDict(frozen=True)

    domain: str = Field(min_length=1, max_length=253)
    purpose: str = Field(min_length=1, max_length=240)
    source_url: str | None = None


class TrustedOrganization(BaseModel):
    """A reviewed organization and its marketplace/network trust anchors."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["company", "foundation", "project", "community", "system"]
    publishers: list[str] = Field(default_factory=list)
    domains: list[TrustedDomain] = Field(default_factory=list)


class TrustedEntityCatalog(BaseModel):
    """Validated, versioned catalog loaded from the shipped JSON artifact."""

    model_config = ConfigDict(frozen=True)

    schema_version: Literal[1]
    organizations: list[TrustedOrganization]

    @model_validator(mode="after")
    def validate_unique_normalized_values(self) -> TrustedEntityCatalog:
        organization_ids: set[str] = set()
        domains: set[str] = set()
        publishers: set[str] = set()
        for organization in self.organizations:
            if organization.id in organization_ids:
                raise ValueError(
                    f"duplicate trusted organization id: {organization.id}"
                )
            organization_ids.add(organization.id)

            for publisher in organization.publishers:
                if publisher != publisher.strip().lower() or not publisher:
                    raise ValueError(
                        f"trusted publisher must be normalized: {publisher!r}"
                    )
                if publisher in publishers:
                    raise ValueError(f"duplicate trusted publisher: {publisher}")
                publishers.add(publisher)

            for entry in organization.domains:
                normalized = normalize_observed_host(entry.domain)
                if normalized != entry.domain:
                    raise ValueError(
                        f"trusted domain must be normalized: {entry.domain!r}"
                    )
                if entry.domain in domains:
                    raise ValueError(f"duplicate trusted domain: {entry.domain}")
                domains.add(entry.domain)
        return self


def normalize_observed_host(host: str) -> str:
    """Normalize an observed host, accepting common ``host:port`` forms."""

    value = host.strip().lower().rstrip(".")
    if not value:
        return ""

    if "://" in value:
        return (urlsplit(value).hostname or "").rstrip(".")
    if value.startswith("["):
        return (urlsplit(f"//{value}").hostname or "").rstrip(".")

    host_part, separator, port = value.rpartition(":")
    if separator and port.isdigit() and ":" not in host_part:
        return host_part.rstrip(".")
    return value


@lru_cache(maxsize=1)
def trusted_entity_catalog() -> TrustedEntityCatalog:
    """Load and validate the shipped trust catalog once per process."""

    return TrustedEntityCatalog.model_validate_json(
        _TRUST_CATALOG_PATH.read_text(encoding="utf-8")
    )


@lru_cache(maxsize=1)
def trusted_domains() -> frozenset[str]:
    """Return all domain suffixes used by unknown-outbound filtering."""

    return frozenset(
        entry.domain
        for organization in trusted_entity_catalog().organizations
        for entry in organization.domains
    )


def match_trusted_domain(host: str) -> str | None:
    """Return the matching trusted suffix for an observed host, if any."""

    normalized = normalize_observed_host(host)
    if not normalized:
        return None
    for trusted in sorted(trusted_domains(), key=len, reverse=True):
        if normalized == trusted or normalized.endswith(f".{trusted}"):
            return trusted
    return None


def is_trusted_domain(host: str) -> bool:
    """Whether an observed host belongs to a reviewed trusted suffix."""

    return match_trusted_domain(host) is not None


__all__ = [
    "TrustedDomain",
    "TrustedEntityCatalog",
    "TrustedOrganization",
    "is_trusted_domain",
    "match_trusted_domain",
    "normalize_observed_host",
    "trusted_domains",
    "trusted_entity_catalog",
]
