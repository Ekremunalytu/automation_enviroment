"""ES-1b (ADR 0016, Static Analysis Pre-Check): programmatic alembic round-trip
for the ``static_report_path`` migration (revision ``f4b9d2e7a1c3``).

The migration is additive — a single nullable ``static_report_path`` column on
``analysis_jobs`` — and unlike the W13-3 ``cancelling`` migration
(``c8a2d4e91f5b``) it does not touch the partial unique index or perform any
data motion. This test pins the round-trip: upgrade head adds the column; a row
carrying a terminal ``rejected_static`` status and a ``static_report_path``
value survives a downgrade to the prior head (``e7c0a8f3b9d2``) with only the
column dropped; upgrade head restores it.

Postgres-only (mirrors the sibling
``test_alembic_cancelling_migration.py``). Uses the ``fresh_alembic_engine``
fixture (``tests/platform/storage/conftest.py``): a throwaway database per test,
dropped on teardown, so a failed DDL cannot poison sibling tests' schema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import inspect, text

pytestmark = pytest.mark.requires_db


_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"

# The revision immediately below f4b9d2e7a1c3 (the pre-ES-1b head). Pinned by
# name rather than ``-1`` so later head migrations do not shift the target.
_PRIOR_HEAD = "e7c0a8f3b9d2"


def test_migration_f4b9d2e7a1c3_round_trip_static_report_path(
    fresh_alembic_engine: tuple[Any, str],
) -> None:
    """``upgrade head → INSERT rejected_static row → downgrade → upgrade`` round-trips.

    The migration body in
    ``alembic/versions/f4b9d2e7a1c3_add_static_report_path_to_analysis_jobs.py``
    only adds (upgrade) / drops (downgrade) the nullable ``static_report_path``
    column. This test inserts a terminal ``rejected_static`` row with the column
    populated and asserts: column present after upgrade, column dropped and row
    preserved after downgrade (no data motion), and column re-added after a
    second upgrade.
    """
    from alembic import command
    from alembic.config import Config

    engine, fresh_url = fresh_alembic_engine
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", fresh_url)
    # Suppress alembic env.py's fileConfig() call (see fresh_alembic_engine).
    cfg.config_file_name = None

    test_job_id = "test-migration-roundtrip-f4b9d2e7a1c3"

    # The fixture already ran ``upgrade head``; the column must exist. Insert a
    # terminal rejected_static row carrying a static_report_path value. Only the
    # NOT-NULL columns plus static_report_path are listed; the rest default NULL.
    with engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "static_report_path" in columns, (
            "upgrade head must add the static_report_path column"
        )
        conn.execute(
            text(
                """
                INSERT INTO analysis_jobs (
                    job_id, owner_boot_id, owner_pid, status,
                    publisher, name, version, steps, message,
                    static_report_path, created_at, updated_at
                ) VALUES (
                    :jid, 'boot', 1, 'rejected_static',
                    'pub', 'name', '1.0.0', '[]'::jsonb, 'static-gate blocked',
                    'static-report.json',
                    EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW())
                )
                """
            ),
            {"jid": test_job_id},
        )

    # Downgrade to the pre-ES-1b head: drops the column; the row is otherwise
    # untouched (the migration performs no data motion).
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, _PRIOR_HEAD)

    with engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "static_report_path" not in columns, (
            "downgrade must drop the static_report_path column"
        )
        row = conn.execute(
            text("SELECT status FROM analysis_jobs WHERE job_id = :jid"),
            {"jid": test_job_id},
        ).first()
        assert row is not None, (
            "row vanished during downgrade (no data motion expected)"
        )
        assert row.status == "rejected_static", (
            "downgrade must not alter the rejected_static row's status"
        )

    # Upgrade head restores the column.
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

    with engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "static_report_path" in columns, (
            "upgrade head must re-add the static_report_path column"
        )
