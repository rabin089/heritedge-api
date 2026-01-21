"""update_festival_model

Revision ID: 202601211400
Revises: fd7aa6314581
Create Date: 2026-01-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '202601211400'
down_revision: Union[str, Sequence[str], None] = 'fd7aa6314581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Handle Status Enum Change
    op.execute("ALTER TYPE festivalstatus RENAME TO festivalstatus_old")
    op.execute("CREATE TYPE festivalstatus AS ENUM('pending', 'approved', 'rejected')")
    op.execute("ALTER TABLE festivals ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE festivals ALTER COLUMN status TYPE festivalstatus USING 'pending'::festivalstatus")
    op.execute("DROP TYPE festivalstatus_old")
    
    # 2. Add New Columns
    op.add_column('festivals', sa.Column('significance', sa.String(), nullable=True))
    op.add_column('festivals', sa.Column('nepali_date', sa.String(), nullable=True))
    op.add_column('festivals', sa.Column('locations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('festivals', sa.Column('main_image', sa.String(), nullable=True))
    op.add_column('festivals', sa.Column('gallery', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('festivals', sa.Column('is_annual', sa.Boolean(), server_default='false', nullable=True))

    # 3. Handle Category Enum Change
    festival_category = sa.Enum('Religious', 'Cultural', 'National', name='festivalcategory')
    festival_category.create(op.get_bind())
    op.execute("ALTER TABLE festivals ALTER COLUMN category TYPE festivalcategory USING category::text::festivalcategory")

    # 4. Handle created_by change to UUID and FK
    # Note: This assumes created_by currently holds valid UUID strings. If not, this migration will fail.
    op.execute("ALTER TABLE festivals ALTER COLUMN created_by TYPE UUID USING created_by::uuid")
    op.create_foreign_key(None, 'festivals', 'users', ['created_by'], ['id'])

    # 5. Drop Old Columns
    op.drop_column('festivals', 'location')
    op.drop_column('festivals', 'latitude')
    op.drop_column('festivals', 'longitude')
    op.drop_column('festivals', 'image_url')
    op.drop_column('festivals', 'secondary_images')
    op.drop_column('festivals', 'organizer')
    op.drop_column('festivals', 'contact_info')
    op.drop_column('festivals', 'website_url')
    op.drop_column('festivals', 'ticket_info')
    op.drop_column('festivals', 'is_approved')
    op.drop_column('festivals', 'approval_reason')
    op.drop_column('festivals', 'approved_by')
    op.drop_column('festivals', 'approved_at')
    op.drop_column('festivals', 'updated_by')
    op.drop_column('festivals', 'updated_at')
    op.drop_column('festivals', 'deleted_by')
    op.drop_column('festivals', 'deleted_at')
    op.drop_column('festivals', 'is_deleted')


def downgrade() -> None:
    # 1. Add back deleted columns (nullable for now)
    op.add_column('festivals', sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('deleted_by', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('approved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('approved_by', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('approval_reason', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('is_approved', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('ticket_info', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('website_url', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('contact_info', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('organizer', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('secondary_images', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('image_url', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('longitude', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('latitude', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('festivals', sa.Column('location', sa.VARCHAR(), autoincrement=False, nullable=True))

    # 2. Revert created_by
    op.drop_constraint(None, 'festivals', type_='foreignkey')
    op.alter_column('festivals', 'created_by', type_=sa.VARCHAR(), postgresql_using="created_by::text")

    # 3. Revert Category
    op.execute("ALTER TABLE festivals ALTER COLUMN category TYPE VARCHAR USING category::text")
    op.execute("DROP TYPE festivalcategory")

    # 4. Remove new columns
    op.drop_column('festivals', 'is_annual')
    op.drop_column('festivals', 'gallery')
    op.drop_column('festivals', 'main_image')
    op.drop_column('festivals', 'locations')
    op.drop_column('festivals', 'nepali_date')
    op.drop_column('festivals', 'significance')
    
    # 5. Revert Status
    op.execute("ALTER TYPE festivalstatus RENAME TO festivalstatus_new")
    op.execute("CREATE TYPE festivalstatus AS ENUM('upcoming', 'ongoing', 'completed', 'cancelled')")
    op.execute("ALTER TABLE festivals ALTER COLUMN status TYPE festivalstatus USING 'upcoming'::festivalstatus")
    op.execute("DROP TYPE festivalstatus_new")
