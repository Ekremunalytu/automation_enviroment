"""add vsix_sha256 to analysis_jobs (W26 / Stream 3 B5 verdict provenance)

Revision ID: e2b7a4c9d1f3
Revises: c3f8a1d7e9b2
Create Date: 2026-06-26 00:00:00.000000

W26 (verdict-provenance-reproducibility, v1.0 bar B5) — adds a nullable
``vsix_sha256`` column. ``start_analysis_job`` computes the SHA-256 of the staged
``.vsix`` at analyze-start and ``reserve_job`` stamps it on the row at creation,
so a completed job's verdict is provably bound to the exact bytes scanned (two
byte-different same-version VSIX yield two distinct rows).

Additive and reversible: a single nullable column. Mirrors the
``last_heartbeat_at`` migration (``c3f8a1d7e9b2``) and the ES-1b
``static_report_path`` migration (``f4b9d2e7a1c3``) — it does NOT touch the
partial unique index (``uq_analysis_jobs_single_active`` keeps its
``('queued', 'running', 'cancelling')`` WHERE clause) and performs no data
motion. Unlike ``last_heartbeat_at`` (operational-only), this column flows
through the ``AnalysisJobCreateSnapshot`` Pydantic contract as an additive,
optional, defaulted field — backward-compatible, so no contract version bump is
required.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2b7a4c9d1f3"
down_revision: str | Sequence[str] | None = "c3f8a1d7e9b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_jobs",
        sa.Column("vsix_sha256", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_jobs", "vsix_sha256")
