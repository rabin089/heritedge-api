"""add intangible to contributiontype enum

Revision ID: a1b2c3d4e5f6
Revises: 39af5558833c
Create Date: 2026-06-05 21:42:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '39af5558833c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'intangible' value to the contributiontype PostgreSQL enum."""
    op.execute("ALTER TYPE contributiontype ADD VALUE IF NOT EXISTS 'intangible'")


def downgrade() -> None:
    """PostgreSQL does not support removing values from enums easily.
    To fully downgrade, you would need to recreate the enum type without 'intangible'.
    This is left as a no-op for safety.
    """
    pass
