"""
Phase 3: soft delete for contributions and audit fields for heritage_sites and contributions

Revision ID: ab12cd34ef56
Revises: e1a2b3c4d5e6
Create Date: 2025-08-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ab12cd34ef56'
down_revision = 'e1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # contributions: soft delete + audit fields
    op.add_column('contributions', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('contributions', sa.Column('approved_by', sa.String(), nullable=True))
    op.add_column('contributions', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('contributions', sa.Column('updated_by', sa.String(), nullable=True))
    op.add_column('contributions', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('contributions', sa.Column('deleted_by', sa.String(), nullable=True))
    op.add_column('contributions', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # heritage_sites: audit fields
    op.add_column('heritage_sites', sa.Column('approved_by', sa.String(), nullable=True))
    op.add_column('heritage_sites', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('heritage_sites', sa.Column('updated_by', sa.String(), nullable=True))
    op.add_column('heritage_sites', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('heritage_sites', sa.Column('deleted_by', sa.String(), nullable=True))
    op.add_column('heritage_sites', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # clear server_default for is_deleted so ORM default applies going forward
    op.alter_column('contributions', 'is_deleted', server_default=None)


def downgrade() -> None:
    # heritage_sites
    op.drop_column('heritage_sites', 'deleted_at')
    op.drop_column('heritage_sites', 'deleted_by')
    op.drop_column('heritage_sites', 'updated_at')
    op.drop_column('heritage_sites', 'updated_by')
    op.drop_column('heritage_sites', 'approved_at')
    op.drop_column('heritage_sites', 'approved_by')

    # contributions
    op.drop_column('contributions', 'deleted_at')
    op.drop_column('contributions', 'deleted_by')
    op.drop_column('contributions', 'updated_at')
    op.drop_column('contributions', 'updated_by')
    op.drop_column('contributions', 'approved_at')
    op.drop_column('contributions', 'approved_by')
    op.drop_column('contributions', 'is_deleted')
