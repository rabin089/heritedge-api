"""add_public_id_uuid_to_all_tables

Revision ID: 448d88367490
Revises: 2bda3ab22456
Create Date: 2026-01-01 19:52:44.643827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '448d88367490'
down_revision: Union[str, Sequence[str], None] = '2bda3ab22456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add public_id column to users table
    op.add_column('users', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.create_index('ix_users_public_id', 'users', ['public_id'], unique=True)
    
    # Add public_id column to notifications table
    op.add_column('notifications', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.create_index('ix_notifications_public_id', 'notifications', ['public_id'], unique=True)
    
    # Add public_id column to user_favorites table
    op.add_column('user_favorites', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.create_index('ix_user_favorites_public_id', 'user_favorites', ['public_id'], unique=True)
    
    # Add public_id column to site_reviews table
    op.add_column('site_reviews', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.create_index('ix_site_reviews_public_id', 'site_reviews', ['public_id'], unique=True)
    
    # Add public_id column to site_ratings table
    op.add_column('site_ratings', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.create_index('ix_site_ratings_public_id', 'site_ratings', ['public_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes and columns
    op.drop_index('ix_site_ratings_public_id', table_name='site_ratings')
    op.drop_column('site_ratings', 'public_id')
    
    op.drop_index('ix_site_reviews_public_id', table_name='site_reviews')
    op.drop_column('site_reviews', 'public_id')
    
    op.drop_index('ix_user_favorites_public_id', table_name='user_favorites')
    op.drop_column('user_favorites', 'public_id')
    
    op.drop_index('ix_notifications_public_id', table_name='notifications')
    op.drop_column('notifications', 'public_id')
    
    op.drop_index('ix_users_public_id', table_name='users')
    op.drop_column('users', 'public_id')
