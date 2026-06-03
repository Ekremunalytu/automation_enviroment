"""Programmatic alembic round-trip for the ``blacklist_domains`` migration
(revision ``b3d9f1c2e7a4``).

The migration is additive — a single new ``blacklist_domains`` table backing the
operator-editable denylist — and, like the sibling ``static_report_path``
migration (``f4b9d2e7a1c3``), touches no existing table or index. This test pins
the round-trip: upgrade head creates the table; an operator row inserted into it
is dropped together with the table by a downgrade to the prior head
(``f4b9d2e7a1c3``); a second upgrade re-creates the (empty) table.

Postgres-only (mirrors ``test_alembic_static_report_path_migration.py``). Uses the
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

# The revision immediately below b3d9f1c2e7a4 (the static_report_path head).
# Pinned by name rather than ``-1`` so later head migrations do not shift it.
_PRIOR_HEAD = "f4b9d2e7a1c3"


def test_migration_b3d9f1c2e7a4_round_trip_blacklist_domains(
    fresh_alembic_engine: tuple[Any, str],
) -> None:
    """``upgrade head → INSERT operator row → downgrade → upgrade`` round-trips.

    The migration body in
    ``alembic/versions/b3d9f1c2e7a4_add_blacklist_domains_table.py`` only creates
    (upgrade) / drops (downgrade) the ``blacklist_domains`` table. This test
    inserts an operator row and asserts: table present after upgrade, table (and
    its rows) dropped after downgrade with the sibling ``analysis_jobs`` table
    untouched, and an empty table re-created after a second upgrade.
    """
    from alembic import command
    from alembic.config import Config

    engine, fresh_url = fresh_alembic_engine
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", fresh_url)
    # Suppress alembic env.py's fileConfig() call (see fresh_alembic_engine).
    cfg.config_file_name = None

    # The fixture already ran ``upgrade head``; the table must exist. Insert an
    # operator-added row carrying the full column set.
    with engine.begin() as conn:
        insp = inspect(conn)
        assert "blacklist_domains" in insp.get_table_names(), (
            "upgrade head must create the blacklist_domains table"
        )
        conn.execute(
            text(
                """
                INSERT INTO blacklist_domains (domain, added_at, added_by)
                VALUES (:domain, EXTRACT(EPOCH FROM NOW()), :added_by)
                """
            ),
            {"domain": "evil.example", "added_by": "operator"},
        )
        count = conn.execute(text("SELECT COUNT(*) FROM blacklist_domains")).scalar()
        assert count == 1, "inserted operator row must be present after upgrade"

    # Downgrade to the pre-b3d9f1c2e7a4 head: drops the table (and its rows).
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, _PRIOR_HEAD)

    with engine.begin() as conn:
        insp = inspect(conn)
        tables = set(insp.get_table_names())
        assert "blacklist_domains" not in tables, (
            "downgrade must drop the blacklist_domains table"
        )
        assert "analysis_jobs" in tables, (
            "downgrade must not touch the sibling analysis_jobs table"
        )

    # Upgrade head re-creates the table, empty (downgrade dropped the data).
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

    with engine.begin() as conn:
        insp = inspect(conn)
        assert "blacklist_domains" in insp.get_table_names(), (
            "upgrade head must re-create the blacklist_domains table"
        )
        count = conn.execute(text("SELECT COUNT(*) FROM blacklist_domains")).scalar()
        assert count == 0, "re-created table must start empty"
