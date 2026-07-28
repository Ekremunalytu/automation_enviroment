"""Operator-tunable runtime settings (key-value pairs).

This table backs operator-facing controls read at request time — the VSIX
hardening thresholds and integer-encoded executor preferences.

Design notes (2026-05-09):
- Single integer column keeps the schema small while covering thresholds and
  boolean flags encoded as 0/1. If a future setting needs strings or floats
  we'd add a typed sibling column rather than overloading ``value``.
- ``key`` is the primary key; the canonical key list lives in
  ``workflows/security_settings/defaults.py`` so seed and validation
  share a single source of truth.
- ``updated_by`` is captured from the request payload (operator name).
  The table is single-tenant by design (ADR 0001) — no auth — so the
  string is informational, not authoritative.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from appcore.storage.model_defs.base import Base


class OperatorSetting(Base):
    __tablename__ = "operator_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[float] = mapped_column(Float, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)


__all__ = ["OperatorSetting"]
