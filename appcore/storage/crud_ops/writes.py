"""Write helpers for extension storage."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.contracts.schemas import (
    ExtensionActivationEventsSchema,
    ExtensionCapabilitiesSchema,
    ExtensionContributesSchema,
    ExtensionSchema,
    ExtensionScriptsSchema,
)
from appcore.storage.models import (
    Extension,
    ExtensionActivationEvents,
    ExtensionCapabilities,
    ExtensionContributes,
    ExtensionContributesAuthentication,
    ExtensionContributesCommands,
    ExtensionContributesKeybindings,
    ExtensionContributesMenus,
    ExtensionContributesTerminal,
    ExtensionScripts,
)


def create_extension(
    db: Session,
    extension: ExtensionSchema,
    capabilities: ExtensionCapabilitiesSchema | None = None,
    scripts: list[ExtensionScriptsSchema] | None = None,
    activation_events: list[ExtensionActivationEventsSchema] | None = None,
    contributes: ExtensionContributesSchema | None = None,
) -> Extension:
    db_extension = Extension(**extension.model_dump())

    try:
        db.add(db_extension)
        db.flush()

        if capabilities:
            db.add(
                ExtensionCapabilities(
                    extension_id=db_extension.id,
                    **capabilities.model_dump(),
                )
            )

        if scripts:
            for script in scripts:
                db.add(
                    ExtensionScripts(
                        extension_id=db_extension.id,
                        **script.model_dump(),
                    )
                )

        if activation_events:
            for event in activation_events:
                db.add(
                    ExtensionActivationEvents(
                        extension_id=db_extension.id,
                        **event.model_dump(),
                    )
                )

        if contributes:
            contributes_dict = contributes.model_dump(
                exclude={
                    "keybindings",
                    "menus",
                    "authentication",
                    "terminal",
                    "commands",
                }
            )
            db.add(
                ExtensionContributes(
                    extension_id=db_extension.id,
                    **contributes_dict,
                )
            )
            db.flush()

            for kb in contributes.keybindings:
                db.add(
                    ExtensionContributesKeybindings(
                        contributes_id=db_extension.id,
                        **kb.model_dump(),
                    )
                )
            for menu in contributes.menus:
                db.add(
                    ExtensionContributesMenus(
                        contributes_id=db_extension.id,
                        **menu.model_dump(),
                    )
                )
            for auth in contributes.authentication:
                db.add(
                    ExtensionContributesAuthentication(
                        contributes_id=db_extension.id,
                        **auth.model_dump(),
                    )
                )
            for term in contributes.terminal:
                db.add(
                    ExtensionContributesTerminal(
                        contributes_id=db_extension.id,
                        **term.model_dump(),
                    )
                )
            for cmd in contributes.commands:
                db.add(
                    ExtensionContributesCommands(
                        contributes_id=db_extension.id,
                        **cmd.model_dump(),
                    )
                )

        db.commit()
        db.refresh(db_extension)
        return db_extension
    except IntegrityError:
        db.rollback()
        raise ValueError("Extension already exists") from None
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc


def delete_extension(
    db: Session, name: str, publisher: str | None = None, version: str | None = None
) -> bool:
    stmt = select(Extension).where(Extension.name == name)
    if publisher:
        stmt = stmt.where(Extension.publisher == publisher)
    if version:
        stmt = stmt.where(Extension.version == version)

    results = db.scalars(stmt).all()
    if not results:
        return False
    if len(results) > 1:
        raise ValueError(
            "Multiple extensions match this name. "
            "Specify publisher and version to delete the correct one."
        )

    db.delete(results[0])
    db.commit()
    return True


__all__ = ["create_extension", "delete_extension"]
