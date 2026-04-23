"""lowercase_festival_category_enum

Revision ID: faabebd8f81e
Revises: a6359f5cfd52
Create Date: 2026-03-08 19:22:04.273481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faabebd8f81e'
down_revision: Union[str, Sequence[str], None] = 'a6359f5cfd52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the enum values using raw SQL since Alembic doesn't autogenerate this
    op.execute("ALTER TYPE festivalcategory RENAME VALUE 'Religious' TO 'religious'")
    op.execute("ALTER TYPE festivalcategory RENAME VALUE 'Cultural' TO 'cultural'")
    op.execute("ALTER TYPE festivalcategory RENAME VALUE 'National' TO 'national'")


def downgrade() -> None:
    op.execute("ALTER TYPE festivalcategory RENAME VALUE 'religious' TO 'Religious'")
    op.execute("ALTER TYPE festivalcategory RENAME VALUE 'cultural' TO 'Cultural'")
    op.execute("ALTER TYPE festivalcategory RENAME VALUE 'national' TO 'National'")
