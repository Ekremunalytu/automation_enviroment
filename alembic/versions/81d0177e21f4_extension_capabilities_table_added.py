"""extension_capabilities table added

Revision ID: 81d0177e21f4
Revises: 89f62ee11a82
Create Date: 2025-12-18 17:25:24.573032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '81d0177e21f4'
down_revision: Union[str, Sequence[str], None] = '89f62ee11a82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('extension_capabilities',
    sa.Column('extension_id', sa.Integer(), nullable=False),
    sa.Column('untrusted_supported', sa.Enum('supported', 'not_supported', 'limited', name='capability_support_state'), nullable=True),
    sa.Column('untrusted_description', sa.Text(), nullable=True),
    sa.Column('untrusted_restricted_configurations', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('virtual_supported', sa.Enum('supported', 'not_supported', 'limited', name='capability_support_state'), nullable=True),
    sa.Column('virtual_description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['extension_id'], ['extensions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('extension_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('extension_capabilities')
    op.execute("DROP TYPE IF EXISTS capability_support_state")
