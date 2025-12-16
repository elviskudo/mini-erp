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
    op.execute("DO $$ BEGIN CREATE TYPE subscriptiontier AS ENUM ('FREE_TRIAL', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE memberrole AS ENUM ('OWNER', 'ADMIN', 'MEMBER', 'PENDING'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'OPERATOR', 'LAB_TECH'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
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
            role userrole DEFAULT 'OPERATOR',
            tenant_id UUID REFERENCES tenants(id),
            is_verified BOOLEAN DEFAULT false,
            otp_code VARCHAR(6),
            otp_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id)")
    
    # Create tenant_members table (for multi-tenant membership)
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            user_id UUID NOT NULL REFERENCES users(id),
            role memberrole NOT NULL,
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            joined_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_members_tenant_id ON tenant_members(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_members_user_id ON tenant_members(user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenant_members")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP TYPE IF EXISTS memberrole")
    op.execute("DROP TYPE IF EXISTS subscriptiontier")
    op.execute("DROP TYPE IF EXISTS userrole")
