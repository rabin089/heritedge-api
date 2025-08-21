"""
Add status_reason column to contributions and backfill from rejection_reason

Revision ID: c9d8e7f6a5b4
Revises: b7a4b3c2d1e0
Create Date: 2025-08-21 19:25:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c9d8e7f6a5b4'
down_revision = 'b7a4b3c2d1e0'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new nullable column
    op.add_column('contributions', sa.Column('status_reason', sa.Text(), nullable=True))

    # Backfill status_reason from rejection_reason where available
    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE contributions SET status_reason = rejection_reason WHERE rejection_reason IS NOT NULL AND status_reason IS NULL"
    ))


def downgrade():
    op.drop_column('contributions', 'status_reason')
