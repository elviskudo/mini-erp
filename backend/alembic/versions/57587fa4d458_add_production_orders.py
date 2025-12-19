"""add_production_orders

Revision ID: 57587fa4d458
Revises: 440d16da2a39
Create Date: 2025-12-19 02:24:32.444922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57587fa4d458'
down_revision: Union[str, None] = '440d16da2a39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
