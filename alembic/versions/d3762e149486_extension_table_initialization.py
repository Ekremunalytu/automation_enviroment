"""extension table initialization

Revision ID: d3762e149486
Revises:
Create Date: 2025-12-09 21:39:45.219457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3762e149486'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'extensions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('publisher', sa.String(), nullable=False, index=True),
        sa.Column('engines', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('license', sa.String(), nullable=True),
        sa.Column('displayName', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('categories', sa.dialects.postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keywords', sa.dialects.postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('galleryBanner', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('preview', sa.Boolean(), nullable=True),
        sa.Column('badges', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('markdown', sa.Text(), nullable=True),
        sa.Column('qna', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('sponsor', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('pricing', sa.String(), nullable=True),
        sa.Column('main', sa.String(), nullable=True),
        sa.Column('web', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('publisher', 'name', name='uix_publisher_name')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('extensions')
