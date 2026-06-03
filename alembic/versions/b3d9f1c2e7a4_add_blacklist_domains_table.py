"""add blacklist_domains table (operator-editable blacklist_domains field)

Revision ID: b3d9f1c2e7a4
Revises: f4b9d2e7a1c3
Create Date: 2026-06-02 00:00:00.000000

Backs the UI-editable operator denylist (``/api/rules/blacklist-domains``). The
detection rules' effective denylist is the shipped seed file UNION the rows in
this table, so an operator edit augments — never replaces — the baseline.

Additive and reversible: a single new table, no touch to existing tables or
indexes. ``domain`` is the primary key (service normalizes to lowercase before
insert), making a repeated add an idempotent upsert.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3d9f1c2e7a4"
down_revision: str | Sequence[str] | None = "f4b9d2e7a1c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "blacklist_domains",
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("added_at", sa.Float(), nullable=False),
        sa.Column("added_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("domain"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("blacklist_domains")
