"""add cancelling status to analysis_jobs (W13-3 / Codex H4)

Revision ID: c8a2d4e91f5b
Revises: a1c4f9d2b8e3
Create Date: 2026-05-10 00:00:00.000000

W13-3 (Codex H4 cancel concurrent race) — `cancel_analysis_job` previously
dropped a `running` job straight to terminal `cancelled`, releasing the
single-active-job lock while the worker thread still drove the shared
executor + `/results/`. The fix introduces a non-terminal `cancelling`
state and a `requested_cancel_at` audit column:

- `cancelling` joins the partial unique index `WHERE` clause so
  `reserve_job` blocks until `finalize_cancelled_analysis_job` (added in
  W13-3.4 CRUD work) transitions the row to terminal `cancelled`.
- `requested_cancel_at` records when the drain was signalled (null for
  jobs that complete normally; set on `running -> cancelling`).

Reversible: downgrade force-finalizes any in-flight `cancelling` rows to
`cancelled` before tightening the partial unique index back to
`('queued', 'running')`. PoC ships with at most one active row at a time,
so the data motion is bounded.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8a2d4e91f5b"
down_revision: str | Sequence[str] | None = "a1c4f9d2b8e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP INDEX uq_analysis_jobs_single_active")
    op.execute(
        "CREATE UNIQUE INDEX uq_analysis_jobs_single_active "
        "ON analysis_jobs ((1)) "
        "WHERE status IN ('queued', 'running', 'cancelling')"
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("requested_cancel_at", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema.

    Force-finalize any in-flight `cancelling` rows to `cancelled` so the
    tightened partial unique index does not reject the existing dataset;
    a row stuck in `cancelling` after rollback would surface as a worker
    that crashed mid-drain (`recover_interrupted_jobs` would otherwise
    catch it on the next boot, but downgrade can run with the API down).
    """
    op.execute(
        "UPDATE analysis_jobs "
        "SET status='cancelled', "
        "    finished_at=COALESCE(finished_at, EXTRACT(EPOCH FROM NOW())), "
        "    requested_cancel_at=NULL "
        "WHERE status='cancelling'"
    )
    op.drop_column("analysis_jobs", "requested_cancel_at")
    op.execute("DROP INDEX uq_analysis_jobs_single_active")
    op.execute(
        "CREATE UNIQUE INDEX uq_analysis_jobs_single_active "
        "ON analysis_jobs ((1)) "
        "WHERE status IN ('queued', 'running')"
    )
