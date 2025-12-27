"""Add logistics models

Revision ID: 27d95a051fa2
Revises: 7e5ce8694982
Create Date: 2025-12-27 00:18:31.761050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27d95a051fa2'
down_revision: Union[str, None] = '7e5ce8694982'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
