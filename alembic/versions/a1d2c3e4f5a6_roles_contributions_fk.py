"""Add users.role, create contributions, add heritage_sites.contribution_id FK

Revision ID: a1d2c3e4f5a6
Revises: 941f7497ff7f
Create Date: 2025-08-20 21:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1d2c3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '941f7497ff7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ContributionStatus = sa.Enum('pending', 'approved', 'rejected', name='contributionstatus')


def upgrade() -> None:
    # 1) users.role
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='user'))

    # 2) contributions table
    op.create_table(
        'contributions',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('secondary_images', postgresql.ARRAY(sa.String(), dimensions=1), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(), dimensions=1), nullable=True),
        sa.Column('status', ContributionStatus, nullable=False, server_default='pending'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=False),
    )
    op.create_index(op.f('ix_contributions_id'), 'contributions', ['id'], unique=False)

    # 3) heritage_sites adjustments
    # ensure existing NULLs for is_pending/created_at are set, then alter
    conn = op.get_bind()
    # Set NULL is_pending to false where needed before making non-nullable
    conn.execute(sa.text("UPDATE heritage_sites SET is_pending = false WHERE is_pending IS NULL"))
    # Set NULL created_at to now() where needed before making non-nullable
    conn.execute(sa.text("UPDATE heritage_sites SET created_at = now() WHERE created_at IS NULL"))

    op.alter_column('heritage_sites', 'is_pending', existing_type=sa.Boolean(), nullable=False, server_default=sa.text('false'))
    op.alter_column('heritage_sites', 'created_at', existing_type=sa.DateTime(), nullable=False, server_default=sa.text('now()'))

    # add contribution_id + FK
    op.add_column('heritage_sites', sa.Column('contribution_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        constraint_name='fk_heritage_sites_contribution_id',
        source_table='heritage_sites',
        referent_table='contributions',
        local_cols=['contribution_id'],
        remote_cols=['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # heritage_sites: drop FK and column
    op.drop_constraint('fk_heritage_sites_contribution_id', 'heritage_sites', type_='foreignkey')
    op.drop_column('heritage_sites', 'contribution_id')

    # heritage_sites: relax constraints (cannot easily drop server defaults across DBs, but attempt)
    op.alter_column('heritage_sites', 'created_at', server_default=None, nullable=True)
    op.alter_column('heritage_sites', 'is_pending', server_default=None, nullable=True)

    # contributions
    op.drop_index(op.f('ix_contributions_id'), table_name='contributions')
    op.drop_table('contributions')
    ContributionStatus.drop(op.get_bind(), checkfirst=True)

    # users.role
    op.drop_column('users', 'role')
