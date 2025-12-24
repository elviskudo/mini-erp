"""add vendor lat long

Revision ID: 3636130474cf
Revises: b66ff48bed61
Create Date: 2025-12-23 08:40:18.682301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3636130474cf'
down_revision: Union[str, None] = 'b66ff48bed61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
