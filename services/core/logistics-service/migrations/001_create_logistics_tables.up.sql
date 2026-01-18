-- Migration: 001_create_logistics_tables.up.sql
-- Logistics Service Tables

CREATE TABLE IF NOT EXISTS delivery_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    do_number VARCHAR(50) NOT NULL,
    sales_order_id UUID,
    customer_id UUID,
    status VARCHAR(50) DEFAULT 'PENDING',
    delivery_date DATE,
    driver_id UUID,
    vehicle_id UUID,
    origin_address TEXT,
    destination_address TEXT,
    notes TEXT,
    total_weight DECIMAL(10,2),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    shipment_number VARCHAR(50),
    delivery_order_id UUID REFERENCES delivery_orders(id),
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'PENDING',
    estimated_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    cost DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_delivery_orders_tenant ON delivery_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_shipments_tenant ON shipments(tenant_id);
