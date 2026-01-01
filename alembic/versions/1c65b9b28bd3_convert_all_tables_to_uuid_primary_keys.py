"""convert_all_tables_to_uuid_primary_keys

Revision ID: 1c65b9b28bd3
Revises: 448d88367490
Create Date: 2026-01-01 20:08:06.859646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1c65b9b28bd3'
down_revision: Union[str, Sequence[str], None] = '448d88367490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop foreign key constraints
    op.drop_constraint('fk_site_reviews_heritage_sites_id', 'site_reviews', type_='foreignkey')
    op.drop_constraint('fk_site_ratings_heritage_sites_id', 'site_ratings', type_='foreignkey')
    op.drop_constraint('fk_user_favorites_heritage_sites_id', 'user_favorites', type_='foreignkey')
    op.drop_constraint('fk_user_favorites_users_id', 'user_favorites', type_='foreignkey')
    op.drop_constraint('fk_heritage_sites_contributions_id', 'heritage_sites', type_='foreignkey')
    
    # Drop primary key constraints
    op.drop_constraint('users_pkey', 'users', type_='primary')
    op.drop_constraint('contributions_pkey', 'contributions', type_='primary')
    op.drop_constraint('heritage_sites_pkey', 'heritage_sites', type_='primary')
    op.drop_constraint('notifications_pkey', 'notifications', type_='primary')
    op.drop_constraint('user_favorites_pkey', 'user_favorites', type_='primary')
    op.drop_constraint('site_reviews_pkey', 'site_reviews', type_='primary')
    op.drop_constraint('site_ratings_pkey', 'site_ratings', type_='primary')
    
    # Drop old integer columns
    op.drop_column('users', 'id')
    op.drop_column('contributions', 'id')
    op.drop_column('heritage_sites', 'id')
    op.drop_column('notifications', 'id')
    op.drop_column('user_favorites', 'id')
    op.drop_column('site_reviews', 'id')
    op.drop_column('site_ratings', 'id')
    
    # Add UUID primary keys
    op.add_column('users', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('contributions', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('heritage_sites', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('notifications', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('user_favorites', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('site_reviews', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('site_ratings', sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False))
    
    # Populate UUID columns with data from public_id
    op.execute('UPDATE users SET id = public_id WHERE public_id IS NOT NULL')
    op.execute('UPDATE contributions SET id = public_id WHERE public_id IS NOT NULL')
    op.execute('UPDATE heritage_sites SET id = public_id WHERE public_id IS NOT NULL')
    op.execute('UPDATE notifications SET id = public_id WHERE public_id IS NOT NULL')
    op.execute('UPDATE user_favorites SET id = public_id WHERE public_id IS NOT NULL')
    op.execute('UPDATE site_reviews SET id = public_id WHERE public_id IS NOT NULL')
    op.execute('UPDATE site_ratings SET id = public_id WHERE public_id IS NOT NULL')
    
    # Make UUID columns not nullable
    op.alter_column('users', 'id', nullable=False)
    op.alter_column('contributions', 'id', nullable=False)
    op.alter_column('heritage_sites', 'id', nullable=False)
    op.alter_column('notifications', 'id', nullable=False)
    op.alter_column('user_favorites', 'id', nullable=False)
    op.alter_column('site_reviews', 'id', nullable=False)
    op.alter_column('site_ratings', 'id', nullable=False)
    
    # Create primary key constraints
    op.create_primary_key('users_pkey', 'users', ['id'])
    op.create_primary_key('contributions_pkey', 'contributions', ['id'])
    op.create_primary_key('heritage_sites_pkey', 'heritage_sites', ['id'])
    op.create_primary_key('notifications_pkey', 'notifications', ['id'])
    op.create_primary_key('user_favorites_pkey', 'user_favorites', ['id'])
    op.create_primary_key('site_reviews_pkey', 'site_reviews', ['id'])
    op.create_primary_key('site_ratings_pkey', 'site_ratings', ['id'])
    
    # Recreate foreign key constraints with UUID references
    op.create_foreign_key('fk_user_favorites_users_id', 'user_favorites', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_favorites_heritage_sites_id', 'user_favorites', 'heritage_sites', ['heritage_site_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_site_reviews_heritage_sites_id', 'site_reviews', 'heritage_sites', ['site_id'], ['id'])
    op.create_foreign_key('fk_site_ratings_heritage_sites_id', 'site_ratings', 'heritage_sites', ['site_id'], ['id'])
    op.create_foreign_key('fk_heritage_sites_contributions_id', 'heritage_sites', 'contributions', ['contribution_id'], ['id'])
    
    # Drop old public_id columns
    op.drop_column('users', 'public_id')
    op.drop_column('contributions', 'public_id')
    op.drop_column('heritage_sites', 'public_id')
    op.drop_column('notifications', 'public_id')
    op.drop_column('user_favorites', 'public_id')
    op.drop_column('site_reviews', 'public_id')
    op.drop_column('site_ratings', 'public_id')


def downgrade() -> None:
    """Downgrade schema."""
    # This would be complex to implement - would need to recreate integer IDs
    # For now, just note that this migration is not easily reversible
    pass
