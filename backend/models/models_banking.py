"""
Bank & Cash Management Models
"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class BankAccountType(str, enum.Enum):
    CHECKING = "Checking"
    SAVINGS = "Savings"
    PETTY_CASH = "Petty Cash"
    DIGITAL_WALLET = "Digital Wallet"


class TransactionType(str, enum.Enum):
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER_IN = "Transfer In"
    TRANSFER_OUT = "Transfer Out"
    PAYMENT = "Payment"
    RECEIPT = "Receipt"
    FEE = "Bank Fee"
    INTEREST = "Interest"
    ADJUSTMENT = "Adjustment"


class BankAccount(Base):
    """Bank accounts and cash registers"""
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String(20), nullable=False, index=True)  # e.g. "BCA-01"
    name = Column(String(100), nullable=False)  # e.g. "BCA Giro Utama"
    
    bank_name = Column(String(100))  # e.g. "Bank Central Asia"
    account_number = Column(String(50))  # e.g. "1234567890"
    account_holder = Column(String(200))  # Account holder name
    
    account_type = Column(Enum(BankAccountType), default=BankAccountType.CHECKING)
    currency_code = Column(String(3), default="IDR")  # ISO currency code
    
    # Opening balance
    opening_balance = Column(Float, default=0.0)
    opening_date = Column(DateTime, nullable=True)
    
    # Current balance (calculated/cached)
    current_balance = Column(Float, default=0.0)
    last_reconciled_date = Column(DateTime, nullable=True)
    last_reconciled_balance = Column(Float, default=0.0)
    
    # Linked GL account
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = relationship("BankTransaction", backref="bank_account")


class BankTransaction(Base):
    """Bank and cash transactions"""
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    transaction_number = Column(String(50), index=True)  # Auto-generated
    transaction_date = Column(DateTime, nullable=False)
    value_date = Column(DateTime)  # Effective date
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    amount = Column(Float, nullable=False)  # Positive for deposits, negative for withdrawals
    running_balance = Column(Float)  # Balance after transaction
    
    # Counterparty
    counterparty_name = Column(String(200))
    counterparty_account = Column(String(50))  # For transfers
    
    # Reference
    reference_type = Column(String(50))  # "vendor_payment", "customer_receipt", etc.
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_number = Column(String(50))
    
    description = Column(Text)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciliation_id = Column(UUID(as_uuid=True), ForeignKey("bank_reconciliations.id"), nullable=True)
    
    # Journal entry
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BankReconciliation(Base):
    """Bank statement reconciliation"""
    __tablename__ = "bank_reconciliations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    statement_date = Column(DateTime, nullable=False)
    statement_ending_balance = Column(Float, nullable=False)
    
    # System calculated
    book_balance = Column(Float, default=0.0)
    outstanding_deposits = Column(Float, default=0.0)
    outstanding_withdrawals = Column(Float, default=0.0)
    adjusted_book_balance = Column(Float, default=0.0)
    
    difference = Column(Float, default=0.0)  # Should be 0 when reconciled
    
    status = Column(String(20), default="draft")  # draft, completed
    
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transactions = relationship("BankTransaction", backref="reconciliation", foreign_keys="BankTransaction.reconciliation_id")


class PettyCash(Base):
    """Petty cash transactions"""
    __tablename__ = "petty_cash"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)  # Links to petty cash "account"
    
    transaction_date = Column(DateTime, nullable=False)
    transaction_number = Column(String(50), index=True)
    
    # Transaction type
    is_replenishment = Column(Boolean, default=False)  # True = refill, False = expense
    
    amount = Column(Float, nullable=False)
    description = Column(Text)
    
    # Expense categorization
    expense_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    cost_center_id = Column(UUID(as_uuid=True), nullable=True)  # Link to cost center
    
    # Receipt/documentation
    receipt_number = Column(String(50))
    receipt_date = Column(DateTime)
    
    # Requestor
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Journal entry
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CashAdvance(Base):
    """Employee cash advances"""
    __tablename__ = "cash_advances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    advance_number = Column(String(50), index=True)
    
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    
    request_date = Column(DateTime, nullable=False)
    purpose = Column(Text)
    
    amount_requested = Column(Float, nullable=False)
    amount_approved = Column(Float, default=0.0)
    amount_settled = Column(Float, default=0.0)  # Amount returned/used
    
    status = Column(String(20), default="pending")  # pending, approved, rejected, disbursed, settled
    
    # Disbursement
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=True)
    disbursed_date = Column(DateTime, nullable=True)
    
    # Settlement
    settlement_date = Column(DateTime, nullable=True)
    settlement_notes = Column(Text, nullable=True)
    
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Journal entries
    disbursement_journal_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    settlement_journal_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = relationship("Employee", foreign_keys=[employee_id])
