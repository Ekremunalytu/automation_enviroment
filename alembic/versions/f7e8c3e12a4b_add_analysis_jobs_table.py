"""add analysis_jobs table

Revision ID: f7e8c3e12a4b
Revises: d50003b4c96e
Create Date: 2026-04-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7e8c3e12a4b"
down_revision: str | Sequence[str] | None = "d50003b4c96e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "analysis_jobs",
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("owner_boot_id", sa.String(), nullable=False),
        sa.Column("owner_pid", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("publisher", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("scenario", sa.String(), nullable=True),
        sa.Column("analysis_profile", sa.String(), nullable=True),
        sa.Column("current_step", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("report_path", sa.String(), nullable=True),
        sa.Column("install_output", sa.Text(), nullable=True),
        sa.Column("automation_output", sa.Text(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("started_at", sa.Float(), nullable=True),
        sa.Column("finished_at", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(
        "ix_analysis_jobs_status",
        "analysis_jobs",
        ["status"],
        unique=False,
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_analysis_jobs_single_active "
        "ON analysis_jobs ((1)) "
        "WHERE status IN ('queued', 'running')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX uq_analysis_jobs_single_active")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
