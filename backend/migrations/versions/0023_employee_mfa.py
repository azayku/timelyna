"""Add MFA/2FA fields to employees table.

Revision ID: 0023
Revises: 0021
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add mfa_secret and mfa_enabled columns to employees."""
    op.add_column(
        "employees",
        sa.Column("mfa_secret", sa.String(64), nullable=True, comment="Secret TOTP pour 2FA")
    )
    op.add_column(
        "employees",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false", comment="2FA activé")
    )


def downgrade() -> None:
    """Remove MFA columns from employees."""
    op.drop_column("employees", "mfa_enabled")
    op.drop_column("employees", "mfa_secret")
