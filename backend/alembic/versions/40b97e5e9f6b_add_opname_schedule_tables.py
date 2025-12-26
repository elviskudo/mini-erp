"""add opname schedule tables

Revision ID: 40b97e5e9f6b
Revises: b576a5d6972b
Create Date: 2025-12-25 08:36:03.665730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40b97e5e9f6b'
down_revision: Union[str, None] = 'b576a5d6972b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
