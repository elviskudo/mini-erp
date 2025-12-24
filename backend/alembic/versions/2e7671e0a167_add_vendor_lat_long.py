"""add vendor lat long

Revision ID: 2e7671e0a167
Revises: 3636130474cf
Create Date: 2025-12-23 08:51:59.974744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e7671e0a167'
down_revision: Union[str, None] = '3636130474cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
