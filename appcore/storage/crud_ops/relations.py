"""Relationship-oriented read helpers for extension storage."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.orm.interfaces import ORMOption

from appcore.storage.models import (
    Extension,
    ExtensionActivationEvents,
    ExtensionCapabilities,
    ExtensionContributes,
    ExtensionContributesCommands,
    ExtensionScripts,
)


def _resolve_extension(
    db: Session,
    *,
    name: str,
    publisher: str | None = None,
    version: str | None = None,
    loader_options: tuple[ORMOption, ...] = (),
) -> Extension | None:
    stmt = select(Extension).where(Extension.name == name)
    if loader_options:
        stmt = stmt.options(*loader_options)
    if publisher:
        stmt = stmt.where(Extension.publisher == publisher)
    if version:
        stmt = stmt.where(Extension.version == version)

    results = db.scalars(stmt).unique().all()
    if not results:
        return None
    if len(results) > 1:
        raise ValueError(
            "Multiple extensions match this name. "
            "Specify publisher and version for an exact match."
        )
    return results[0]


def get_extension_scripts(
    db: Session, name: str, publisher: str | None = None, version: str | None = None
) -> list[ExtensionScripts] | None:
    extension = _resolve_extension(
        db,
        name=name,
        publisher=publisher,
        version=version,
        loader_options=(selectinload(Extension.scripts),),
    )
    if extension is None:
        return None
    return list(extension.scripts)


def get_extension_activation_events(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionActivationEvents] | None:
    extension = _resolve_extension(
        db,
        name=extension_name,
        publisher=extension_publisher,
        version=extension_version,
        loader_options=(selectinload(Extension.activation_events),),
    )
    if extension is None:
        return None
    return list(extension.activation_events)


def get_extension_capabilities(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> ExtensionCapabilities | None:
    extension = _resolve_extension(
        db,
        name=extension_name,
        publisher=extension_publisher,
        version=extension_version,
        loader_options=(joinedload(Extension.capabilities),),
    )
    if extension is None:
        return None
    return extension.capabilities


def get_extension_contributes_all(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> ExtensionContributes | None:
    extension = _resolve_extension(
        db,
        name=extension_name,
        publisher=extension_publisher,
        version=extension_version,
        loader_options=(
            joinedload(Extension.contributes).options(
                selectinload(ExtensionContributes.keybindings),
                selectinload(ExtensionContributes.menus),
                selectinload(ExtensionContributes.authentication),
                selectinload(ExtensionContributes.terminal),
                selectinload(ExtensionContributes.commands),
            ),
        ),
    )
    if extension is None:
        return None
    return extension.contributes


def get_extension_contributes_commands(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionContributesCommands] | None:
    extension = _resolve_extension(
        db,
        name=extension_name,
        publisher=extension_publisher,
        version=extension_version,
        loader_options=(
            joinedload(Extension.contributes).options(
                selectinload(ExtensionContributes.commands),
            ),
        ),
    )
    if extension is None:
        return None
    if extension.contributes is None:
        return []
    return extension.contributes.commands


__all__ = [
    "get_extension_activation_events",
    "get_extension_capabilities",
    "get_extension_contributes_all",
    "get_extension_contributes_commands",
    "get_extension_scripts",
]
