"""add_product_description_column

Revision ID: c3801fe48343
Revises: 50566179d206
Create Date: 2025-12-20 00:03:54.937940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3801fe48343'
down_revision: Union[str, None] = '50566179d206'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
