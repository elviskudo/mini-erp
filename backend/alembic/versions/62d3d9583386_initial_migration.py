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


def downgrade() -> None:
    # Drop Maintenance module tables first (reverse order of creation)
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

