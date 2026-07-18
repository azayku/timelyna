"""Add emergency_contacts table for contact management.

Revision ID: 0026
Revises: 0025
Create Date: 2026-07-18
"""
from alembic import op
import sqlalchemy as sa


revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emergency_contacts",
        sa.Column("contact_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.employee_id"),
            nullable=False,
        ),
        sa.Column("contact_name", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("contact_type", sa.String(50), nullable=False, server_default="urgence"),
        sa.Column("tags", sa.Text, nullable=True),  # JSON array as text
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by",
            sa.Integer,
            sa.ForeignKey("employees.employee_id"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "deleted_at", sa.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("emergency_contacts")
