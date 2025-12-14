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
    code = Column(String, unique=True, index=True)
    name = Column(String)
    type = Column(String) # AccountType e.g. "Asset"
    parent_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    parent = relationship("ChartOfAccount", remote_side=[id], backref="children")

class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True) # e.g. "2025-01" or "Jan 2025"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_closed = Column(Boolean, default=False)

class JournalEntry(Base):
    __tablename__ = "gl_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String)
    reference_id = Column(String, nullable=True) # e.g. PO-1001
    reference_type = Column(String, nullable=True) # e.g. "Purchase Order"
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    details = relationship("JournalDetail", backref="entry", cascade="all, delete-orphan")

class JournalDetail(Base):
    __tablename__ = "gl_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    debit = Column(Float, default=0.0)
    
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
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True)
    
    purchase_date = Column(DateTime, nullable=False)
    cost = Column(Float, nullable=False)
    salvage_value = Column(Float, default=0.0)
    useful_life_years = Column(Integer, nullable=False)
    
    status = Column(String, default="Active") # Active, Retired, Disposed
    
    # Calibration & Maintenance Extension
    calibration_status = Column(Enum(CalibrationStatus), default=CalibrationStatus.N_A)
    last_calibration_date = Column(DateTime, nullable=True)
    next_calibration_date = Column(DateTime, nullable=True)
    maintenance_schedule = Column(String, nullable=True) # e.g. "Every 30 days"
    
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
    asset_id = Column(UUID(as_uuid=True), ForeignKey("fixed_assets.id"))
    date = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"))
    
    asset = relationship("FixedAsset", backref="depreciation_entries")
