"""add operator_settings table

Revision ID: a1c4f9d2b8e3
Revises: f7e8c3e12a4b
Create Date: 2026-05-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c4f9d2b8e3"
down_revision: str | Sequence[str] | None = "f7e8c3e12a4b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "operator_settings",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("operator_settings")
