"""add per-admin host display preferences

Revision ID: d15b7a6c9e21
Revises: 48a6bcb8bba1

"""

import sqlalchemy as sa
from alembic import op

revision = "d15b7a6c9e21"
down_revision = "48a6bcb8bba1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("admins", sa.Column("host_preferences", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("admins", "host_preferences")
