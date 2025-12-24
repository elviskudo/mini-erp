"""add vendor lat long

Revision ID: b66ff48bed61
Revises: daf70ed761ae
Create Date: 2025-12-23 08:06:45.833687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b66ff48bed61'
down_revision: Union[str, None] = 'daf70ed761ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
