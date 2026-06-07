"""add_festival_location_specific

Revision ID: 202606071200
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202606071200'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('festivals', sa.Column('is_location_specific', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('festivals', sa.Column('location_name', sa.String(), nullable=True))
    op.add_column('festivals', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('festivals', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('festivals', 'longitude')
    op.drop_column('festivals', 'latitude')
    op.drop_column('festivals', 'location_name')
    op.drop_column('festivals', 'is_location_specific')
