"""Contribution-related ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appcore.storage.model_defs.base import Base

if TYPE_CHECKING:
    from appcore.storage.model_defs.extension import Extension


class ExtensionContributes(Base):
    __tablename__ = "extension_contributes"

    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    configuration: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    debuggers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    walkthroughs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    grammars: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    colors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    icons: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    snippets: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    views: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    viewsContainers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    languages: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    themes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    iconThemes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    productIconThemes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    jsonValidation: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    problemMatchers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    problemPatterns: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    taskDefinitions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    customEditors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    submenus: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    viewsWelcome: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    breakpoints: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    configurationDefaults: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    typescriptServerPlugins: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    extension: Mapped[Extension] = relationship(
        "Extension", back_populates="contributes"
    )
    keybindings: Mapped[list[ExtensionContributesKeybindings]] = relationship(
        "ExtensionContributesKeybindings",
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    menus: Mapped[list[ExtensionContributesMenus]] = relationship(
        "ExtensionContributesMenus",
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    authentication: Mapped[list[ExtensionContributesAuthentication]] = relationship(
        "ExtensionContributesAuthentication",
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    terminal: Mapped[list[ExtensionContributesTerminal]] = relationship(
        "ExtensionContributesTerminal",
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    commands: Mapped[list[ExtensionContributesCommands]] = relationship(
        "ExtensionContributesCommands",
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class ExtensionContributesCommands(Base):
    __tablename__ = "extension_contributes_commands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    command_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    icon: Mapped[dict[str, Any] | str | None] = mapped_column(JSONB, nullable=True)
    when: Mapped[str | None] = mapped_column(Text, nullable=True)

    contributes: Mapped[ExtensionContributes] = relationship(
        "ExtensionContributes", back_populates="commands"
    )


class ExtensionContributesKeybindings(Base):
    __tablename__ = "extension_contributes_keybindings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str] = mapped_column(String, nullable=False)
    when: Mapped[str | None] = mapped_column(Text, nullable=True)
    mac: Mapped[str | None] = mapped_column(String, nullable=True)
    linux: Mapped[str | None] = mapped_column(String, nullable=True)
    win: Mapped[str | None] = mapped_column(String, nullable=True)
    args: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    contributes: Mapped[ExtensionContributes] = relationship(
        "ExtensionContributes", back_populates="keybindings"
    )


class ExtensionContributesMenus(Base):
    __tablename__ = "extension_contributes_menus"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_location: Mapped[str] = mapped_column(String, nullable=False, index=True)
    command: Mapped[str | None] = mapped_column(String, nullable=True)
    submenu: Mapped[str | None] = mapped_column(String, nullable=True)
    when: Mapped[str | None] = mapped_column(Text, nullable=True)
    group: Mapped[str | None] = mapped_column(String, nullable=True)
    alt: Mapped[str | None] = mapped_column(String, nullable=True)

    contributes: Mapped[ExtensionContributes] = relationship(
        "ExtensionContributes", back_populates="menus"
    )


class ExtensionContributesAuthentication(Base):
    __tablename__ = "extension_contributes_authentication"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    auth_id: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)

    contributes: Mapped[ExtensionContributes] = relationship(
        "ExtensionContributes", back_populates="authentication"
    )


class ExtensionContributesTerminal(Base):
    __tablename__ = "extension_contributes_terminal"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)

    contributes: Mapped[ExtensionContributes] = relationship(
        "ExtensionContributes", back_populates="terminal"
    )


__all__ = [
    "ExtensionContributes",
    "ExtensionContributesAuthentication",
    "ExtensionContributesCommands",
    "ExtensionContributesKeybindings",
    "ExtensionContributesMenus",
    "ExtensionContributesTerminal",
]
