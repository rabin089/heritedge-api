"""Add type and dates to contributions

Revision ID: f3b8e2d4a1b0
Revises: cec5c3eccaa4
Create Date: 2026-02-22 15:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f3b8e2d4a1b0'
down_revision: Union[str, Sequence[str], None] = 'cec5c3eccaa4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ContributionType enum
    contribution_type = sa.Enum('site', 'festival', name='contributiontype')
    contribution_type.create(op.get_bind())

    # Add columns to contributions table
    op.add_column('contributions', sa.Column('type', sa.Enum('site', 'festival', name='contributiontype'), server_default='site', nullable=False))
    op.add_column('contributions', sa.Column('start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('contributions', sa.Column('end_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Drop columns
    op.drop_column('contributions', 'end_date')
    op.drop_column('contributions', 'start_date')
    op.drop_column('contributions', 'type')

    # Drop enum type
    op.execute('DROP TYPE contributiontype')
