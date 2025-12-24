"""add vendor lat long

Revision ID: b576a5d6972b
Revises: 2e7671e0a167
Create Date: 2025-12-23 08:54:41.165329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b576a5d6972b'
down_revision: Union[str, None] = '2e7671e0a167'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
