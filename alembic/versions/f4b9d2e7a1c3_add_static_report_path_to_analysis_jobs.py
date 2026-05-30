"""add static_report_path to analysis_jobs (ES-1b / ADR 0016 Static Analysis Pre-Check)

Revision ID: f4b9d2e7a1c3
Revises: e7c0a8f3b9d2
Create Date: 2026-05-30 00:00:00.000000

ES-1b (Static Analysis Pre-Check Stream, ADR 0016) — adds a nullable
``static_report_path`` column recording the filesystem path to the persisted
``StaticAnalysisReport`` JSON for jobs that ran the static pre-check stage. The
column mirrors the ``static_report_path`` field added to
``AnalysisJobCreateSnapshot`` / ``AnalysisJobUpdate`` in the same sub-iter.

Additive and reversible: a single nullable column. Unlike the W13-3
``cancelling`` migration (``c8a2d4e91f5b``) this does NOT touch the partial
unique index — the new ``rejected_static`` status is terminal, never active,
so ``uq_analysis_jobs_single_active`` keeps its
``('queued', 'running', 'cancelling')`` WHERE clause. Status values live in a
free ``String`` column (no DB enum), so ``rejected_static`` needs no type
alteration either.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4b9d2e7a1c3"
down_revision: str | Sequence[str] | None = "e7c0a8f3b9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_jobs",
        sa.Column("static_report_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_jobs", "static_report_path")
