-- Migration: 001_create_procurement_tables.up.sql
-- Procurement Service Tables

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    contact_person VARCHAR(255),
    tax_id VARCHAR(50),
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Purchase Requests
CREATE TABLE IF NOT EXISTS purchase_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    pr_number VARCHAR(50) NOT NULL,
    requested_by UUID,
    department VARCHAR(100),
    status VARCHAR(50) DEFAULT 'DRAFT',
    priority VARCHAR(20) DEFAULT 'NORMAL',
    required_date DATE,
    notes TEXT,
    total_amount DECIMAL(15,2),
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    po_number VARCHAR(50) NOT NULL,
    vendor_id UUID REFERENCES vendors(id),
    pr_id UUID REFERENCES purchase_requests(id),
    status VARCHAR(50) DEFAULT 'DRAFT',
    order_date DATE,
    expected_date DATE,
    shipping_address TEXT,
    subtotal DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    notes TEXT,
    created_by UUID,
    approved_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vendor Bills
CREATE TABLE IF NOT EXISTS vendor_bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    bill_number VARCHAR(50) NOT NULL,
    vendor_id UUID REFERENCES vendors(id),
    po_id UUID REFERENCES purchase_orders(id),
    bill_date DATE,
    due_date DATE,
    status VARCHAR(50) DEFAULT 'PENDING',
    subtotal DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    paid_amount DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vendors_tenant ON vendors(tenant_id);
CREATE INDEX IF NOT EXISTS idx_purchase_requests_tenant ON purchase_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_tenant ON purchase_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vendor_bills_tenant ON vendor_bills(tenant_id);
