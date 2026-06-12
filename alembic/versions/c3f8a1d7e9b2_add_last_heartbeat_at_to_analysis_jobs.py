"""add last_heartbeat_at to analysis_jobs (S2 / W23 B3 same-boot wedged-job recovery)

Revision ID: c3f8a1d7e9b2
Revises: b3d9f1c2e7a4
Create Date: 2026-06-12 00:00:00.000000

S2 (W23 reliability-self-defense, v1.0 bar B3) — adds a nullable
``last_heartbeat_at`` column. The worker stamps it every few seconds while a
job is ``running`` (dedicated heartbeat thread); the same-boot stale-running
reaper compares ``now - COALESCE(last_heartbeat_at, started_at)`` against the
stale timeout to recover a hung/crashed worker that would otherwise hold the
single-active slot forever — without an API restart.

Additive and reversible: a single nullable column. Mirrors the ES-1b
``static_report_path`` migration (``f4b9d2e7a1c3``) — it does NOT touch the
partial unique index (``uq_analysis_jobs_single_active`` keeps its
``('queued', 'running', 'cancelling')`` WHERE clause) and performs no data
motion. The column is operational-only: it never flows through the analysis-job
snapshot Pydantic contracts, so no schema/contract version bump is required.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f8a1d7e9b2"
down_revision: str | Sequence[str] | None = "b3d9f1c2e7a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_jobs",
        sa.Column("last_heartbeat_at", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_jobs", "last_heartbeat_at")
