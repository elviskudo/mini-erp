"""add_workcenter_location_fields

Revision ID: 440d16da2a39
Revises: 30c11b6a583c
Create Date: 2025-12-17 13:19:33.322545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '440d16da2a39'
down_revision: Union[str, None] = '30c11b6a583c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename columns
    op.alter_column('work_centers', 'hourly_rate', new_column_name='cost_per_hour')
    op.alter_column('work_centers', 'capacity_per_hour', new_column_name='capacity_hours')
    
    # Add new columns
    op.add_column('work_centers', sa.Column('location', sa.String(), nullable=True))
    op.add_column('work_centers', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('work_centers', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove new columns
    op.drop_column('work_centers', 'longitude')
    op.drop_column('work_centers', 'latitude')
    op.drop_column('work_centers', 'location')
    
    # Rename columns back
    op.alter_column('work_centers', 'capacity_hours', new_column_name='capacity_per_hour')
    op.alter_column('work_centers', 'cost_per_hour', new_column_name='hourly_rate')
