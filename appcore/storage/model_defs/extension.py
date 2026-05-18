"""Core extension metadata models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from appcore.storage.model_defs.base import Base, capability_support_enum

if TYPE_CHECKING:
    from appcore.storage.model_defs.contributes import ExtensionContributes


class Extension(Base):
    __tablename__ = "extensions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String, nullable=False, index=True)
    publisher: Mapped[str] = mapped_column(String, nullable=False, index=True)
    engines: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    license: Mapped[str | None] = mapped_column(String, nullable=True)
    displayName: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    galleryBanner: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    preview: Mapped[bool | None] = mapped_column(nullable=True)
    badges: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    qna: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    sponsor: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    pricing: Mapped[str | None] = mapped_column(String, nullable=True)
    main: Mapped[str | None] = mapped_column(String, nullable=True)
    browser: Mapped[str | None] = mapped_column(String, nullable=True)
    dependencies: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    devDependencies: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    extensionPack: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    extensionDependencies: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    extensionKind: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    npm_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    extra_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    capabilities: Mapped[ExtensionCapabilities | None] = relationship(
        "ExtensionCapabilities",
        back_populates="extension",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )
    scripts: Mapped[list[ExtensionScripts]] = relationship(
        "ExtensionScripts",
        back_populates="extension",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    activation_events: Mapped[list[ExtensionActivationEvents]] = relationship(
        "ExtensionActivationEvents",
        back_populates="extension",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    contributes: Mapped[ExtensionContributes | None] = relationship(
        "ExtensionContributes",
        back_populates="extension",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "publisher", "name", "version", name="uix_publisher_name_version"
        ),
        Index(
            "ix_extensions_publisher_name_version",
            "publisher",
            "name",
            "version",
        ),
        Index("ix_extensions_publisher_name", "publisher", "name"),
    )


class ExtensionCapabilities(Base):
    __tablename__ = "extension_capabilities"

    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    untrusted_supported: Mapped[str | None] = mapped_column(
        capability_support_enum, nullable=True
    )
    untrusted_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    untrusted_restricted_configurations: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    virtual_supported: Mapped[str | None] = mapped_column(
        capability_support_enum, nullable=True
    )
    virtual_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    extension: Mapped[Extension] = relationship(
        "Extension",
        back_populates="capabilities",
    )


class ExtensionScripts(Base):
    __tablename__ = "extension_scripts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    script_name: Mapped[str] = mapped_column(String, nullable=False)
    script_command: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    extension: Mapped[Extension] = relationship("Extension", back_populates="scripts")


class ExtensionActivationEvents(Base):
    __tablename__ = "extension_activation_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_value: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    extension: Mapped[Extension] = relationship(
        "Extension", back_populates="activation_events"
    )


__all__ = [
    "Extension",
    "ExtensionActivationEvents",
    "ExtensionCapabilities",
    "ExtensionScripts",
]
