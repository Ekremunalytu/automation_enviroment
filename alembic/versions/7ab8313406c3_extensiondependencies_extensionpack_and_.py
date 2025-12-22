"""extensionDependencies, extensionPack and extensionKind fields added to extension table

Revision ID: 7ab8313406c3
Revises: 972a85ca728a
Create Date: 2025-12-21 14:42:24.443741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ab8313406c3'
down_revision: Union[str, Sequence[str], None] = '972a85ca728a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "extensions",
        sa.Column("extensionPack", sa.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "extensions",
        sa.Column("extensionDependencies", sa.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "extensions",
        sa.Column("extensionKind", sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("extensions", "extensionKind")
    op.drop_column("extensions", "extensionDependencies")
    op.drop_column("extensions", "extensionPack")
