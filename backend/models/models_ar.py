"""
Accounts Receivable (AR) Models
Customer invoicing, payments, and credit management
"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class InvoiceStatus(str, enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"
    BAD_DEBT = "Bad Debt"


class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    CHECK = "Check"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    DIGITAL_WALLET = "Digital Wallet"
    GIRO = "Giro"


class CustomerInvoice(Base):
    """Customer/Sales invoices"""
    __tablename__ = "ar_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    invoice_number = Column(String(50), nullable=False, index=True)
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=False)
    
    # Reference to source document
    reference_type = Column(String(50), nullable=True)  # "sales_order", "pos_sale", etc.
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_number = Column(String(50))
    
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    
    # Payment terms
    payment_terms = Column(String(50))  # e.g. "NET30", "COD"
    payment_terms_days = Column(Float, default=0)  # Auto-calculate due date
    
    # Currency
    currency_code = Column(String(3), default="IDR")
    exchange_rate = Column(Float, default=1.0)
    
    # Amounts
    subtotal = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Payment tracking
    amount_paid = Column(Float, default=0.0)
    amount_due = Column(Float, default=0.0)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    
    # Additional info
    notes = Column(Text)
    internal_notes = Column(Text)
    
    # Billing address (snapshot)
    billing_address = Column(Text)
    
    # GL posting
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer")
    items = relationship("CustomerInvoiceItem", backref="invoice", cascade="all, delete-orphan")
    payments = relationship("CustomerPayment", backref="invoice")


class CustomerInvoiceItem(Base):
    """Line items for customer invoices"""
    __tablename__ = "ar_invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=False)
    
    # Product/service
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    description = Column(Text, nullable=False)
    
    quantity = Column(Float, nullable=False)
    unit = Column(String(20))  # e.g. "pcs", "kg", "hour"
    unit_price = Column(Float, nullable=False)
    
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    
    # Tax
    tax_code_id = Column(UUID(as_uuid=True), ForeignKey("tax_codes.id"), nullable=True)
    tax_amount = Column(Float, default=0.0)
    
    # Line total
    subtotal = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    # Revenue account
    revenue_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    
    # Cost center for revenue allocation
    cost_center_id = Column(UUID(as_uuid=True), nullable=True)
    
    product = relationship("Product")


class CustomerPayment(Base):
    """Customer payment receipts"""
    __tablename__ = "ar_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    payment_number = Column(String(50), nullable=False, index=True)
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=True)  # Can be advance payment
    
    payment_date = Column(DateTime, nullable=False)
    
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Currency
    currency_code = Column(String(3), default="IDR")
    exchange_rate = Column(Float, default=1.0)
    
    amount = Column(Float, nullable=False)
    amount_in_base_currency = Column(Float, nullable=False)  # Converted amount
    
    # Bank/cash account
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=True)
    
    # Reference
    reference_number = Column(String(100))  # Bank transfer ref, check number, etc.
    
    notes = Column(Text)
    
    # Journal entry
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer")


class CreditNote(Base):
    """Credit notes/memos for returns or adjustments"""
    __tablename__ = "ar_credit_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    credit_note_number = Column(String(50), nullable=False, index=True)
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=True)  # Related invoice if any
    
    date = Column(DateTime, nullable=False)
    
    # Reason
    reason = Column(String(100))  # "Sales Return", "Price Adjustment", etc.
    description = Column(Text)
    
    # Currency
    currency_code = Column(String(3), default="IDR")
    exchange_rate = Column(Float, default=1.0)
    
    # Amounts
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default="draft")  # draft, approved, applied
    applied_amount = Column(Float, default=0.0)  # Amount applied to invoices
    
    # GL posting
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer")
    items = relationship("CreditNoteItem", backref="credit_note", cascade="all, delete-orphan")


class CreditNoteItem(Base):
    """Line items for credit notes"""
    __tablename__ = "ar_credit_note_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    credit_note_id = Column(UUID(as_uuid=True), ForeignKey("ar_credit_notes.id"), nullable=False)
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    description = Column(Text, nullable=False)
    
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    tax_code_id = Column(UUID(as_uuid=True), ForeignKey("tax_codes.id"), nullable=True)
    tax_amount = Column(Float, default=0.0)
    
    total = Column(Float, default=0.0)
    
    product = relationship("Product")
