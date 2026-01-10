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
            longitude FLOAT,
            is_active BOOLEAN DEFAULT true
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_work_centers_tenant_id ON work_centers(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_work_centers_code ON work_centers(code)")
    
    # Create producttype enum
    op.execute("DO $$ BEGIN CREATE TYPE producttype AS ENUM ('Raw Material', 'WIP', 'Finished Goods'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create products table
    op.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            type producttype DEFAULT 'Raw Material',
            uom VARCHAR DEFAULT 'pcs',
            is_manufactured BOOLEAN DEFAULT true,
            image_url TEXT,
            standard_cost FLOAT DEFAULT 0.0,
            weighted_avg_cost FLOAT DEFAULT 0.0,
            desired_margin FLOAT DEFAULT 0.3,
            suggested_selling_price FLOAT DEFAULT 0.0,
            requires_cold_chain BOOLEAN DEFAULT false,
            max_storage_temp FLOAT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_tenant_id ON products(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_code ON products(code)")
    
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
    
    # Create warehouses table
    op.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            address VARCHAR
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_warehouses_tenant_id ON warehouses(tenant_id)")
    
    # Create storage_zones table (for cold chain management)
    op.execute("""
        CREATE TABLE IF NOT EXISTS storage_zones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            zone_name VARCHAR NOT NULL,
            zone_type VARCHAR DEFAULT 'Ambient',
            min_temp FLOAT,
            max_temp FLOAT,
            capacity_units INTEGER DEFAULT 0,
            sensor_id VARCHAR,
            electricity_meter_id VARCHAR,
            electricity_tariff FLOAT DEFAULT 1500.0,
            daily_kwh_usage FLOAT DEFAULT 0.0,
            monthly_energy_cost FLOAT DEFAULT 0.0
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_storage_zones_tenant_id ON storage_zones(tenant_id)")
    
    # Create locationtype enum
    op.execute("DO $$ BEGIN CREATE TYPE locationtype AS ENUM ('STORAGE', 'RECEIVING', 'SHIPPING', 'PRODUCTION'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create locations table with zone_id
    op.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            zone_id UUID REFERENCES storage_zones(id),
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            type locationtype DEFAULT 'STORAGE'
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_locations_tenant_id ON locations(tenant_id)")
    
    # Create origintype enum for inventory batches
    op.execute("DO $$ BEGIN CREATE TYPE origintype AS ENUM ('PURCHASED', 'MANUFACTURED', 'TRANSFERRED', 'ADJUSTED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create inventory_batches table with all columns
    op.execute("""
        CREATE TABLE IF NOT EXISTS inventory_batches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            batch_number VARCHAR NOT NULL,
            quantity_on_hand FLOAT DEFAULT 0.0,
            expiration_date TIMESTAMP,
            location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
            origin_type origintype DEFAULT 'PURCHASED',
            unit_cost FLOAT DEFAULT 0.0,
            goods_receipt_id UUID,
            production_order_id UUID,
            vendor_id UUID,
            qr_code_data VARCHAR
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_inventory_batches_tenant_id ON inventory_batches(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_inventory_batches_batch_number ON inventory_batches(batch_number)")
    
    # Create movementtype enum with proper values
    op.execute("DO $$ BEGIN CREATE TYPE movementtype AS ENUM ('INBOUND', 'OUTBOUND', 'TRANSFER', 'ADJUSTMENT'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create stock_movements table
    op.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            batch_id UUID REFERENCES inventory_batches(id),
            location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
            quantity_change FLOAT NOT NULL,
            movement_type movementtype NOT NULL,
            reference_id VARCHAR,
            project_id VARCHAR,
            created_by UUID REFERENCES users(id),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes VARCHAR
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_stock_movements_tenant_id ON stock_movements(tenant_id)")
    
    # Create gatewaytype enum
    op.execute("DO $$ BEGIN CREATE TYPE gatewaytype AS ENUM ('Stripe', 'Midtrans', 'Xendit', 'PayPal', 'Manual'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create tenant_settings table
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_settings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id) UNIQUE NOT NULL,
            company_name VARCHAR,
            company_logo_url VARCHAR,
            industry VARCHAR,
            currency_code VARCHAR(3) DEFAULT 'IDR',
            currency_symbol VARCHAR(10) DEFAULT 'Rp',
            currency_position VARCHAR(10) DEFAULT 'before',
            decimal_separator VARCHAR(1) DEFAULT ',',
            thousand_separator VARCHAR(1) DEFAULT '.',
            decimal_places VARCHAR(1) DEFAULT '0',
            timezone VARCHAR DEFAULT 'Asia/Jakarta',
            date_format VARCHAR DEFAULT 'DD/MM/YYYY',
            setup_complete BOOLEAN DEFAULT false
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_settings_tenant_id ON tenant_settings(tenant_id)")
    
    # Create payment_gateways table
    op.execute("""
        CREATE TABLE IF NOT EXISTS payment_gateways (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id) NOT NULL,
            name VARCHAR NOT NULL,
            gateway_type gatewaytype DEFAULT 'Manual',
            api_key TEXT,
            api_secret TEXT,
            webhook_secret TEXT,
            is_active BOOLEAN DEFAULT true,
            is_sandbox BOOLEAN DEFAULT false,
            notes TEXT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payment_gateways_tenant_id ON payment_gateways(tenant_id)")
    
    # Create storagetype enum
    op.execute("DO $$ BEGIN CREATE TYPE storagetype AS ENUM ('Local', 'Cloudinary', 'AWS S3', 'Google Cloud Storage', 'Azure Blob Storage'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create storage_providers table
    op.execute("""
        CREATE TABLE IF NOT EXISTS storage_providers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id) NOT NULL,
            name VARCHAR NOT NULL,
            storage_type storagetype DEFAULT 'Local',
            bucket_name VARCHAR,
            region VARCHAR,
            base_url VARCHAR,
            api_key TEXT,
            api_secret TEXT,
            cloud_name VARCHAR,
            access_key_id VARCHAR,
            secret_access_key TEXT,
            is_active BOOLEAN DEFAULT true,
            is_default BOOLEAN DEFAULT false,
            notes TEXT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_storage_providers_tenant_id ON storage_providers(tenant_id)")
    
    # ============ Procurement Base Tables ============
    
    # Create vendor enums
    op.execute("DO $$ BEGIN CREATE TYPE vendorrating AS ENUM ('A', 'B', 'C'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE vendorcategory AS ENUM ('Raw Material', 'Finished Goods', 'Both'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE prstatus AS ENUM ('Draft', 'Pending Approval', 'Approved', 'Rejected', 'Converted'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE postatus AS ENUM ('Draft', 'Pending Approval', 'Open', 'Partial Receive', 'Closed', 'Cancelled'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create vendors table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            email VARCHAR,
            phone VARCHAR,
            address VARCHAR,
            rating vendorrating DEFAULT 'B',
            category vendorcategory DEFAULT 'Raw Material'
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendors_tenant_id ON vendors(tenant_id)")
    
    # Create purchase_requests table
    op.execute("""
        CREATE TABLE IF NOT EXISTS purchase_requests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            pr_number VARCHAR NOT NULL,
            requester_id UUID REFERENCES users(id),
            department VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            required_date TIMESTAMP,
            status prstatus DEFAULT 'Draft',
            notes VARCHAR
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_purchase_requests_tenant_id ON purchase_requests(tenant_id)")
    
    # Create pr_lines table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pr_lines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            pr_id UUID NOT NULL REFERENCES purchase_requests(id) ON DELETE CASCADE,
            product_id UUID REFERENCES products(id),
            quantity FLOAT NOT NULL,
            estimated_price FLOAT DEFAULT 0.0
        )
    """)
    
    # Create purchase_orders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            po_number VARCHAR NOT NULL,
            vendor_id UUID NOT NULL REFERENCES vendors(id),
            pr_id UUID REFERENCES purchase_requests(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expected_delivery TIMESTAMP,
            status postatus DEFAULT 'Draft',
            budget_checked BOOLEAN DEFAULT false,
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMP,
            subtotal FLOAT DEFAULT 0.0,
            shipping_cost FLOAT DEFAULT 0.0,
            insurance_cost FLOAT DEFAULT 0.0,
            customs_duty FLOAT DEFAULT 0.0,
            total_amount FLOAT DEFAULT 0.0,
            notes VARCHAR
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_purchase_orders_tenant_id ON purchase_orders(tenant_id)")
    
    # Create po_lines table
    op.execute("""
        CREATE TABLE IF NOT EXISTS po_lines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
            product_id UUID REFERENCES products(id),
            quantity FLOAT NOT NULL,
            received_qty FLOAT DEFAULT 0.0,
            unit_price FLOAT DEFAULT 0.0,
            line_total FLOAT DEFAULT 0.0
        )
    """)
    
    # ============ Procurement Enhancement ============
    
    # Create payment enums
    op.execute("DO $$ BEGIN CREATE TYPE paymentterm AS ENUM ('Cash', 'Net 7', 'Net 15', 'Net 30', 'Net 60', '3 Termin', '6 Termin', '12 Termin'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE paymentstatus AS ENUM ('Unpaid', 'Partial', 'Paid'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Add payment fields to vendors
    op.execute("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS payment_term paymentterm DEFAULT 'Net 30'")
    op.execute("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS credit_limit FLOAT DEFAULT 0.0")
    
    # Add payment and progress fields to purchase_orders
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS payment_term paymentterm DEFAULT 'Net 30'")
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS due_date TIMESTAMP")
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS amount_paid FLOAT DEFAULT 0.0")
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS payment_status paymentstatus DEFAULT 'Unpaid'")
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS progress FLOAT DEFAULT 0.0")
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS current_approval_level INTEGER DEFAULT 0")
    op.execute("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS required_approval_level INTEGER DEFAULT 1")
    
    # ============ Approval Workflow ============
    
    # Create approval enums
    op.execute("DO $$ BEGIN CREATE TYPE approvalstatus AS ENUM ('Pending', 'Approved', 'Rejected'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE entitytype AS ENUM ('PurchaseOrder', 'PurchaseRequest', 'Payment', 'Expense'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create approval_levels table
    op.execute("""
        CREATE TABLE IF NOT EXISTS approval_levels (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id) NOT NULL,
            level INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            min_amount FLOAT DEFAULT 0.0,
            max_amount FLOAT,
            role_id UUID REFERENCES roles(id),
            description VARCHAR,
            is_active BOOLEAN DEFAULT true
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_levels_tenant_id ON approval_levels(tenant_id)")
    
    # Create approval_history table
    op.execute("""
        CREATE TABLE IF NOT EXISTS approval_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id) NOT NULL,
            entity_type entitytype NOT NULL,
            entity_id UUID NOT NULL,
            level INTEGER NOT NULL,
            approved_by UUID REFERENCES users(id),
            status approvalstatus DEFAULT 'Pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_history_tenant_id ON approval_history(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_history_entity_id ON approval_history(entity_id)")
    
    # ============ Projects Module ============
    
    # Create project enums
    op.execute("DO $$ BEGIN CREATE TYPE projecttype AS ENUM ('R_AND_D', 'CUSTOMER_ORDER', 'INTERNAL_IMPROVEMENT', 'MAINTENANCE', 'CONSULTING'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE projectstatus AS ENUM ('DRAFT', 'PLANNING', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE projectpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE expensecategory AS ENUM ('MATERIAL', 'LABOR', 'EQUIPMENT', 'TRAVEL', 'SOFTWARE', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pmemberrole AS ENUM ('PROJECT_MANAGER', 'TEAM_LEAD', 'DEVELOPER', 'DESIGNER', 'QA', 'MEMBER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create projects table
    op.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            code VARCHAR,
            description TEXT,
            type projecttype DEFAULT 'INTERNAL_IMPROVEMENT',
            status projectstatus DEFAULT 'DRAFT',
            priority projectpriority DEFAULT 'MEDIUM',
            manager_id UUID REFERENCES users(id),
            client_id UUID,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            actual_end_date TIMESTAMP,
            budget FLOAT DEFAULT 0.0,
            tags JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_tenant_id ON projects(tenant_id)")
    
    # Create project_tasks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_tasks (
            id VARCHAR PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            description TEXT,
            wbs_code VARCHAR,
            status VARCHAR DEFAULT 'TODO',
            priority VARCHAR DEFAULT 'MEDIUM',
            parent_id VARCHAR REFERENCES project_tasks(id),
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            progress FLOAT DEFAULT 0.0,
            estimated_hours FLOAT DEFAULT 0.0,
            actual_hours FLOAT DEFAULT 0.0,
            assigned_to UUID REFERENCES users(id),
            dependencies JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_tasks_tenant_id ON project_tasks(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_tasks_project_id ON project_tasks(project_id)")
    
    # Create project_members table
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id),
            role pmemberrole DEFAULT 'MEMBER',
            hourly_rate FLOAT DEFAULT 0.0,
            joined_at TIMESTAMP DEFAULT NOW(),
            is_active BOOLEAN DEFAULT true
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_members_tenant_id ON project_members(tenant_id)")
    
    # Create time_entries table
    op.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            task_id VARCHAR REFERENCES project_tasks(id) ON DELETE SET NULL,
            user_id UUID NOT NULL REFERENCES users(id),
            date DATE NOT NULL,
            hours FLOAT NOT NULL,
            description TEXT,
            billable BOOLEAN DEFAULT true,
            billed BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_time_entries_tenant_id ON time_entries(tenant_id)")
    
    # Create project_expenses table
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_expenses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            description VARCHAR NOT NULL,
            category expensecategory DEFAULT 'OTHER',
            amount FLOAT NOT NULL,
            date DATE NOT NULL,
            receipt_url VARCHAR,
            notes TEXT,
            submitted_by UUID REFERENCES users(id),
            approved BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_expenses_tenant_id ON project_expenses(tenant_id)")
    
    # Create task_assignees table (many-to-many task-user assignment)
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_assignees (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            task_id VARCHAR NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id),
            assigned_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(task_id, user_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_assignees_tenant_id ON task_assignees(tenant_id)")
    
    # Create task_comments table
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_comments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            task_id VARCHAR NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            parent_id UUID REFERENCES task_comments(id),
            reactions JSON DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_comments_tenant_id ON task_comments(tenant_id)")

    # Create task_attachments table
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_attachments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            task_id VARCHAR NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id),
            file_name VARCHAR NOT NULL,
            file_url VARCHAR NOT NULL,
            file_type VARCHAR,
            file_size INTEGER,
            public_id VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_attachments_task_id ON task_attachments(task_id)")

    # ==================== MAINTENANCE MODULE ====================

    # Create assets table
    op.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            category VARCHAR,
            location VARCHAR,
            status VARCHAR DEFAULT 'OPERATIONAL',
            purchase_date DATE,
            purchase_cost FLOAT DEFAULT 0,
            serial_number VARCHAR,
            manufacturer VARCHAR,
            model VARCHAR,
            warranty_expiry DATE,
            notes TEXT,
            image_url VARCHAR,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_tenant_id ON assets(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_code ON assets(code)")

    # Create maintenance_types table
    op.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_types (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            is_scheduled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_types_tenant_id ON maintenance_types(tenant_id)")

    # Create maintenance_work_orders table (new structure for maintenance)
    op.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_work_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            asset_id UUID REFERENCES assets(id),
            type_id UUID REFERENCES maintenance_types(id),
            title VARCHAR NOT NULL,
            description TEXT,
            priority VARCHAR DEFAULT 'MEDIUM',
            status VARCHAR DEFAULT 'DRAFT',
            scheduled_date TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            assigned_to UUID REFERENCES users(id),
            reported_by UUID REFERENCES users(id),
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_work_orders_tenant_id ON maintenance_work_orders(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_work_orders_code ON maintenance_work_orders(code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_work_orders_asset_id ON maintenance_work_orders(asset_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_work_orders_status ON maintenance_work_orders(status)")

    # Create maintenance_work_order_tasks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_work_order_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            work_order_id UUID NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            completed_by UUID REFERENCES users(id)
        )
    """)

    # Create maintenance_work_order_parts table
    op.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_work_order_parts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            work_order_id UUID NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
            part_name VARCHAR NOT NULL,
            part_number VARCHAR,
            quantity INTEGER DEFAULT 1,
            unit_cost FLOAT DEFAULT 0,
            total_cost FLOAT DEFAULT 0
        )
    """)

    # Create maintenance_work_order_costs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_work_order_costs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            work_order_id UUID NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
            category VARCHAR DEFAULT 'OTHER',
            description VARCHAR NOT NULL,
            amount FLOAT DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE
        )
    """)

    # Create maintenance_schedules table
    op.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            asset_id UUID NOT NULL REFERENCES assets(id),
            type_id UUID REFERENCES maintenance_types(id),
            title VARCHAR NOT NULL,
            description TEXT,
            frequency VARCHAR DEFAULT 'MONTHLY',
            interval_days INTEGER DEFAULT 30,
            last_performed DATE,
            next_due DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_schedules_tenant_id ON maintenance_schedules(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_schedules_asset_id ON maintenance_schedules(asset_id)")

    # ==================== FLEET MANAGEMENT MODULE ====================

    # Create Fleet enums
    op.execute("DO $$ BEGIN CREATE TYPE vehiclestatus AS ENUM ('AVAILABLE', 'IN_USE', 'MAINTENANCE', 'BROKEN', 'RETIRED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE vehiclecategory AS ENUM ('OPERATIONAL', 'LOGISTICS', 'RENTAL', 'EXECUTIVE', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE bookingstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'IN_USE', 'COMPLETED', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE bookingpurpose AS ENUM ('BUSINESS_TRIP', 'DELIVERY', 'CLIENT_VISIT', 'SITE_INSPECTION', 'PICKUP', 'EVENT', 'TRAINING', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE origintype AS ENUM ('WAREHOUSE', 'STORAGE_ZONE', 'MANUAL'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE fleetexpensecategory AS ENUM ('FUEL', 'TOLL', 'PARKING', 'SERVICE', 'TAX', 'INSURANCE', 'KIR', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE remindertype AS ENUM ('TAX', 'SERVICE', 'INSURANCE', 'KIR', 'STNK', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create fleet_departments table
    op.execute("""
        CREATE TABLE IF NOT EXISTS fleet_departments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_fleet_departments_tenant_id ON fleet_departments(tenant_id)")

    # Create fleet_drivers table
    op.execute("""
        CREATE TABLE IF NOT EXISTS fleet_drivers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            phone VARCHAR,
            email VARCHAR,
            card_id_url VARCHAR,
            card_id_number VARCHAR,
            employment_status VARCHAR,
            license_number VARCHAR,
            license_type VARCHAR,
            license_expiry DATE,
            address TEXT,
            photo_url VARCHAR,
            qr_code TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_fleet_drivers_tenant_id ON fleet_drivers(tenant_id)")

    # Create fleet_vendors table
    op.execute("""
        CREATE TABLE IF NOT EXISTS fleet_vendors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            contact_person VARCHAR,
            phone VARCHAR,
            email VARCHAR,
            address TEXT,
            city VARCHAR,
            service_types VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_fleet_vendors_tenant_id ON fleet_vendors(tenant_id)")

    # Create vehicles table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR NOT NULL,
            plate_number VARCHAR NOT NULL,
            brand VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            year INTEGER,
            color VARCHAR,
            vehicle_type VARCHAR,
            category vehiclecategory DEFAULT 'OPERATIONAL',
            capacity VARCHAR,
            fuel_type VARCHAR DEFAULT 'Gasoline',
            chassis_number VARCHAR,
            engine_number VARCHAR,
            stnk_number VARCHAR,
            bpkb_number VARCHAR,
            status vehiclestatus DEFAULT 'AVAILABLE',
            current_odometer FLOAT DEFAULT 0,
            purchase_date DATE,
            purchase_cost FLOAT DEFAULT 0,
            stnk_url VARCHAR,
            bpkb_url VARCHAR,
            insurance_url VARCHAR,
            image_url VARCHAR,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_tenant_id ON vehicles(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_code ON vehicles(code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicles_plate_number ON vehicles(plate_number)")

    # Create bookingorigintype enum for vehicle bookings
    op.execute("DO $$ BEGIN CREATE TYPE bookingorigintype AS ENUM ('WAREHOUSE', 'STORAGE_ZONE', 'MANUAL'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create vehicle_bookings table with new columns
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_bookings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            code VARCHAR NOT NULL,
            purpose bookingpurpose DEFAULT 'BUSINESS_TRIP',
            origin_type bookingorigintype DEFAULT 'MANUAL',
            origin_warehouse_id UUID REFERENCES warehouses(id),
            origin_zone_id UUID REFERENCES storage_zones(id),
            origin_address VARCHAR,
            origin_lat FLOAT,
            origin_lng FLOAT,
            destination VARCHAR NOT NULL,
            destination_lat FLOAT,
            destination_lng FLOAT,
            start_datetime TIMESTAMP NOT NULL,
            end_datetime TIMESTAMP NOT NULL,
            actual_start TIMESTAMP,
            actual_end TIMESTAMP,
            start_odometer FLOAT,
            end_odometer FLOAT,
            requested_by UUID REFERENCES users(id),
            driver_id UUID REFERENCES fleet_drivers(id),
            department_id UUID REFERENCES fleet_departments(id),
            project_id VARCHAR,
            status bookingstatus DEFAULT 'PENDING',
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMP,
            rejected_by UUID REFERENCES users(id),
            rejected_at TIMESTAMP,
            reject_reason TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_bookings_tenant_id ON vehicle_bookings(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_bookings_vehicle_id ON vehicle_bookings(vehicle_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_bookings_status ON vehicle_bookings(status)")


    # Create vehicle_fuel_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_fuel_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            driver_id UUID REFERENCES fleet_drivers(id),
            date DATE NOT NULL,
            odometer FLOAT NOT NULL,
            fuel_type VARCHAR DEFAULT 'Gasoline',
            liters FLOAT NOT NULL,
            price_per_liter FLOAT NOT NULL,
            total_cost FLOAT NOT NULL,
            gas_station VARCHAR NOT NULL,
            lat FLOAT,
            lng FLOAT,
            distance_traveled FLOAT,
            fuel_efficiency FLOAT,
            recorded_by UUID REFERENCES users(id),
            notes TEXT,
            receipt_url VARCHAR NOT NULL,
            invoice_number VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_fuel_logs_tenant_id ON vehicle_fuel_logs(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_fuel_logs_vehicle_id ON vehicle_fuel_logs(vehicle_id)")


    # Create vehicle_maintenance_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_maintenance_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            vendor_id UUID NOT NULL REFERENCES fleet_vendors(id),
            date DATE NOT NULL,
            odometer FLOAT NOT NULL,
            service_type VARCHAR NOT NULL,
            description TEXT NOT NULL,
            lat FLOAT,
            lng FLOAT,
            parts_cost FLOAT NOT NULL DEFAULT 0,
            labor_cost FLOAT NOT NULL DEFAULT 0,
            total_cost FLOAT NOT NULL DEFAULT 0,
            next_service_date DATE NOT NULL,
            next_service_odometer FLOAT,
            performed_by VARCHAR,
            recorded_by UUID REFERENCES users(id),
            invoice_number VARCHAR,
            receipt_url VARCHAR,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_maintenance_logs_tenant_id ON vehicle_maintenance_logs(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_maintenance_logs_vehicle_id ON vehicle_maintenance_logs(vehicle_id)")


    # Create vehicle_expenses table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_expenses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            category fleetexpensecategory DEFAULT 'OTHER',
            description VARCHAR NOT NULL,
            amount FLOAT NOT NULL,
            booking_id UUID REFERENCES vehicle_bookings(id),
            recorded_by UUID REFERENCES users(id),
            receipt_url VARCHAR,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_expenses_tenant_id ON vehicle_expenses(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_expenses_vehicle_id ON vehicle_expenses(vehicle_id)")

    # Create vehicle_reminders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_reminders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            reminder_type remindertype NOT NULL,
            title VARCHAR NOT NULL,
            description TEXT,
            due_date DATE NOT NULL,
            remind_days_before INTEGER DEFAULT 30,
            estimated_cost FLOAT,
            reference_number VARCHAR,
            document_url VARCHAR,
            is_notified BOOLEAN DEFAULT FALSE,
            is_completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            completed_by UUID REFERENCES users(id),
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_reminders_tenant_id ON vehicle_reminders(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_reminders_vehicle_id ON vehicle_reminders(vehicle_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vehicle_reminders_due_date ON vehicle_reminders(due_date)")

    # Create documenttype enum for fleet invoices
    op.execute("DO $$ BEGIN CREATE TYPE documenttype AS ENUM ('MAINTENANCE_INVOICE', 'EXPENSE_RECEIPT', 'FUEL_RECEIPT', 'STNK', 'DRIVER_LICENSE', 'KIR', 'INSURANCE', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create fleet_invoices table for extracted document data
    op.execute("""
        CREATE TABLE IF NOT EXISTS fleet_invoices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            document_type documenttype NOT NULL,
            source_table VARCHAR,
            source_id UUID,
            file_url VARCHAR NOT NULL,
            file_name VARCHAR,
            invoice_number VARCHAR,
            vendor_name VARCHAR,
            invoice_date DATE,
            subtotal FLOAT,
            tax_amount FLOAT,
            total_amount FLOAT,
            currency VARCHAR DEFAULT 'IDR',
            document_number VARCHAR,
            expiry_date DATE,
            holder_name VARCHAR,
            line_items TEXT,
            raw_extracted_text TEXT,
            extraction_confidence FLOAT,
            is_valid_document BOOLEAN DEFAULT TRUE,
            validation_message VARCHAR,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_fleet_invoices_tenant_id ON fleet_invoices(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_fleet_invoices_source ON fleet_invoices(source_table, source_id)")

    # ==================== HR & PAYROLL MODULE ====================
    
    # Create HR enums
    op.execute("DO $$ BEGIN CREATE TYPE employeestatus AS ENUM ('ACTIVE', 'INACTIVE', 'ON_LEAVE', 'TERMINATED', 'PROBATION'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE contracttype AS ENUM ('PERMANENT', 'CONTRACT', 'PROBATION', 'INTERNSHIP', 'PART_TIME'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE gender AS ENUM ('MALE', 'FEMALE', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE maritalstatus AS ENUM ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE attendancestatus AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'ON_LEAVE', 'HOLIDAY', 'WEEKEND'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE checkinmethod AS ENUM ('FACE', 'FINGERPRINT', 'MANUAL', 'QR_CODE', 'MOBILE'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE leavestatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE payrollstatus AS ENUM ('DRAFT', 'CALCULATED', 'APPROVED', 'PAID', 'CANCELLED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE cameratype AS ENUM ('WEBCAM', 'CCTV', 'IP_CAMERA', 'USB_CAMERA'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE activitytype AS ENUM ('WORKING', 'IDLE', 'AWAY', 'MEETING', 'BREAK'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create hr_departments table
    op.execute("""
        CREATE TABLE IF NOT EXISTS hr_departments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            code VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            manager_id UUID REFERENCES users(id),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_hr_departments_tenant_id ON hr_departments(tenant_id)")

    # Create hr_positions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS hr_positions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            code VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            department_id UUID REFERENCES hr_departments(id),
            level INTEGER DEFAULT 1,
            base_salary FLOAT DEFAULT 0.0,
            min_salary FLOAT,
            max_salary FLOAT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_hr_positions_tenant_id ON hr_positions(tenant_id)")

    # Create employees table (enhanced)
    op.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_code VARCHAR(20) NOT NULL UNIQUE,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            nik VARCHAR(20),
            npwp VARCHAR(30),
            birth_date DATE,
            birth_place VARCHAR(100),
            gender gender,
            marital_status maritalstatus,
            religion VARCHAR(50),
            blood_type VARCHAR(5),
            address TEXT,
            city VARCHAR(100),
            province VARCHAR(100),
            postal_code VARCHAR(10),
            profile_photo_url VARCHAR(500),
            id_card_photo_url VARCHAR(500),
            face_encoding TEXT,
            fingerprint_data TEXT,
            department_id UUID REFERENCES hr_departments(id),
            position_id UUID REFERENCES hr_positions(id),
            manager_id UUID REFERENCES employees(id),
            hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
            termination_date DATE,
            contract_type contracttype DEFAULT 'PERMANENT',
            contract_start DATE,
            contract_end DATE,
            status employeestatus DEFAULT 'ACTIVE',
            base_salary FLOAT DEFAULT 0.0,
            bank_name VARCHAR(100),
            bank_account VARCHAR(50),
            bank_account_name VARCHAR(100),
            bpjs_kesehatan VARCHAR(30),
            bpjs_ketenagakerjaan VARCHAR(30),
            emergency_contact_name VARCHAR(100),
            emergency_contact_phone VARCHAR(20),
            emergency_contact_relation VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_employees_tenant_id ON employees(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_employees_employee_code ON employees(employee_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_employees_email ON employees(email)")

    # hr_departments manager_id already references users(id) directly in table creation

    # Create employee_documents table
    op.execute("""
        CREATE TABLE IF NOT EXISTS employee_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            document_type VARCHAR(50) NOT NULL,
            document_name VARCHAR(255) NOT NULL,
            file_url VARCHAR(500) NOT NULL,
            expiry_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            uploaded_by UUID REFERENCES users(id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_employee_documents_employee_id ON employee_documents(employee_id)")

    # Create hr_shifts table
    op.execute("""
        CREATE TABLE IF NOT EXISTS hr_shifts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR(50) NOT NULL,
            code VARCHAR(10) NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            break_start TIME,
            break_end TIME,
            late_tolerance_minutes INTEGER DEFAULT 15,
            early_leave_tolerance INTEGER DEFAULT 15,
            is_overnight BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_hr_shifts_tenant_id ON hr_shifts(tenant_id)")

    # Create employee_schedules table
    op.execute("""
        CREATE TABLE IF NOT EXISTS employee_schedules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            shift_id UUID NOT NULL REFERENCES hr_shifts(id),
            date DATE NOT NULL,
            is_holiday BOOLEAN DEFAULT FALSE,
            notes VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_employee_schedules_employee_id ON employee_schedules(employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_employee_schedules_date ON employee_schedules(date)")

    # Create attendances table
    op.execute("""
        CREATE TABLE IF NOT EXISTS attendances (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            shift_id UUID REFERENCES hr_shifts(id),
            check_in TIMESTAMP,
            check_in_method checkinmethod DEFAULT 'MANUAL',
            check_in_photo_url VARCHAR(500),
            check_in_location VARCHAR(255),
            check_in_device VARCHAR(100),
            check_out TIMESTAMP,
            check_out_method checkinmethod,
            check_out_photo_url VARCHAR(500),
            check_out_location VARCHAR(255),
            check_out_device VARCHAR(100),
            status attendancestatus DEFAULT 'ABSENT',
            late_minutes INTEGER DEFAULT 0,
            early_leave_minutes INTEGER DEFAULT 0,
            overtime_minutes INTEGER DEFAULT 0,
            work_hours FLOAT DEFAULT 0.0,
            notes TEXT,
            approved_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendances_tenant_id ON attendances(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendances_employee_id ON attendances(employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendances_date ON attendances(date)")

    # Create leave_types table
    op.execute("""
        CREATE TABLE IF NOT EXISTS leave_types (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR(50) NOT NULL,
            code VARCHAR(10) NOT NULL,
            annual_quota INTEGER DEFAULT 12,
            is_paid BOOLEAN DEFAULT TRUE,
            requires_document BOOLEAN DEFAULT FALSE,
            max_consecutive_days INTEGER,
            color VARCHAR(7) DEFAULT '#3B82F6',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_leave_types_tenant_id ON leave_types(tenant_id)")

    # Create leave_balances table
    op.execute("""
        CREATE TABLE IF NOT EXISTS leave_balances (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            leave_type_id UUID NOT NULL REFERENCES leave_types(id),
            year INTEGER NOT NULL,
            quota INTEGER DEFAULT 0,
            used INTEGER DEFAULT 0,
            carried_forward INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_leave_balances_employee_id ON leave_balances(employee_id)")

    # Create leave_requests table
    op.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            leave_type_id UUID NOT NULL REFERENCES leave_types(id),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_days INTEGER NOT NULL,
            reason TEXT,
            attachment_url VARCHAR(500),
            status leavestatus DEFAULT 'PENDING',
            approver_id UUID REFERENCES users(id),
            approved_at TIMESTAMP,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_leave_requests_employee_id ON leave_requests(employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leave_requests_status ON leave_requests(status)")

    # Create salary_components table
    op.execute("""
        CREATE TABLE IF NOT EXISTS salary_components (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(20) NOT NULL,
            component_type VARCHAR(20) NOT NULL,
            is_taxable BOOLEAN DEFAULT TRUE,
            is_fixed BOOLEAN DEFAULT TRUE,
            default_amount FLOAT DEFAULT 0.0,
            calculation_formula TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_salary_components_tenant_id ON salary_components(tenant_id)")

    # Create employee_salary_components table
    op.execute("""
        CREATE TABLE IF NOT EXISTS employee_salary_components (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            component_id UUID NOT NULL REFERENCES salary_components(id),
            amount FLOAT NOT NULL,
            effective_from DATE NOT NULL,
            effective_to DATE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_employee_salary_components_employee_id ON employee_salary_components(employee_id)")

    # Create payroll_periods table
    op.execute("""
        CREATE TABLE IF NOT EXISTS payroll_periods (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR(50),
            period_month INTEGER NOT NULL,
            period_year INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            payment_date DATE,
            status payrollstatus DEFAULT 'DRAFT',
            is_closed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payroll_periods_tenant_id ON payroll_periods(tenant_id)")

    # Create payroll_runs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS payroll_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            payroll_period_id UUID REFERENCES payroll_periods(id),
            run_date TIMESTAMP DEFAULT NOW(),
            run_by UUID REFERENCES users(id),
            status payrollstatus DEFAULT 'DRAFT',
            total_employees INTEGER DEFAULT 0,
            total_gross FLOAT DEFAULT 0.0,
            total_deductions FLOAT DEFAULT 0.0,
            total_net FLOAT DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payroll_runs_tenant_id ON payroll_runs(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payroll_runs_period_id ON payroll_runs(payroll_period_id)")

    # Create payslips table
    op.execute("""
        CREATE TABLE IF NOT EXISTS payslips (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            payroll_run_id UUID REFERENCES payroll_runs(id),
            employee_id UUID REFERENCES employees(id),
            base_salary FLOAT DEFAULT 0.0,
            allowances FLOAT DEFAULT 0.0,
            overtime_pay FLOAT DEFAULT 0.0,
            bonus FLOAT DEFAULT 0.0,
            gross_pay FLOAT DEFAULT 0.0,
            tax_deduction FLOAT DEFAULT 0.0,
            bpjs_kes_deduction FLOAT DEFAULT 0.0,
            bpjs_tk_deduction FLOAT DEFAULT 0.0,
            other_deductions FLOAT DEFAULT 0.0,
            total_deductions FLOAT DEFAULT 0.0,
            net_pay FLOAT DEFAULT 0.0,
            earnings_detail JSONB,
            deductions_detail JSONB,
            is_paid BOOLEAN DEFAULT FALSE,
            paid_at TIMESTAMP,
            payment_method VARCHAR(50),
            payment_reference VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payslips_tenant_id ON payslips(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payslips_employee_id ON payslips(employee_id)")

    # Create hr_kpis table
    op.execute("""
        CREATE TABLE IF NOT EXISTS hr_kpis (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            period_year INTEGER NOT NULL,
            period_quarter INTEGER,
            metric_name VARCHAR(200) NOT NULL,
            metric_description TEXT,
            target_value FLOAT NOT NULL,
            actual_value FLOAT,
            weight FLOAT DEFAULT 1.0,
            unit VARCHAR(20),
            score FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_hr_kpis_employee_id ON hr_kpis(employee_id)")

    # Create performance_reviews table
    op.execute("""
        CREATE TABLE IF NOT EXISTS performance_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            reviewer_id UUID NOT NULL REFERENCES users(id),
            period_year INTEGER NOT NULL,
            period_type VARCHAR(20) NOT NULL,
            kpi_score FLOAT,
            competency_score FLOAT,
            overall_score FLOAT,
            rating VARCHAR(20),
            strengths TEXT,
            areas_for_improvement TEXT,
            goals_next_period TEXT,
            employee_feedback TEXT,
            status VARCHAR(20) DEFAULT 'DRAFT',
            submitted_at TIMESTAMP,
            acknowledged_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_performance_reviews_employee_id ON performance_reviews(employee_id)")

    # Create office_cameras table
    op.execute("""
        CREATE TABLE IF NOT EXISTS office_cameras (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(200),
            description TEXT,
            camera_type cameratype DEFAULT 'WEBCAM',
            stream_url VARCHAR(500),
            device_id VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            is_ai_enabled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_office_cameras_tenant_id ON office_cameras(tenant_id)")

    # Create camera_activities table
    op.execute("""
        CREATE TABLE IF NOT EXISTS camera_activities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            camera_id UUID NOT NULL REFERENCES office_cameras(id) ON DELETE CASCADE,
            timestamp TIMESTAMP DEFAULT NOW(),
            activity_type activitytype,
            employee_detected_id UUID REFERENCES employees(id),
            people_count INTEGER DEFAULT 0,
            snapshot_url VARCHAR(500),
            confidence_score FLOAT,
            activity_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_camera_activities_camera_id ON camera_activities(camera_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_camera_activities_timestamp ON camera_activities(timestamp)")


def downgrade() -> None:
    # Drop Fleet module tables first (reverse order of creation)
    op.execute("DROP TABLE IF EXISTS fleet_invoices")
    op.execute("DROP TYPE IF EXISTS documenttype")
    op.execute("DROP TABLE IF EXISTS vehicle_reminders")
    op.execute("DROP TABLE IF EXISTS vehicle_expenses")
    op.execute("DROP TABLE IF EXISTS vehicle_maintenance_logs")
    op.execute("DROP TABLE IF EXISTS vehicle_fuel_logs")
    op.execute("DROP TABLE IF EXISTS vehicle_bookings")
    op.execute("DROP TABLE IF EXISTS vehicles CASCADE")
    op.execute("DROP TABLE IF EXISTS fleet_vendors")
    op.execute("DROP TABLE IF EXISTS fleet_drivers")
    op.execute("DROP TABLE IF EXISTS fleet_departments")
    op.execute("DROP TYPE IF EXISTS remindertype")
    op.execute("DROP TYPE IF EXISTS fleetexpensecategory")
    op.execute("DROP TYPE IF EXISTS origintype")
    op.execute("DROP TYPE IF EXISTS bookingpurpose")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS vehiclecategory")
    op.execute("DROP TYPE IF EXISTS vehiclestatus")
    
    # Drop Maintenance module tables (reverse order of creation)
    op.execute("DROP TABLE IF EXISTS maintenance_schedules")
    op.execute("DROP TABLE IF EXISTS maintenance_work_order_costs")
    op.execute("DROP TABLE IF EXISTS maintenance_work_order_parts")
    op.execute("DROP TABLE IF EXISTS maintenance_work_order_tasks")
    op.execute("DROP TABLE IF EXISTS maintenance_work_orders CASCADE")
    op.execute("DROP TABLE IF EXISTS maintenance_types")
    op.execute("DROP TABLE IF EXISTS assets CASCADE")
    op.execute("DROP TABLE IF EXISTS task_attachments")
    op.execute("DROP TABLE IF EXISTS task_comments")
    op.execute("DROP TABLE IF EXISTS task_assignees")

    
    # Drop Projects module tables
    op.execute("DROP TABLE IF EXISTS project_expenses")
    op.execute("DROP TABLE IF EXISTS time_entries")
    op.execute("DROP TABLE IF EXISTS project_members")
    op.execute("DROP TABLE IF EXISTS project_tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS projects CASCADE")
    
    # Drop other tables
    op.execute("DROP TABLE IF EXISTS storage_providers")
    op.execute("DROP TYPE IF EXISTS storagetype")
    op.execute("DROP TABLE IF EXISTS payment_gateways")
    op.execute("DROP TABLE IF EXISTS tenant_settings")
    op.execute("DROP TYPE IF EXISTS gatewaytype")
    op.execute("DROP TABLE IF EXISTS stock_movements")
    op.execute("DROP TABLE IF EXISTS inventory_batches")
    op.execute("DROP TABLE IF EXISTS locations")
    op.execute("DROP TABLE IF EXISTS storage_zones")
    op.execute("DROP TABLE IF EXISTS warehouses")
    op.execute("DROP TABLE IF EXISTS role_menu_permissions")
    op.execute("DROP TABLE IF EXISTS menus")
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS work_centers")
    op.execute("DROP TABLE IF EXISTS tenant_members")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP TYPE IF EXISTS movementtype")
    op.execute("DROP TYPE IF EXISTS origintype")
    op.execute("DROP TYPE IF EXISTS locationtype")
    op.execute("DROP TYPE IF EXISTS producttype")
    op.execute("DROP TYPE IF EXISTS memberrole")
    op.execute("DROP TYPE IF EXISTS subscriptiontier")
    op.execute("DROP TYPE IF EXISTS userrole")

