"""Add preferred_language to employees

Revision ID: 0015
Revises: 0020
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0015'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'employees',
        sa.Column(
            'preferred_language',
            sa.String(5),
            nullable=False,
            server_default='fr',
        ),
    )


def downgrade() -> None:
    op.drop_column('employees', 'preferred_language')
