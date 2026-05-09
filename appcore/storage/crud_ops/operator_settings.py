"""CRUD helpers for the operator_settings key-value table.

The table is a thin store for runtime-tunable values that the analysis
pipeline reads at request time (currently the VSIX hardening thresholds).
Callers should normally go through
``workflows.security_settings.service`` rather than touching this module
directly — that layer adds default-fallback and validation.
"""

from __future__ import annotations

import time
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.storage.models import OperatorSetting


def get_operator_setting(db: Session, key: str) -> OperatorSetting | None:
    return db.scalars(select(OperatorSetting).where(OperatorSetting.key == key)).first()


def list_operator_settings(
    db: Session, keys: Iterable[str] | None = None
) -> list[OperatorSetting]:
    stmt = select(OperatorSetting)
    if keys is not None:
        keys_list = list(keys)
        if not keys_list:
            return []
        stmt = stmt.where(OperatorSetting.key.in_(keys_list))
    return list(db.scalars(stmt).all())


def upsert_operator_setting(
    db: Session,
    key: str,
    value: int,
    updated_by: str | None = None,
) -> OperatorSetting:
    """Insert-or-update a single key. Idempotent; updates timestamp."""
    now = time.time()
    stmt = (
        pg_insert(OperatorSetting)
        .values(key=key, value=value, updated_at=now, updated_by=updated_by)
        .on_conflict_do_update(
            index_elements=[OperatorSetting.key],
            set_={
                "value": value,
                "updated_at": now,
                "updated_by": updated_by,
            },
        )
    )
    db.execute(stmt)
    db.flush()
    row = get_operator_setting(db, key)
    assert row is not None  # we just upserted it
    return row


def upsert_operator_settings_bulk(
    db: Session,
    items: dict[str, int],
    updated_by: str | None = None,
) -> list[OperatorSetting]:
    """Apply a batch of key/value updates atomically (single transaction)."""
    if not items:
        return []
    rows = [
        upsert_operator_setting(db, key=k, value=v, updated_by=updated_by)
        for k, v in items.items()
    ]
    return rows


def upsert_operator_settings_bulk_and_commit(
    db: Session,
    items: dict[str, int],
    updated_by: str | None = None,
) -> list[OperatorSetting]:
    """Apply a batch of key/value updates and own the transaction boundary."""
    try:
        rows = upsert_operator_settings_bulk(db, items=items, updated_by=updated_by)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return rows


__all__ = [
    "get_operator_setting",
    "list_operator_settings",
    "upsert_operator_setting",
    "upsert_operator_settings_bulk",
    "upsert_operator_settings_bulk_and_commit",
]
