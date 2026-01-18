-- Finance Service Database Migration
-- Version: 001
-- Description: Initial tables for Finance Service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========== CHART OF ACCOUNTS ==========
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Asset', 'Liability', 'Equity', 'Income', 'Expense')),
    parent_id UUID REFERENCES chart_of_accounts(id) ON DELETE SET NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_coa_tenant ON chart_of_accounts(tenant_id);
CREATE INDEX idx_coa_parent ON chart_of_accounts(parent_id);
CREATE INDEX idx_coa_type ON chart_of_accounts(type);

-- ========== FISCAL PERIODS ==========
CREATE TABLE IF NOT EXISTS fiscal_periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP WITH TIME ZONE,
    closed_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_fiscal_tenant ON fiscal_periods(tenant_id);
CREATE INDEX idx_fiscal_dates ON fiscal_periods(start_date, end_date);

-- ========== JOURNAL ENTRIES ==========
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    entry_number VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    reference_type VARCHAR(50),
    reference_id UUID,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'posted', 'reversed')),
    posted_at TIMESTAMP WITH TIME ZONE,
    posted_by UUID,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, entry_number)
);

CREATE INDEX idx_journal_tenant ON journal_entries(tenant_id);
CREATE INDEX idx_journal_date ON journal_entries(date);
CREATE INDEX idx_journal_status ON journal_entries(status);
CREATE INDEX idx_journal_reference ON journal_entries(reference_type, reference_id);

-- ========== JOURNAL DETAILS (LINES) ==========
CREATE TABLE IF NOT EXISTS journal_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
    description TEXT,
    debit DECIMAL(18, 2) DEFAULT 0,
    credit DECIMAL(18, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_journal_detail_entry ON journal_details(journal_entry_id);
CREATE INDEX idx_journal_detail_account ON journal_details(account_id);

-- ========== FIXED ASSETS ==========
CREATE TABLE IF NOT EXISTS fixed_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    acquisition_date DATE NOT NULL,
    acquisition_cost DECIMAL(18, 2) NOT NULL,
    salvage_value DECIMAL(18, 2) DEFAULT 0,
    useful_life_months INTEGER NOT NULL,
    depreciation_method VARCHAR(50) DEFAULT 'straight_line' CHECK (depreciation_method IN ('straight_line', 'declining_balance', 'units_of_production')),
    accumulated_depreciation DECIMAL(18, 2) DEFAULT 0,
    book_value DECIMAL(18, 2) NOT NULL,
    asset_account_id UUID REFERENCES chart_of_accounts(id),
    depreciation_expense_account_id UUID REFERENCES chart_of_accounts(id),
    accumulated_depreciation_account_id UUID REFERENCES chart_of_accounts(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'disposed', 'fully_depreciated')),
    disposal_date DATE,
    disposal_amount DECIMAL(18, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_asset_tenant ON fixed_assets(tenant_id);
CREATE INDEX idx_asset_status ON fixed_assets(status);

-- ========== ASSET DEPRECIATION LOG ==========
CREATE TABLE IF NOT EXISTS asset_depreciation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES fixed_assets(id) ON DELETE CASCADE,
    depreciation_date DATE NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    accumulated_total DECIMAL(18, 2) NOT NULL,
    book_value_after DECIMAL(18, 2) NOT NULL,
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_depreciation_asset ON asset_depreciation_log(asset_id);
CREATE INDEX idx_depreciation_date ON asset_depreciation_log(depreciation_date);

-- ========== BANK ACCOUNTS ==========
CREATE TABLE IF NOT EXISTS bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    bank_name VARCHAR(255),
    account_number VARCHAR(50),
    account_holder VARCHAR(255),
    account_type VARCHAR(50) DEFAULT 'Checking' CHECK (account_type IN ('Checking', 'Savings', 'Credit', 'Cash', 'Other')),
    currency_code VARCHAR(3) DEFAULT 'IDR',
    opening_balance DECIMAL(18, 2) DEFAULT 0,
    current_balance DECIMAL(18, 2) DEFAULT 0,
    gl_account_id UUID REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_bank_tenant ON bank_accounts(tenant_id);
CREATE INDEX idx_bank_active ON bank_accounts(is_active);

-- ========== BANK TRANSACTIONS ==========
CREATE TABLE IF NOT EXISTS bank_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    transaction_number VARCHAR(50) NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    value_date TIMESTAMP WITH TIME ZONE,
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer In', 'Transfer Out', 'Bank Fee', 'Interest')),
    amount DECIMAL(18, 2) NOT NULL,
    running_balance DECIMAL(18, 2),
    counterparty_name VARCHAR(255),
    counterparty_account VARCHAR(100),
    reference_type VARCHAR(50),
    reference_number VARCHAR(100),
    description TEXT,
    is_reconciled BOOLEAN DEFAULT FALSE,
    reconciliation_id UUID,
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, transaction_number)
);

CREATE INDEX idx_bank_tx_tenant ON bank_transactions(tenant_id);
CREATE INDEX idx_bank_tx_account ON bank_transactions(bank_account_id);
CREATE INDEX idx_bank_tx_date ON bank_transactions(transaction_date);
CREATE INDEX idx_bank_tx_reconciled ON bank_transactions(is_reconciled);

-- ========== BANK RECONCILIATIONS ==========
CREATE TABLE IF NOT EXISTS bank_reconciliations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    statement_date DATE NOT NULL,
    statement_ending_balance DECIMAL(18, 2) NOT NULL,
    book_balance DECIMAL(18, 2),
    difference DECIMAL(18, 2),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed')),
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_by UUID,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_recon_tenant ON bank_reconciliations(tenant_id);
CREATE INDEX idx_recon_account ON bank_reconciliations(bank_account_id);
CREATE INDEX idx_recon_date ON bank_reconciliations(statement_date);

-- ========== PETTY CASH ==========
CREATE TABLE IF NOT EXISTS petty_cash (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    bank_account_id UUID REFERENCES bank_accounts(id),
    transaction_number VARCHAR(50) NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_replenishment BOOLEAN DEFAULT FALSE,
    amount DECIMAL(18, 2) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    requested_by UUID,
    approved_by UUID,
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, transaction_number)
);

CREATE INDEX idx_petty_tenant ON petty_cash(tenant_id);
CREATE INDEX idx_petty_date ON petty_cash(transaction_date);
CREATE INDEX idx_petty_type ON petty_cash(is_replenishment);

-- ========== TRIGGERS FOR UPDATED_AT ==========
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_coa_updated_at BEFORE UPDATE ON chart_of_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fiscal_updated_at BEFORE UPDATE ON fiscal_periods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journal_updated_at BEFORE UPDATE ON journal_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_asset_updated_at BEFORE UPDATE ON fixed_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bank_account_updated_at BEFORE UPDATE ON bank_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bank_tx_updated_at BEFORE UPDATE ON bank_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recon_updated_at BEFORE UPDATE ON bank_reconciliations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_petty_updated_at BEFORE UPDATE ON petty_cash
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========== SEED DEFAULT COA TEMPLATE ==========
-- This will be executed via the /coa/seed endpoint
