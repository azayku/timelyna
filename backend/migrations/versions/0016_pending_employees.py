"""0016 — pending_employees table + account_creation_lead_days on org_settings

Revision ID: 0016
Revises: 0015
Create Date: 2025-01-01 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_employees",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="employee"),
        sa.Column("manager_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("birth_date", sa.Date, nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("hire_date", sa.Date, nullable=False),
        sa.Column("account_creation_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column(
        "org_settings",
        sa.Column("account_creation_lead_days", sa.Integer, nullable=False, server_default="2"),
    )


def downgrade() -> None:
    op.drop_column("org_settings", "account_creation_lead_days")
    op.drop_table("pending_employees")
