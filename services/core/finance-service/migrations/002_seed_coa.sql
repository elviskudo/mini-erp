-- Finance Service Database Migration
-- Version: 002
-- Description: Seed default Chart of Accounts template

-- Insert default COA for tenant (will be run per-tenant via /coa/seed endpoint)
-- This is a template showing the structure

-- For actual seeding, use the API endpoint POST /finance/coa/seed
-- which will create COA for the requesting tenant's tenant_id

-- Example seed for development/testing (replace tenant_id with actual UUID)
DO $$
DECLARE
    v_tenant_id UUID := '6c812e6d-da95-49e8-8510-cc36b196bdb6'; -- Default dev tenant
    v_assets_id UUID;
    v_current_assets_id UUID;
    v_fixed_assets_id UUID;
    v_liabilities_id UUID;
    v_equity_id UUID;
    v_revenue_id UUID;
    v_expenses_id UUID;
BEGIN
    -- Check if COA already seeded for this tenant
    IF EXISTS (SELECT 1 FROM chart_of_accounts WHERE tenant_id = v_tenant_id LIMIT 1) THEN
        RAISE NOTICE 'COA already seeded for tenant %', v_tenant_id;
        RETURN;
    END IF;

    -- ASSETS
    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '1000', 'ASSETS', 'Asset', NULL)
    RETURNING id INTO v_assets_id;

    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '1100', 'Current Assets', 'Asset', v_assets_id)
    RETURNING id INTO v_current_assets_id;

    INSERT INTO chart_of_accounts (tenant_id, code, name, type, parent_id)
    VALUES 
        (v_tenant_id, '1110', 'Cash & Bank', 'Asset', v_current_assets_id),
        (v_tenant_id, '1120', 'Accounts Receivable', 'Asset', v_current_assets_id),
        (v_tenant_id, '1130', 'Inventory', 'Asset', v_current_assets_id),
        (v_tenant_id, '1140', 'Prepaid Expenses', 'Asset', v_current_assets_id);

    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '1200', 'Fixed Assets', 'Asset', v_assets_id)
    RETURNING id INTO v_fixed_assets_id;

    INSERT INTO chart_of_accounts (tenant_id, code, name, type, parent_id)
    VALUES 
        (v_tenant_id, '1210', 'Equipment', 'Asset', v_fixed_assets_id),
        (v_tenant_id, '1220', 'Vehicles', 'Asset', v_fixed_assets_id),
        (v_tenant_id, '1230', 'Buildings', 'Asset', v_fixed_assets_id),
        (v_tenant_id, '1290', 'Accumulated Depreciation', 'Asset', v_fixed_assets_id);

    -- LIABILITIES
    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '2000', 'LIABILITIES', 'Liability', NULL)
    RETURNING id INTO v_liabilities_id;

    INSERT INTO chart_of_accounts (tenant_id, code, name, type, parent_id)
    VALUES 
        (v_tenant_id, '2100', 'Accounts Payable', 'Liability', v_liabilities_id),
        (v_tenant_id, '2200', 'Accrued Expenses', 'Liability', v_liabilities_id),
        (v_tenant_id, '2300', 'Tax Payable', 'Liability', v_liabilities_id),
        (v_tenant_id, '2400', 'Long Term Debt', 'Liability', v_liabilities_id);

    -- EQUITY
    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '3000', 'EQUITY', 'Equity', NULL)
    RETURNING id INTO v_equity_id;

    INSERT INTO chart_of_accounts (tenant_id, code, name, type, parent_id)
    VALUES 
        (v_tenant_id, '3100', 'Capital Stock', 'Equity', v_equity_id),
        (v_tenant_id, '3200', 'Retained Earnings', 'Equity', v_equity_id),
        (v_tenant_id, '3300', 'Current Year Earnings', 'Equity', v_equity_id);

    -- REVENUE
    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '4000', 'REVENUE', 'Income', NULL)
    RETURNING id INTO v_revenue_id;

    INSERT INTO chart_of_accounts (tenant_id, code, name, type, parent_id)
    VALUES 
        (v_tenant_id, '4100', 'Sales Revenue', 'Income', v_revenue_id),
        (v_tenant_id, '4200', 'Service Revenue', 'Income', v_revenue_id),
        (v_tenant_id, '4300', 'Other Income', 'Income', v_revenue_id),
        (v_tenant_id, '4400', 'Interest Income', 'Income', v_revenue_id);

    -- EXPENSES
    INSERT INTO chart_of_accounts (id, tenant_id, code, name, type, parent_id)
    VALUES (uuid_generate_v4(), v_tenant_id, '5000', 'EXPENSES', 'Expense', NULL)
    RETURNING id INTO v_expenses_id;

    INSERT INTO chart_of_accounts (tenant_id, code, name, type, parent_id)
    VALUES 
        (v_tenant_id, '5100', 'Cost of Goods Sold', 'Expense', v_expenses_id),
        (v_tenant_id, '5200', 'Salaries & Wages', 'Expense', v_expenses_id),
        (v_tenant_id, '5300', 'Rent Expense', 'Expense', v_expenses_id),
        (v_tenant_id, '5400', 'Utilities Expense', 'Expense', v_expenses_id),
        (v_tenant_id, '5500', 'Depreciation Expense', 'Expense', v_expenses_id),
        (v_tenant_id, '5600', 'Office Supplies', 'Expense', v_expenses_id),
        (v_tenant_id, '5700', 'Bank Fees', 'Expense', v_expenses_id),
        (v_tenant_id, '5800', 'Other Expenses', 'Expense', v_expenses_id);

    RAISE NOTICE 'COA seeded successfully for tenant %', v_tenant_id;
END $$;
