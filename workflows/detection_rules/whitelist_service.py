"""Read-only operator view of the curated detection whitelist.

Network domains feed the dynamic engine's existing unknown-outbound filter.
Organization/publisher metadata makes ownership reviewable, while only exact
extension identifiers from the typosquat baseline receive identity treatment.
Publisher names alone never suppress behavioral detections.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.analysis_contracts import trusted_entity_catalog
from packages.analysis_contracts.typosquat_match import popular_extensions

_DOMAIN_FILTERED_RULE_IDS = (
    "extrace.a1.credential_read_then_network",
    "extrace.a2.startup_network_beacon",
    "extrace.a4.workspace_exfil",
    "extrace.a8.reverse_shell",
)


@dataclass(frozen=True, slots=True)
class WhitelistDomainView:
    domain: str
    organization_id: str
    organization: str
    organization_kind: str
    purpose: str
    source_url: str | None


@dataclass(frozen=True, slots=True)
class WhitelistOrganizationView:
    id: str
    name: str
    kind: str
    publishers: list[str]
    extensions: list[str]


@dataclass(frozen=True, slots=True)
class WhitelistView:
    domains: list[WhitelistDomainView]
    organizations: list[WhitelistOrganizationView]
    extension_identities: list[str]
    domain_filtered_rule_ids: list[str]


def effective_whitelist() -> WhitelistView:
    """Compose the shipped domain, owner, publisher, and extension baselines."""

    catalog = trusted_entity_catalog()
    extensions = sorted(popular_extensions())
    domains = sorted(
        (
            WhitelistDomainView(
                domain=entry.domain,
                organization_id=organization.id,
                organization=organization.name,
                organization_kind=organization.kind,
                purpose=entry.purpose,
                source_url=entry.source_url,
            )
            for organization in catalog.organizations
            for entry in organization.domains
        ),
        key=lambda entry: entry.domain,
    )
    organizations = sorted(
        (
            WhitelistOrganizationView(
                id=organization.id,
                name=organization.name,
                kind=organization.kind,
                publishers=list(organization.publishers),
                extensions=[
                    extension
                    for extension in extensions
                    if extension.partition(".")[0] in organization.publishers
                ],
            )
            for organization in catalog.organizations
        ),
        key=lambda entry: entry.name.casefold(),
    )
    return WhitelistView(
        domains=domains,
        organizations=organizations,
        extension_identities=extensions,
        domain_filtered_rule_ids=list(_DOMAIN_FILTERED_RULE_IDS),
    )


__all__ = [
    "WhitelistDomainView",
    "WhitelistOrganizationView",
    "WhitelistView",
    "effective_whitelist",
]
