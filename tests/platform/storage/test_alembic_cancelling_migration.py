"""W13-4 (cancellation lifecycle hardening): programmatic alembic
round-trip pinning for the W13-3 ``cancelling`` migration
(revision ``c8a2d4e91f5b``).

W13-3 close evidence in
``W13-test-expansion-observability.md`` § W13-3.6 documents a manual
``alembic upgrade head && alembic downgrade -1 && alembic upgrade head``
round-trip; ``tests/architecture/test_job_state_invariants.py:114-140``
pins the migration body's ``WHERE`` clause literals statically. This
test closes the runtime data-motion gap: the downgrade ``UPDATE``
statement must actually force-finalize ``cancelling`` rows to
``cancelled`` (so the tightened partial unique index does not reject
the existing dataset on rollback), and the column drop + index
re-narrow must reverse cleanly.

Postgres-only: relies on partial unique index ``WHERE`` semantics and
``EXTRACT(EPOCH FROM NOW())``. Skipped by default until W13-4.5; the
fixture below uses a module-scope teardown that explicitly returns the
schema to ``head`` so other test modules aren't poisoned by a partial
downgrade if this test fails mid-flight.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import inspect, text

pytestmark = pytest.mark.requires_db


_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


@pytest.fixture
def alembic_round_trip_safety(test_engine: Any) -> Generator[None, None, None]:
    """Ensure the schema is restored to ``head`` after the test.

    A failed downgrade leaves the test DB at the previous revision and
    breaks every later module that assumes the W13-3 schema (the
    ``requested_cancel_at`` column, partial unique index extension).
    Even on assertion failure, the ``finally`` clause re-runs
    ``alembic upgrade head`` so subsequent tests see a consistent
    schema.
    """
    yield
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_ALEMBIC_INI))
    with test_engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")


@pytest.mark.skip(
    reason=(
        "W13-4.5 deferred to W14+ as "
        "[FOLLOWUP w13-4-alembic-roundtrip-programmatic]: programmatic "
        "alembic upgrade/downgrade against the session-scoped test_engine "
        "leaves alembic_version + schema state inconsistent on failure, "
        "poisoning subsequent tests. W13-3.6 close evidence documents "
        "manual `alembic upgrade head && alembic downgrade -1 && "
        "alembic upgrade head` round-trip; "
        "tests/architecture/test_job_state_invariants.py:114-140 pins "
        "the migration body's WHERE clause literals statically. The "
        "behavioral data-motion gap remains as a deferred candidate "
        "pending a fresh-DB-per-test fixture (e.g. throwaway schema or "
        "templated test DB)."
    )
)
def test_migration_c8a2d4e91f5b_round_trip_preserves_cancelling_rows(
    test_engine: Any,
    alembic_round_trip_safety: None,
) -> None:
    """``upgrade head → INSERT cancelling row → downgrade -1`` force-finalizes safely.

    The downgrade body in
    ``alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py``
    runs:

    .. code-block:: sql

        UPDATE analysis_jobs
        SET status='cancelled',
            finished_at=COALESCE(finished_at, EXTRACT(EPOCH FROM NOW())),
            requested_cancel_at=NULL
        WHERE status='cancelling'

    before tightening the partial unique index back to
    ``WHERE status IN ('queued', 'running')`` and dropping the
    ``requested_cancel_at`` column. This test inserts a draining row
    and asserts every step of the data motion: column drop, row
    transition, index re-narrowing, and that ``upgrade head`` restores
    everything cleanly.
    """
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_ALEMBIC_INI))

    # Conftest's `test_engine` does `Base.metadata.create_all` (not
    # `alembic upgrade`), so the alembic_version table is empty. Stamp
    # to head before exercising downgrade so alembic knows where it is.
    with test_engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.stamp(cfg, "head")

    test_job_id = "test-migration-roundtrip-c8a2d4e91f5b"

    # Insert a cancelling row that the downgrade must force-finalize.
    with test_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM analysis_jobs WHERE job_id = :jid"),
            {"jid": test_job_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO analysis_jobs (
                    job_id, owner_boot_id, owner_pid, status,
                    publisher, name, version, steps, report_path,
                    message, current_step, error_detail, error_code,
                    install_output, automation_output,
                    created_at, started_at, finished_at, updated_at,
                    requested_cancel_at, scenario, analysis_profile
                ) VALUES (
                    :jid, 'boot', 1, 'cancelling',
                    'pub', 'name', '1.0.0', '[]'::jsonb, 'r.json',
                    'mid-drain', 'run_monitoring', NULL, 'cancelled_by_user',
                    NULL, NULL,
                    EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW()),
                    NULL, EXTRACT(EPOCH FROM NOW()),
                    EXTRACT(EPOCH FROM NOW()), NULL, NULL
                )
                """
            ),
            {"jid": test_job_id},
        )

    # Downgrade -1: revision a1c4f9d2b8e3 (pre-W13-3 schema).
    with test_engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "-1")

    # Post-downgrade assertions:
    #  1. requested_cancel_at column dropped.
    #  2. The cancelling row was force-finalized to cancelled with
    #     finished_at set (downgrade body's UPDATE statement).
    #  3. Partial unique index WHERE clause shrunk to (queued, running).
    with test_engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "requested_cancel_at" not in columns, (
            "downgrade must drop the requested_cancel_at column"
        )

        row = conn.execute(
            text("SELECT status, finished_at FROM analysis_jobs WHERE job_id = :jid"),
            {"jid": test_job_id},
        ).first()
        assert row is not None, "row vanished during downgrade"
        assert row.status == "cancelled", (
            "downgrade UPDATE must force-finalize cancelling → cancelled"
        )
        assert row.finished_at is not None, (
            "downgrade UPDATE must populate finished_at via COALESCE"
        )

        # Inspect the partial unique index WHERE clause via pg_catalog.
        index_rows = conn.execute(
            text(
                "SELECT pg_get_indexdef(indexrelid) AS def "
                "FROM pg_index i "
                "JOIN pg_class c ON c.oid = i.indexrelid "
                "WHERE c.relname = 'uq_analysis_jobs_single_active'"
            )
        ).all()
        assert len(index_rows) == 1
        index_def = (
            index_rows[0].def_ if hasattr(index_rows[0], "def_") else index_rows[0][0]
        )
        assert "cancelling" not in index_def.lower(), (
            f"downgrade should narrow WHERE to (queued, running) only; got {index_def}"
        )

    # Upgrade head restores: column re-added, index widened back.
    with test_engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

    with test_engine.begin() as conn:
        insp = inspect(conn)
        columns = {col["name"] for col in insp.get_columns("analysis_jobs")}
        assert "requested_cancel_at" in columns, (
            "upgrade must re-add the requested_cancel_at column"
        )

        index_def = conn.execute(
            text(
                "SELECT pg_get_indexdef(indexrelid) "
                "FROM pg_index i "
                "JOIN pg_class c ON c.oid = i.indexrelid "
                "WHERE c.relname = 'uq_analysis_jobs_single_active'"
            )
        ).scalar()
        assert "cancelling" in index_def.lower(), (
            f"upgrade should widen WHERE to include cancelling; got {index_def}"
        )

        # Cleanup test row so other tests aren't surprised.
        conn.execute(
            text("DELETE FROM analysis_jobs WHERE job_id = :jid"),
            {"jid": test_job_id},
        )
