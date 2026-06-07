"""Create module_licenses table for modular licensing.

Revision ID: 0010
Revises: 0001
Create Date: 2024-01-15 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create module_licenses table
    op.create_table(
        "module_licenses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("module_name", sa.String(50), nullable=False),
        sa.Column("license_key", sa.String(100), nullable=False),
        sa.Column("expires_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "module_name", name="uq_org_module"),
    )


def downgrade() -> None:
    # Drop module_licenses table
    op.drop_table("module_licenses")
