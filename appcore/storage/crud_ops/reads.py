"""Read/query helpers for extension storage."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, defer, joinedload, load_only, selectinload

from appcore.storage.models import (
    Extension,
    ExtensionContributes,
)


def get_extension_by_id(db: Session, extension_id: int) -> Extension | None:
    stmt = select(Extension).where(Extension.id == extension_id)
    return db.scalars(stmt).first()


def search_extension_by_name(
    db: Session, name: str, publisher: str | None = None, version: str | None = None
) -> Extension | None:
    stmt = (
        select(Extension)
        .options(
            joinedload(Extension.capabilities),
            selectinload(Extension.scripts),
            selectinload(Extension.activation_events),
            joinedload(Extension.contributes).options(
                selectinload(ExtensionContributes.keybindings),
                selectinload(ExtensionContributes.menus),
                selectinload(ExtensionContributes.authentication),
                selectinload(ExtensionContributes.terminal),
                selectinload(ExtensionContributes.commands),
            ),
        )
        .where(Extension.name == name)
    )
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


def get_extensions_all_info(
    db: Session, skip: int = 0, limit: int | None = None
) -> list[Extension]:
    stmt = select(Extension).options(
        defer(Extension.markdown),
        joinedload(Extension.capabilities),
        selectinload(Extension.scripts),
        selectinload(Extension.activation_events),
        joinedload(Extension.contributes).options(
            selectinload(ExtensionContributes.keybindings),
            selectinload(ExtensionContributes.menus),
            selectinload(ExtensionContributes.authentication),
            selectinload(ExtensionContributes.terminal),
            selectinload(ExtensionContributes.commands),
        ),
    )
    if skip > 0:
        stmt = stmt.offset(skip)
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).unique().all())


def get_db_extensions_base_info(db: Session) -> list[Extension]:
    stmt = select(Extension).options(
        load_only(
            Extension.id,
            Extension.name,
            Extension.version,
            Extension.publisher,
            Extension.description,
            Extension.icon,
        )
    )
    return list(db.scalars(stmt).all())


__all__ = [
    "get_db_extensions_base_info",
    "get_extension_by_id",
    "get_extensions_all_info",
    "search_extension_by_name",
]
