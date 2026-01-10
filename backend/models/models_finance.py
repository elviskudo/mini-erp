from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
import enum
from datetime import datetime


class AccountType(str, enum.Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"


class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True)
    name = Column(String)
    type = Column(String)  # AccountType e.g. "Asset"
    parent_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    parent = relationship("ChartOfAccount", remote_side=[id], backref="children")


class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String)  # e.g. "2025-01" or "Jan 2025"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_closed = Column(Boolean, default=False)


class JournalEntry(Base):
    __tablename__ = "gl_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String)
    reference_id = Column(String, nullable=True)  # e.g. PO-1001
    reference_type = Column(String, nullable=True)  # e.g. "Purchase Order"
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    details = relationship("JournalDetail", backref="entry", cascade="all, delete-orphan")


class JournalDetail(Base):
    __tablename__ = "gl_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    
    account = relationship("ChartOfAccount")


class AssetStatus(str, enum.Enum):
    ACTIVE = "Active"
    SOLD = "Sold"
    SCRAPPED = "Scrapped"
    FULLY_DEPRECIATED = "Fully Depreciated"


class CalibrationStatus(str, enum.Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    N_A = "N_A"


class FixedAsset(Base):
    __tablename__ = "fixed_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    code = Column(String, index=True)
    
    purchase_date = Column(DateTime, nullable=False)
    cost = Column(Float, nullable=False)
    salvage_value = Column(Float, default=0.0)
    useful_life_years = Column(Integer, nullable=False)
    
    status = Column(String, default="Active")  # Active, Retired, Disposed
    
    # Calibration & Maintenance Extension
    calibration_status = Column(Enum(CalibrationStatus), default=CalibrationStatus.N_A)
    last_calibration_date = Column(DateTime, nullable=True)
    next_calibration_date = Column(DateTime, nullable=True)
    maintenance_schedule = Column(String, nullable=True)  # e.g. "Every 30 days"
    
    accumulated_depreciation = Column(Float, default=0.0)
    # Linked Asset Account (e.g. Machinery)
    asset_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    # Linked Depr Expense Account
    depr_expense_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    # Linked Acc Depr Account
    acc_depr_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)


class DepreciationEntry(Base):
    __tablename__ = "depreciation_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("fixed_assets.id"))
    date = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"))
    
    asset = relationship("FixedAsset", backref="depreciation_entries")


# ==================== Currency Management ====================

class Currency(Base):
    """Currency definitions for multi-currency support"""
    __tablename__ = "currencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String(3), nullable=False, index=True)  # ISO 4217: IDR, USD, EUR
    name = Column(String(50), nullable=False)  # "Indonesian Rupiah", "US Dollar"
    symbol = Column(String(10))  # "Rp", "$", "€"
    
    decimal_places = Column(Integer, default=2)
    is_base_currency = Column(Boolean, default=False)  # Only one per tenant
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ExchangeRate(Base):
    """Exchange rates for currency conversion"""
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    from_currency = Column(String(3), nullable=False)  # e.g. "USD"
    to_currency = Column(String(3), nullable=False)    # e.g. "IDR"
    
    rate = Column(Float, nullable=False)  # e.g. 15500 (1 USD = 15500 IDR)
    
    effective_date = Column(DateTime, nullable=False)
    source = Column(String(50))  # "Manual", "Bank Indonesia", "API"
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Budgeting ====================

class BudgetStatus(str, enum.Enum):
    DRAFT = "Draft"
    APPROVED = "Approved"
    ACTIVE = "Active"
    CLOSED = "Closed"


class Budget(Base):
    """Budget header - can be annual, quarterly, or monthly"""
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String(20), nullable=False, index=True)  # e.g. "BUD-2026"
    name = Column(String(100), nullable=False)  # e.g. "Annual Budget 2026"
    
    fiscal_year = Column(Integer)  # e.g. 2026
    period_type = Column(String(20))  # "Annual", "Quarterly", "Monthly"
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    status = Column(Enum(BudgetStatus), default=BudgetStatus.DRAFT)
    
    # Totals
    total_revenue = Column(Float, default=0.0)
    total_expense = Column(Float, default=0.0)
    net_budget = Column(Float, default=0.0)
    
    notes = Column(String)
    
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lines = relationship("BudgetLine", backref="budget", cascade="all, delete-orphan")


class BudgetLine(Base):
    """Budget line items - one per account per period"""
    __tablename__ = "budget_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    
    # Optional department/cost center allocation
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    
    # Monthly breakdown (for annual budgets)
    period = Column(String(10))  # e.g. "2026-01" for monthly detail
    
    budgeted_amount = Column(Float, default=0.0)
    actual_amount = Column(Float, default=0.0)  # Updated from GL
    variance = Column(Float, default=0.0)  # budgeted - actual
    variance_percent = Column(Float, default=0.0)
    
    notes = Column(String)
    
    account = relationship("ChartOfAccount")


# ==================== Cost & Profit Centers ====================

class CostCenter(Base):
    """Cost centers for expense allocation"""
    __tablename__ = "cost_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String(20), nullable=False, index=True)  # e.g. "CC-PROD"
    name = Column(String(100), nullable=False)  # e.g. "Production Department"
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    
    # Manager
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("CostCenter", remote_side=[id], backref="children")


class ProfitCenter(Base):
    """Profit centers for revenue and margin tracking"""
    __tablename__ = "profit_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String(20), nullable=False, index=True)  # e.g. "PC-RETAIL"
    name = Column(String(100), nullable=False)  # e.g. "Retail Sales Division"
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("profit_centers.id"), nullable=True)
    
    # Manager
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("ProfitCenter", remote_side=[id], backref="children")

