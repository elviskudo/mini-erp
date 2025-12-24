"""add_product_description_column

Revision ID: 8de2581c49f2
Revises: c3801fe48343
Create Date: 2025-12-20 12:59:53.065689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8de2581c49f2'
down_revision: Union[str, None] = 'c3801fe48343'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
