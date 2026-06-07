"""Add address and deactivation_scheduled_at to employees.

Revision ID: 0012
Revises: 0011_invoice_enhancements
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("address", sa.String(500), nullable=True),
    )
    op.add_column(
        "employees",
        sa.Column(
            "deactivation_scheduled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("employees", "deactivation_scheduled_at")
    op.drop_column("employees", "address")
