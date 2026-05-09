"""CRUD coverage for the operator_settings key/value table.

Pins the transaction-owning helper introduced when
[FOLLOWUP security-settings-commit-ownership] moved commit ownership out
of the workflow service: the helper must commit on the success path,
rollback + re-raise on SQLAlchemyError, and treat an empty payload as a
no-op write (still safe to call with no items).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.storage.crud import upsert_operator_settings_bulk_and_commit
from appcore.storage.crud_ops.operator_settings import (
    list_operator_settings,
)


@pytest.mark.requires_db
def test_bulk_and_commit_persists_rows_across_session_boundary(
    db_session: Session,
) -> None:
    items = {"vsix_max_file_count": 75_000, "vsix_max_uncompressed_size": 250_000_000}

    rows = upsert_operator_settings_bulk_and_commit(
        db_session, items=items, updated_by="operator-test"
    )

    assert {row.key for row in rows} == set(items.keys())
    persisted = {row.key: row.value for row in list_operator_settings(db_session)}
    for key, value in items.items():
        assert persisted[key] == value


@pytest.mark.requires_db
def test_bulk_and_commit_with_empty_dict_is_safe_noop(db_session: Session) -> None:
    rows = upsert_operator_settings_bulk_and_commit(db_session, items={})
    assert rows == []


def test_bulk_and_commit_rolls_back_when_commit_raises() -> None:
    """Pin transaction discipline: SQLAlchemyError on commit triggers rollback + re-raise."""
    session = MagicMock(spec=Session)
    session.commit.side_effect = SQLAlchemyError("simulated commit failure")

    with pytest.raises(SQLAlchemyError, match="simulated commit failure"):
        upsert_operator_settings_bulk_and_commit(
            session, items={"vsix_max_file_count": 1}
        )

    session.commit.assert_called_once()
    session.rollback.assert_called_once()
