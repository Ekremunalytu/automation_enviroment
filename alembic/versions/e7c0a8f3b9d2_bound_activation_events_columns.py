"""bound activation_events column lengths

Revision ID: e7c0a8f3b9d2
Revises: c8a2d4e91f5b
Create Date: 2026-05-15 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7c0a8f3b9d2"
down_revision: str | Sequence[str] | None = "c8a2d4e91f5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "extension_activation_events",
        "event_type",
        existing_type=sa.String(),
        type_=sa.String(64),
        existing_nullable=False,
        postgresql_using="substring(event_type, 1, 64)",
    )
    op.alter_column(
        "extension_activation_events",
        "event_value",
        existing_type=sa.String(),
        type_=sa.String(1024),
        existing_nullable=True,
        postgresql_using="substring(event_value, 1, 1024)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "extension_activation_events",
        "event_value",
        existing_type=sa.String(1024),
        type_=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "extension_activation_events",
        "event_type",
        existing_type=sa.String(64),
        type_=sa.String(),
        existing_nullable=False,
    )
