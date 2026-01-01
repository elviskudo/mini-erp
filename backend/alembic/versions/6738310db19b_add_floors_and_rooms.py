"""add_floors_and_rooms

Revision ID: 6738310db19b
Revises: 7d0dd76bdde3
Create Date: 2025-12-30 23:00:01.318674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6738310db19b'
down_revision: Union[str, None] = '7d0dd76bdde3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
