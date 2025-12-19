"""Initial migration

Revision ID: 62d3d9583386
Revises: 
Create Date: 2025-12-12 22:00:46.702829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '62d3d9583386'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Initial schema creation.
    Note: Most tables are auto-created by SQLAlchemy Base.metadata.create_all()
    This migration ensures critical SaaS tables exist with all required columns.
    """
    
    # Create enum types
    op.execute("DO $$ BEGIN CREATE TYPE subscriptiontier AS ENUM ('FREE_TRIAL', 'MAKER', 'GROWTH', 'ENTERPRISE'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE memberrole AS ENUM ('owner', 'admin', 'member', 'pending'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'PRODUCTION', 'WAREHOUSE', 'STAFF', 'PROCUREMENT', 'FINANCE', 'HR', 'LAB_TECH'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create tenants table (core SaaS table)
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            domain VARCHAR,
            company_code VARCHAR(6),
            tier subscriptiontier DEFAULT 'FREE_TRIAL',
            subscription_status VARCHAR DEFAULT 'active',
            stripe_customer_id VARCHAR,
            stripe_subscription_id VARCHAR,
            currency VARCHAR DEFAULT 'USD',
            timezone VARCHAR DEFAULT 'UTC',
            logo_url VARCHAR,
            is_setup_complete BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_domain ON tenants(domain)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_company_code ON tenants(company_code)")
    
    # Create users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR NOT NULL UNIQUE,
            email VARCHAR NOT NULL UNIQUE,
            password_hash VARCHAR NOT NULL,
            role userrole DEFAULT 'STAFF',
            tenant_id UUID REFERENCES tenants(id),
            is_verified BOOLEAN DEFAULT false,
            otp_code VARCHAR(6),
            otp_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users(username)")
    
    # Create tenant_members table (for multi-tenant membership)
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role memberrole NOT NULL DEFAULT 'member',
            invited_by UUID REFERENCES users(id),
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            joined_at TIMESTAMP,
            UNIQUE(tenant_id, user_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_members_tenant_id ON tenant_members(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_members_user_id ON tenant_members(user_id)")
    
    # Create work_centers table (for manufacturing work centers)
    op.execute("""
        CREATE TABLE IF NOT EXISTS work_centers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            cost_per_hour FLOAT DEFAULT 0.0,
            capacity_hours FLOAT DEFAULT 8.0,
            location VARCHAR,
            latitude FLOAT,
            longitude FLOAT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_work_centers_tenant_id ON work_centers(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_work_centers_code ON work_centers(code)")
    
    # Create menus table (for database-driven menu system)
    op.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code VARCHAR NOT NULL UNIQUE,
            label VARCHAR NOT NULL,
            icon VARCHAR,
            path VARCHAR,
            parent_id UUID REFERENCES menus(id),
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_menus_code ON menus(code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_menus_parent_id ON menus(parent_id)")
    
    # Create role_menu_permissions table (for role-based menu access per tenant)
    op.execute("""
        CREATE TABLE IF NOT EXISTS role_menu_permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL,
            menu_id UUID NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
            can_access BOOLEAN DEFAULT true
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_role_menu_permissions_tenant_id ON role_menu_permissions(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_role_menu_permissions_menu_id ON role_menu_permissions(menu_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS role_menu_permissions")
    op.execute("DROP TABLE IF EXISTS menus")
    op.execute("DROP TABLE IF EXISTS work_centers")
    op.execute("DROP TABLE IF EXISTS tenant_members")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP TYPE IF EXISTS memberrole")
    op.execute("DROP TYPE IF EXISTS subscriptiontier")
    op.execute("DROP TYPE IF EXISTS userrole")
