-- Migration: 001_create_pos_tables.up.sql
-- POS Service Tables

CREATE TABLE IF NOT EXISTS pos_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    transaction_number VARCHAR(50) NOT NULL,
    terminal_id VARCHAR(50),
    cashier_id UUID,
    customer_id UUID,
    transaction_type VARCHAR(20) DEFAULT 'SALE',
    status VARCHAR(20) DEFAULT 'COMPLETED',
    subtotal DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    discount_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    change_amount DECIMAL(15,2),
    notes TEXT,
    transaction_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pos_transaction_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES pos_transactions(id),
    product_id UUID,
    product_name VARCHAR(255),
    quantity INTEGER,
    unit_price DECIMAL(15,2),
    discount DECIMAL(15,2),
    tax DECIMAL(15,2),
    total DECIMAL(15,2)
);

CREATE TABLE IF NOT EXISTS pos_promos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    type VARCHAR(50),
    value DECIMAL(15,2),
    min_purchase DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pos_transactions_tenant ON pos_transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pos_promos_tenant ON pos_promos(tenant_id);
