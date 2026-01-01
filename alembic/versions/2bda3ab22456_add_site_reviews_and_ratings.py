"""add_site_reviews_and_ratings

Revision ID: 2bda3ab22456
Revises: c709ad228bb4
Create Date: 2026-01-01 19:13:37.966996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bda3ab22456'
down_revision: Union[str, Sequence[str], None] = 'c709ad228bb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create site_reviews table
    op.create_table('site_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['heritage_sites.id'], ),
        sa.CheckConstraint('rating >= 0 AND rating <= 10', name='check_rating_range'),
        sa.UniqueConstraint('site_id', 'user_email', name='unique_site_user_review'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_reviews_site_id', 'site_reviews', ['site_id'])
    op.create_index('ix_site_reviews_user_email', 'site_reviews', ['user_email'])
    
    # Create site_ratings table
    op.create_table('site_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['heritage_sites.id'], ),
        sa.CheckConstraint('rating >= 0 AND rating <= 10', name='check_rating_range'),
        sa.UniqueConstraint('site_id', 'user_email', name='unique_site_user_rating'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_ratings_site_id', 'site_ratings', ['site_id'])
    op.create_index('ix_site_ratings_user_email', 'site_ratings', ['user_email'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('site_ratings')
    op.drop_table('site_reviews')
