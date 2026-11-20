"""Add subadmin ownership and accounting entries.

Revision ID: b8c6d1a4f203
Revises: f3a91b62d408
"""

from alembic import op
import sqlalchemy as sa


revision = "b8c6d1a4f203"
down_revision = "f3a91b62d408"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "admins",
        sa.Column(
            "parent_admin_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("admins.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index("ix_admins_parent_admin_id", "admins", ["parent_admin_id"])
    op.add_column(
        "admins",
        sa.Column("blocked_by_parent", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_table(
        "admin_accounting_entries",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "admin_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("admins.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "user_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_accounting_entries_admin_created",
        "admin_accounting_entries",
        ["admin_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_admin_accounting_entries_admin_created", table_name="admin_accounting_entries")
    op.drop_table("admin_accounting_entries")
    op.drop_column("admins", "blocked_by_parent")
    op.drop_index("ix_admins_parent_admin_id", table_name="admins")
    op.drop_column("admins", "parent_admin_id")
