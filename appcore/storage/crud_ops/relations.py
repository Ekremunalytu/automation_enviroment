"""Relationship-oriented read helpers for extension storage."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from appcore.storage.models import (
    Extension,
    ExtensionActivationEvents,
    ExtensionCapabilities,
    ExtensionContributes,
    ExtensionContributesCommands,
    ExtensionScripts,
)


def get_extension_scripts(
    db: Session, name: str, publisher: str | None = None, version: str | None = None
) -> list[ExtensionScripts] | None:
    stmt = (
        select(Extension)
        .where(Extension.name == name)
        .options(selectinload(Extension.scripts))
    )
    if publisher:
        stmt = stmt.where(Extension.publisher == publisher)
    if version:
        stmt = stmt.where(Extension.version == version)

    extension = db.scalars(stmt).first()
    if extension is None:
        return None
    return list(extension.scripts)


def get_extension_activation_events(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionActivationEvents] | None:
    stmt = (
        select(Extension)
        .where(Extension.name == extension_name)
        .options(selectinload(Extension.activation_events))
    )
    if extension_publisher:
        stmt = stmt.where(Extension.publisher == extension_publisher)
    if extension_version:
        stmt = stmt.where(Extension.version == extension_version)

    extension = db.scalars(stmt).first()
    if extension is None:
        return None
    return list(extension.activation_events)


def get_extension_capabilities(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> ExtensionCapabilities | None:
    stmt = (
        select(Extension)
        .where(Extension.name == extension_name)
        .options(joinedload(Extension.capabilities))
    )
    if extension_publisher:
        stmt = stmt.where(Extension.publisher == extension_publisher)
    if extension_version:
        stmt = stmt.where(Extension.version == extension_version)

    extension = db.scalars(stmt).first()
    if extension is None:
        return None
    return extension.capabilities


def get_extension_contributes_all(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> ExtensionContributes | None:
    stmt = (
        select(Extension)
        .where(Extension.name == extension_name)
        .options(
            joinedload(Extension.contributes).options(
                selectinload(ExtensionContributes.keybindings),
                selectinload(ExtensionContributes.menus),
                selectinload(ExtensionContributes.authentication),
                selectinload(ExtensionContributes.terminal),
                selectinload(ExtensionContributes.commands),
            )
        )
    )
    if extension_publisher:
        stmt = stmt.where(Extension.publisher == extension_publisher)
    if extension_version:
        stmt = stmt.where(Extension.version == extension_version)

    extension = db.scalars(stmt).first()
    if extension is None:
        return None
    return extension.contributes


def get_extension_contributes_commands(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionContributesCommands] | None:
    stmt = (
        select(Extension)
        .where(Extension.name == extension_name)
        .options(
            joinedload(Extension.contributes).options(
                selectinload(ExtensionContributes.commands),
            )
        )
    )
    if extension_publisher:
        stmt = stmt.where(Extension.publisher == extension_publisher)
    if extension_version:
        stmt = stmt.where(Extension.version == extension_version)

    extension = db.scalars(stmt).first()
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
