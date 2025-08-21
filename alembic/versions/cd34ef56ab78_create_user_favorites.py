"""
Create user_favorites table

Revision ID: cd34ef56ab78
Revises: bc23de45fa67
Create Date: 2025-08-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cd34ef56ab78'
down_revision = 'bc23de45fa67'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_favorites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('heritage_site_id', sa.Integer(), sa.ForeignKey('heritage_sites.id', ondelete='CASCADE'), nullable=False),
    )
    op.create_unique_constraint('uq_user_site_fav', 'user_favorites', ['user_id', 'heritage_site_id'])
    op.create_index('ix_user_favorites_user_id', 'user_favorites', ['user_id'])
    op.create_index('ix_user_favorites_site_id', 'user_favorites', ['heritage_site_id'])


def downgrade() -> None:
    op.drop_index('ix_user_favorites_site_id', table_name='user_favorites')
    op.drop_index('ix_user_favorites_user_id', table_name='user_favorites')
    op.drop_constraint('uq_user_site_fav', 'user_favorites', type_='unique')
    op.drop_table('user_favorites')
