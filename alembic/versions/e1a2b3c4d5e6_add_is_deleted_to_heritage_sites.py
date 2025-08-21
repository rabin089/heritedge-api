"""
Add is_deleted (soft delete) to heritage_sites

Revision ID: e1a2b3c4d5e6
Revises: c9d8e7f6a5b4
Create Date: 2025-08-21 20:08:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'c9d8e7f6a5b4'
branch_labels = None
depends_on = None


def upgrade():
    # Add column with server_default for backfill, then drop default
    op.add_column('heritage_sites', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade():
    op.drop_column('heritage_sites', 'is_deleted')
