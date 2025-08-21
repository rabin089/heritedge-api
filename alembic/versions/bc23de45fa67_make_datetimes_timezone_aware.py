"""
Make datetime columns timezone-aware (timestamptz) assuming existing values are UTC.

Revision ID: bc23de45fa67
Revises: ab12cd34ef56
Create Date: 2025-08-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bc23de45fa67'
down_revision = 'ab12cd34ef56'
branch_labels = None
depends_on = None


TABLES_AND_COLS = {
    'contributions': ['created_at', 'approved_at', 'updated_at', 'deleted_at'],
    'heritage_sites': ['created_at', 'approved_at', 'updated_at', 'deleted_at'],
}


def upgrade() -> None:
    # Alter columns to timestamptz, interpreting existing timestamps as UTC
    for table, cols in TABLES_AND_COLS.items():
        for col in cols:
            # Some nullable columns may not exist in earlier states, guard with IF EXISTS
            op.execute(
                sa.text(
                    f"""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = :table AND column_name = :col
                        ) THEN
                            ALTER TABLE {table}
                                ALTER COLUMN {col}
                                TYPE TIMESTAMP WITH TIME ZONE
                                USING CASE WHEN {col} IS NULL THEN NULL ELSE {col} AT TIME ZONE 'UTC' END;
                        END IF;
                    END $$;
                    """
                ).bindparams(table=table, col=col)
            )


def downgrade() -> None:
    # Revert to timestamp without time zone, dropping tz info
    for table, cols in TABLES_AND_COLS.items():
        for col in cols:
            op.execute(
                f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{table}' AND column_name = '{col}'
                    ) THEN
                        ALTER TABLE {table}
                            ALTER COLUMN {col}
                            TYPE TIMESTAMP WITHOUT TIME ZONE
                            USING {col} AT TIME ZONE 'UTC';
                    END IF;
                END $$;
                """
            )
