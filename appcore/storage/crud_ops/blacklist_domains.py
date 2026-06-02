"""CRUD helpers for the blacklist_domains table (operator denylist additions).

Callers should normally go through ``workflows.detection_rules.blacklist_service``
rather than touching this module directly — that layer adds domain validation,
the seed-union, and the in-process matcher-override refresh.
"""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.storage.models import BlacklistDomain


def list_blacklist_domains(db: Session) -> list[str]:
    """Return all operator-added blacklist domains (sorted)."""
    rows = db.scalars(select(BlacklistDomain.domain)).all()
    return sorted(rows)


def add_blacklist_domain_and_commit(
    db: Session, domain: str, added_by: str | None = None
) -> None:
    """Idempotently insert ``domain`` (already normalized) and own the commit."""
    now = time.time()
    stmt = (
        pg_insert(BlacklistDomain)
        .values(domain=domain, added_at=now, added_by=added_by)
        .on_conflict_do_update(
            index_elements=[BlacklistDomain.domain],
            set_={"added_at": now, "added_by": added_by},
        )
    )
    try:
        db.execute(stmt)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


def remove_blacklist_domain_and_commit(db: Session, domain: str) -> bool:
    """Delete ``domain``; return True if a row was removed. Owns the commit."""
    row = db.get(BlacklistDomain, domain)
    if row is None:
        return False
    try:
        db.delete(row)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return True


__all__ = [
    "add_blacklist_domain_and_commit",
    "list_blacklist_domains",
    "remove_blacklist_domain_and_commit",
]
