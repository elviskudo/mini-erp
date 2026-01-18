-- Migration: 001_create_maintenance_tables.up.sql
-- Maintenance Service Tables

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    asset_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'OPERATIONAL',
    purchase_date DATE,
    purchase_cost DECIMAL(15,2),
    warranty_expiry DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS maintenance_work_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    wo_number VARCHAR(50) NOT NULL,
    asset_id UUID REFERENCES assets(id),
    type VARCHAR(50) DEFAULT 'CORRECTIVE',
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(50) DEFAULT 'OPEN',
    description TEXT,
    assigned_to UUID,
    scheduled_date DATE,
    completed_date DATE,
    labor_hours DECIMAL(5,2),
    labor_cost DECIMAL(15,2),
    parts_cost DECIMAL(15,2),
    total_cost DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    asset_id UUID REFERENCES assets(id),
    frequency VARCHAR(50),
    interval_days INTEGER,
    last_performed DATE,
    next_due DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assets_tenant ON assets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_tenant ON maintenance_work_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_schedules_tenant ON maintenance_schedules(tenant_id);
