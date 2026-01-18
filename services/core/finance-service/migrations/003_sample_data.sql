-- Finance Service Database Migration
-- Version: 003  
-- Description: Sample data for development/testing

-- Insert sample bank accounts
INSERT INTO bank_accounts (id, tenant_id, code, name, bank_name, account_number, account_holder, account_type, currency_code, opening_balance, current_balance, is_active)
VALUES 
    ('11111111-1111-1111-1111-111111111111', '6c812e6d-da95-49e8-8510-cc36b196bdb6', 'BANK-001', 'BCA Operating', 'BCA', '1234567890', 'PT. Company', 'Checking', 'IDR', 100000000, 150000000, TRUE),
    ('22222222-2222-2222-2222-222222222222', '6c812e6d-da95-49e8-8510-cc36b196bdb6', 'BANK-002', 'Mandiri Savings', 'Mandiri', '0987654321', 'PT. Company', 'Savings', 'IDR', 50000000, 55000000, TRUE)
ON CONFLICT DO NOTHING;

-- Insert sample fiscal periods
INSERT INTO fiscal_periods (id, tenant_id, name, start_date, end_date, is_closed)
VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '6c812e6d-da95-49e8-8510-cc36b196bdb6', 'January 2024', '2024-01-01', '2024-01-31', TRUE),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '6c812e6d-da95-49e8-8510-cc36b196bdb6', 'February 2024', '2024-02-01', '2024-02-29', FALSE),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '6c812e6d-da95-49e8-8510-cc36b196bdb6', 'March 2024', '2024-03-01', '2024-03-31', FALSE)
ON CONFLICT DO NOTHING;

-- Insert sample bank transactions
INSERT INTO bank_transactions (tenant_id, bank_account_id, transaction_number, transaction_date, transaction_type, amount, running_balance, counterparty_name, description, is_reconciled)
VALUES
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', '11111111-1111-1111-1111-111111111111', 'TXN-20240115001', '2024-01-15 10:30:00+07', 'Deposit', 10000000, 110000000, 'Customer A', 'Payment for Invoice INV-001', TRUE),
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', '11111111-1111-1111-1111-111111111111', 'TXN-20240116001', '2024-01-16 14:00:00+07', 'Withdrawal', 5000000, 105000000, 'Vendor B', 'Payment for Bill BILL-001', FALSE),
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', '11111111-1111-1111-1111-111111111111', 'TXN-20240120001', '2024-01-20 09:00:00+07', 'Deposit', 15000000, 120000000, 'Customer B', 'Payment for Invoice INV-002', FALSE)
ON CONFLICT DO NOTHING;

-- Insert sample petty cash
INSERT INTO petty_cash (tenant_id, bank_account_id, transaction_number, transaction_date, is_replenishment, amount, category, description)
VALUES
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', '11111111-1111-1111-1111-111111111111', 'PC-REP-001', '2024-01-15 08:00:00+07', TRUE, 5000000, 'Replenishment', 'Initial petty cash fund'),
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', '11111111-1111-1111-1111-111111111111', 'PC-EXP-001', '2024-01-16 11:00:00+07', FALSE, 150000, 'Office Supplies', 'Purchase paper and pens'),
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', '11111111-1111-1111-1111-111111111111', 'PC-EXP-002', '2024-01-17 15:00:00+07', FALSE, 50000, 'Transportation', 'Taxi for meeting')
ON CONFLICT DO NOTHING;

-- Insert sample fixed asset
INSERT INTO fixed_assets (tenant_id, code, name, category, acquisition_date, acquisition_cost, salvage_value, useful_life_months, depreciation_method, accumulated_depreciation, book_value, status)
VALUES
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', 'FA-001', 'Office Computer', 'Equipment', '2024-01-01', 10000000, 1000000, 36, 'straight_line', 0, 10000000, 'active'),
    ('6c812e6d-da95-49e8-8510-cc36b196bdb6', 'FA-002', 'Company Vehicle', 'Vehicles', '2024-01-01', 200000000, 50000000, 60, 'straight_line', 0, 200000000, 'active')
ON CONFLICT DO NOTHING;
