"""Add app_config table for installation wizard.

Revision ID: 0025
Revises: 0024
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("is_installed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("app_name", sa.String(255), nullable=False, server_default="Timelyna"),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("company_logo", sa.Text, nullable=True),
        sa.Column("installed_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
    # Insert the initial (not-installed) row
    op.execute(
        "INSERT INTO app_config (is_installed, app_name) VALUES (false, 'Timelyna')"
    )

    # Add logo column to org_settings if missing (for future use)
    try:
        op.add_column(
            "org_settings",
            sa.Column("company_logo", sa.Text, nullable=True),
        )
    except Exception:
        pass  # Column may already exist


def downgrade() -> None:
    op.drop_table("app_config")
    try:
        op.drop_column("org_settings", "company_logo")
    except Exception:
        pass
