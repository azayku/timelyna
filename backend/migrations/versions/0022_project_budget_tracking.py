"""Add budget_alert_threshold to projects for budget tracking

Revision ID: 0022
Revises: 0021
Create Date: 2026-06-06 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add budget_alert_threshold column to projects table."""
    op.add_column(
        'projects',
        sa.Column('budget_alert_threshold', sa.Numeric(3, 2), nullable=True, comment='Seuil d\'alerte (0.8 = 80%)')
    )
    # Set default value for existing projects
    op.execute("UPDATE projects SET budget_alert_threshold = 0.8 WHERE budget_hours IS NOT NULL")


def downgrade() -> None:
    """Remove budget_alert_threshold column from projects table."""
    op.drop_column('projects', 'budget_alert_threshold')
