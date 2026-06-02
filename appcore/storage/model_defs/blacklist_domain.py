"""Operator-managed blacklist domains (the editable ``blacklist_domains`` field).

Backs the UI-editable denylist surfaced at ``/api/rules/blacklist-domains``. The
effective denylist the detection rules use is the shipped seed
(``packages/analysis_contracts/data/blacklist_domains.txt``) UNION the rows in
this table; this table holds only the operator's own additions, so the shipped
baseline can never be silently dropped by an edit.

Single-tenant by design (ADR 0001) — no auth — so ``added_by`` is informational.
``domain`` is the primary key (already normalized lowercase by the service before
insert), so re-adding an existing domain is an idempotent upsert.
"""

from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from appcore.storage.model_defs.base import Base


class BlacklistDomain(Base):
    __tablename__ = "blacklist_domains"

    domain: Mapped[str] = mapped_column(String, primary_key=True)
    added_at: Mapped[float] = mapped_column(Float, nullable=False)
    added_by: Mapped[str | None] = mapped_column(String, nullable=True)


__all__ = ["BlacklistDomain"]
