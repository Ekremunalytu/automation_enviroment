"""Shared SQLAlchemy base objects."""

from __future__ import annotations

from sqlalchemy import Enum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for ExTrace ORM models."""


capability_support_enum = Enum(
    "supported",
    "not_supported",
    "limited",
    name="capability_support_state",
)


__all__ = ["Base", "capability_support_enum"]
