"""Add opname schedule tables and enhanced columns

Revision ID: 7e5ce8694982
Revises: 40b97e5e9f6b
Create Date: 2025-12-25 09:30:55.410951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7e5ce8694982'
down_revision: Union[str, None] = '40b97e5e9f6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create opname_schedules table
    op.create_table('opname_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(50), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('start_time', sa.String(10), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('count_all_items', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('category_filter', sa.String(255), nullable=True),
        sa.Column('location_filter', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_opname_schedules_tenant_id', 'opname_schedules', ['tenant_id'])
    
    # Create opname_assignments table
    op.create_table('opname_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('assigned_locations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['opname_schedules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_opname_assignments_tenant_id', 'opname_assignments', ['tenant_id'])
    
    # Add new columns to stock_opnames
    op.add_column('stock_opnames', sa.Column('schedule_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opnames', sa.Column('opname_number', sa.String(50), nullable=True))
    op.add_column('stock_opnames', sa.Column('total_items', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('stock_opnames', sa.Column('counted_items', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('stock_opnames', sa.Column('items_with_variance', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('stock_opnames', sa.Column('total_system_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opnames', sa.Column('total_counted_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opnames', sa.Column('total_variance_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opnames', sa.Column('counting_started_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opnames', sa.Column('counting_completed_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opnames', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opnames', sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opnames', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opnames', sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opnames', sa.Column('posted_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opnames', sa.Column('posted_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opnames', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opnames', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    op.create_foreign_key(None, 'stock_opnames', 'opname_schedules', ['schedule_id'], ['id'])
    op.create_foreign_key(None, 'stock_opnames', 'users', ['reviewed_by'], ['id'])
    op.create_foreign_key(None, 'stock_opnames', 'users', ['approved_by'], ['id'])
    op.create_foreign_key(None, 'stock_opnames', 'users', ['posted_by'], ['id'])
    op.create_foreign_key(None, 'stock_opnames', 'users', ['created_by'], ['id'])
    
    # Add new columns to stock_opname_details
    op.add_column('stock_opname_details', sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opname_details', sa.Column('variance', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opname_details', sa.Column('unit_cost', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opname_details', sa.Column('system_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opname_details', sa.Column('counted_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opname_details', sa.Column('variance_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('stock_opname_details', sa.Column('variance_reason', sa.String(50), nullable=True))
    op.add_column('stock_opname_details', sa.Column('variance_notes', sa.Text(), nullable=True))
    op.add_column('stock_opname_details', sa.Column('counted_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opname_details', sa.Column('counted_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opname_details', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('stock_opname_details', sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_opname_details', sa.Column('needs_recount', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('stock_opname_details', sa.Column('recount_reason', sa.String(255), nullable=True))
    
    op.create_foreign_key(None, 'stock_opname_details', 'locations', ['location_id'], ['id'])
    op.create_foreign_key(None, 'stock_opname_details', 'users', ['counted_by'], ['id'])
    op.create_foreign_key(None, 'stock_opname_details', 'users', ['verified_by'], ['id'])


def downgrade() -> None:
    # Drop columns from stock_opname_details
    op.drop_column('stock_opname_details', 'recount_reason')
    op.drop_column('stock_opname_details', 'needs_recount')
    op.drop_column('stock_opname_details', 'verified_by')
    op.drop_column('stock_opname_details', 'verified_at')
    op.drop_column('stock_opname_details', 'counted_by')
    op.drop_column('stock_opname_details', 'counted_at')
    op.drop_column('stock_opname_details', 'variance_notes')
    op.drop_column('stock_opname_details', 'variance_reason')
    op.drop_column('stock_opname_details', 'variance_value')
    op.drop_column('stock_opname_details', 'counted_value')
    op.drop_column('stock_opname_details', 'system_value')
    op.drop_column('stock_opname_details', 'unit_cost')
    op.drop_column('stock_opname_details', 'variance')
    op.drop_column('stock_opname_details', 'location_id')
    
    # Drop columns from stock_opnames
    op.drop_column('stock_opnames', 'created_by')
    op.drop_column('stock_opnames', 'created_at')
    op.drop_column('stock_opnames', 'posted_by')
    op.drop_column('stock_opnames', 'posted_at')
    op.drop_column('stock_opnames', 'approved_by')
    op.drop_column('stock_opnames', 'approved_at')
    op.drop_column('stock_opnames', 'reviewed_by')
    op.drop_column('stock_opnames', 'reviewed_at')
    op.drop_column('stock_opnames', 'counting_completed_at')
    op.drop_column('stock_opnames', 'counting_started_at')
    op.drop_column('stock_opnames', 'total_variance_value')
    op.drop_column('stock_opnames', 'total_counted_value')
    op.drop_column('stock_opnames', 'total_system_value')
    op.drop_column('stock_opnames', 'items_with_variance')
    op.drop_column('stock_opnames', 'counted_items')
    op.drop_column('stock_opnames', 'total_items')
    op.drop_column('stock_opnames', 'opname_number')
    op.drop_column('stock_opnames', 'schedule_id')
    
    # Drop tables
    op.drop_table('opname_assignments')
    op.drop_table('opname_schedules')
