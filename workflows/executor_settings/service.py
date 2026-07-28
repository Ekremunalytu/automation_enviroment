"""Persistence service for operator-tunable executor preferences."""

from __future__ import annotations

from sqlalchemy.orm import Session

from appcore.storage.crud import (
    get_operator_setting,
    upsert_operator_settings_bulk_and_commit,
)
from workflows.executor_settings.defaults import (
    DYNAMIC_ANALYSIS_ENABLED_DEFAULT,
    DYNAMIC_ANALYSIS_ENABLED_KEY,
)


def load_dynamic_analysis_enabled(db: Session) -> bool:
    """Return the persisted preference, failing closed to the default."""
    row = get_operator_setting(db, DYNAMIC_ANALYSIS_ENABLED_KEY)
    if row is None:
        return DYNAMIC_ANALYSIS_ENABLED_DEFAULT
    return row.value == 1


def save_dynamic_analysis_enabled(
    db: Session,
    enabled: bool,
    updated_by: str | None = None,
) -> bool:
    """Persist a validated boolean as the table's canonical 0/1 value."""
    if not isinstance(enabled, bool):
        raise TypeError("dynamic_analysis_enabled must be a boolean")

    upsert_operator_settings_bulk_and_commit(
        db,
        items={DYNAMIC_ANALYSIS_ENABLED_KEY: int(enabled)},
        updated_by=updated_by,
    )
    return load_dynamic_analysis_enabled(db)


__all__ = [
    "load_dynamic_analysis_enabled",
    "save_dynamic_analysis_enabled",
]
