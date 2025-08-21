"""
add public_id (UUID) to contributions and heritage_sites

Revision ID: b7a4b3c2d1e0
Revises: a1d2c3e4f5a6
Create Date: 2025-08-20 21:46:50
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'b7a4b3c2d1e0'
down_revision = 'a1d2c3e4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add nullable columns first
    op.add_column('contributions', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('heritage_sites', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=True))

    bind = op.get_bind()

    # 2) Backfill with UUIDv4 for existing rows
    for table in ('contributions', 'heritage_sites'):
        rows = bind.execute(sa.text(f"SELECT id FROM {table} WHERE public_id IS NULL")).fetchall()
        for r in rows:
            bind.execute(
                sa.text(f"UPDATE {table} SET public_id = :pid WHERE id = :id"),
                {"pid": str(uuid.uuid4()), "id": r.id},
            )

    # 3) Set NOT NULL and add indexes/uniques
    op.alter_column('contributions', 'public_id', nullable=False)
    op.alter_column('heritage_sites', 'public_id', nullable=False)

    op.create_index('ix_contributions_public_id', 'contributions', ['public_id'], unique=False)
    op.create_unique_constraint('uq_contributions_public_id', 'contributions', ['public_id'])

    op.create_index('ix_heritage_sites_public_id', 'heritage_sites', ['public_id'], unique=False)
    op.create_unique_constraint('uq_heritage_sites_public_id', 'heritage_sites', ['public_id'])


def downgrade():
    # Drop constraints and columns in reverse order
    op.drop_constraint('uq_heritage_sites_public_id', 'heritage_sites', type_='unique')
    op.drop_index('ix_heritage_sites_public_id', table_name='heritage_sites')
    op.drop_column('heritage_sites', 'public_id')

    op.drop_constraint('uq_contributions_public_id', 'contributions', type_='unique')
    op.drop_index('ix_contributions_public_id', table_name='contributions')
    op.drop_column('contributions', 'public_id')
