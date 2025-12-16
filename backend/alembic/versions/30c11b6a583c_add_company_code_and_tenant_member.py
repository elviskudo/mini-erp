"""add_company_code_and_tenant_member

Revision ID: 30c11b6a583c
Revises: 62d3d9583386
Create Date: 2025-12-14 10:31:12.467366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '30c11b6a583c'
down_revision: Union[str, None] = '62d3d9583386'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create MemberRole enum type
    member_role = postgresql.ENUM('OWNER', 'ADMIN', 'MEMBER', 'PENDING', name='memberrole', create_type=False)
    member_role.create(op.get_bind(), checkfirst=True)
    
    # Add company_code column to tenants table
    op.add_column('tenants', sa.Column('company_code', sa.String(length=6), nullable=True))
    op.create_index(op.f('ix_tenants_company_code'), 'tenants', ['company_code'], unique=True)
    
    # Create tenant_members table
    op.create_table('tenant_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'PENDING', name='memberrole'), nullable=False),
        sa.Column('invited_at', sa.DateTime(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_members_tenant_id'), 'tenant_members', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_tenant_members_user_id'), 'tenant_members', ['user_id'], unique=False)
    
    # Add tenant_id to users if not exists
    try:
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'))
        op.add_column('users', sa.Column('otp_code', sa.String(length=6), nullable=True))
        op.add_column('users', sa.Column('otp_expires_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Columns might already exist


def downgrade() -> None:
    op.drop_index(op.f('ix_tenant_members_user_id'), table_name='tenant_members')
    op.drop_index(op.f('ix_tenant_members_tenant_id'), table_name='tenant_members')
    op.drop_table('tenant_members')
    op.drop_index(op.f('ix_tenants_company_code'), table_name='tenants')
    op.drop_column('tenants', 'company_code')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS memberrole")
