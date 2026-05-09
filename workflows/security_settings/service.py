"""Service layer for operator-tunable security thresholds.

- ``load_vsix_thresholds(db)``: returns the full threshold dict, falling
  back to ``VSIX_THRESHOLD_DEFAULTS`` for any key not yet persisted. This
  is the function the marketplace client calls per request.
- ``save_vsix_thresholds(db, values, updated_by)``: validates and upserts
  a partial dict. Raises ``SecuritySettingValidationError`` on bad input
  before touching the DB.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from appcore.storage.crud import (
    list_operator_settings,
    upsert_operator_settings_bulk,
)
from workflows.security_settings.defaults import (
    THRESHOLD_BOUNDS,
    VSIX_THRESHOLD_DEFAULTS,
    VSIX_THRESHOLD_KEYS,
)


class SecuritySettingValidationError(ValueError):
    """Raised when operator-supplied threshold values violate bounds."""

    def __init__(self, key: str, value: object, reason: str) -> None:
        super().__init__(f"{key}={value!r}: {reason}")
        self.key = key
        self.value = value
        self.reason = reason


def load_vsix_thresholds(db: Session) -> dict[str, int]:
    """Return all VSIX thresholds; fall back to defaults for missing keys.

    The DB is the operator-tunable layer; defaults are the safety net for
    a fresh install or a partially-migrated state. The merge order means
    operator-set values always win over defaults for keys that exist in
    the DB.
    """
    persisted = {
        row.key: row.value
        for row in list_operator_settings(db, keys=VSIX_THRESHOLD_KEYS)
    }
    merged = dict(VSIX_THRESHOLD_DEFAULTS)
    merged.update(persisted)
    return merged


def save_vsix_thresholds(
    db: Session,
    values: dict[str, int],
    updated_by: str | None = None,
) -> dict[str, int]:
    """Validate and upsert a partial threshold dict.

    Returns the merged dict (defaults + persisted) after the write so the
    caller can echo back the new effective state without a second query.
    """
    if not values:
        return load_vsix_thresholds(db)

    # Validate every supplied value before any DB write.
    for key, value in values.items():
        if key not in VSIX_THRESHOLD_KEYS:
            raise SecuritySettingValidationError(
                key, value, f"unknown threshold key (valid: {VSIX_THRESHOLD_KEYS})"
            )
        if not isinstance(value, int) or isinstance(value, bool):
            raise SecuritySettingValidationError(
                key, value, "value must be a non-boolean integer"
            )
        bounds = THRESHOLD_BOUNDS[key]
        if value < bounds.min_value or value > bounds.max_value:
            raise SecuritySettingValidationError(
                key,
                value,
                f"out of allowed range [{bounds.min_value}, {bounds.max_value}]",
            )

    upsert_operator_settings_bulk(db, items=values, updated_by=updated_by)
    db.commit()
    return load_vsix_thresholds(db)


__all__ = [
    "SecuritySettingValidationError",
    "load_vsix_thresholds",
    "save_vsix_thresholds",
]
