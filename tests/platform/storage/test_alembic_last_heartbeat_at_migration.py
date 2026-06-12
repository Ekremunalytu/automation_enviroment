"""S2 (W23 B3, same-boot wedged-job recovery): programmatic alembic round-trip
for the ``last_heartbeat_at`` migration (revision ``c3f8a1d7e9b2``).

The migration is additive — a single nullable ``last_heartbeat_at`` column on
``analysis_jobs`` — and like the ES-1b ``static_report_path`` migration
(``f4b9d2e7a1c3``) it does not touch the partial unique index or perform any
data motion. This test pins the round-trip: upgrade head adds the column; a
``running`` row carrying a ``last_heartbeat_at`` value survives a downgrade to
the prior head (``b3d9f1c2e7a4``) with only the column dropped; upgrade head
restores it.

Postgres-only (mirrors the sibling
``test_alembic_static_report_path_migration.py``). Uses the
``fresh_alembic_engine`` fixture (``tests/platform/storage/conftest.py``): a
throwaway database per test, dropped on teardown, so a failed DDL cannot poison
sibling tests' schema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import inspect, text

pytestmark = pytest.mark.requires_db


_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"

# The revision immediately below c3f8a1d7e9b2 (the pre-S2 head). Pinned by name
# rather than ``-1`` so later head migrations do not shift the target.
_PRIOR_HEAD = "b3d9f1c2e7a4"


def test_migration_c3f8a1d7e9b2_round_trip_last_heartbeat_at(
    fresh_alembic_engine: tuple[Any, str],
) -> None:
    """``upgrade head → INSERT running row → downgrade → upgrade`` round-trips.

    The migration body in
    ``alembic/versions/c3f8a1d7e9b2_add_last_heartbeat_at_to_analysis_jobs.py``
    only adds (upgrade) / drops (downgrade) the nullable ``last_heartbeat_at``
    column. This test inserts a ``running`` row with the column populated and
    asserts: column present after upgrade, column dropped and row preserved
    after downgrade (no data motion), and column re-added after a second
    upgrade.
    """
    from alembic import command
    from alembic.config import Config

    engine, fresh_url = fresh_alembic_engine
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", fresh_url)
    # Suppress alembic env.py's fileConfig() call (see fresh_alembic_engine).
    cfg.config_file_name = None

    test_job_id = "test-migration-roundtrip-c3f8a1d7e9b2"

    # The fixture already ran ``upgrade head``; the column must exist. Insert a
    # running row carrying a last_heartbeat_at value. Only the NOT-NULL columns
    # plus last_heartbeat_at are listed; the rest default NULL.
    with engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "last_heartbeat_at" in columns, (
            "upgrade head must add the last_heartbeat_at column"
        )
        conn.execute(
            text(
                """
                INSERT INTO analysis_jobs (
                    job_id, owner_boot_id, owner_pid, status,
                    publisher, name, version, steps, message,
                    last_heartbeat_at, created_at, updated_at
                ) VALUES (
                    :jid, 'boot', 1, 'running',
                    'pub', 'name', '1.0.0', '[]'::jsonb, 'running',
                    1234567890.0,
                    EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW())
                )
                """
            ),
            {"jid": test_job_id},
        )

    # Downgrade to the pre-S2 head: drops the column; the row is otherwise
    # untouched (the migration performs no data motion).
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, _PRIOR_HEAD)

    with engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "last_heartbeat_at" not in columns, (
            "downgrade must drop the last_heartbeat_at column"
        )
        row = conn.execute(
            text("SELECT status FROM analysis_jobs WHERE job_id = :jid"),
            {"jid": test_job_id},
        ).first()
        assert row is not None, (
            "row vanished during downgrade (no data motion expected)"
        )
        assert row.status == "running", (
            "downgrade must not alter the running row's status"
        )

    # Upgrade head restores the column.
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

    with engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "last_heartbeat_at" in columns, (
            "upgrade head must re-add the last_heartbeat_at column"
        )
