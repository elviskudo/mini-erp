from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime
import enum


class InvoiceStatus(str, enum.Enum):
    DRAFT = "Draft"
    MATCHED = "Matched"
    DISPUTED = "Disputed"
    POSTED = "Posted"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"


class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    CHECK = "Check"
    GIRO = "Giro"


class PurchaseInvoice(Base):
    """Vendor bills / purchase invoices"""
    __tablename__ = "ap_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_number = Column(String, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    
    date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    # Payment terms
    payment_terms = Column(String(50))  # e.g. "NET30", "COD"
    
    # Currency
    currency_code = Column(String(3), default="IDR")
    exchange_rate = Column(Float, default=1.0)
    
    # Amounts
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Payment tracking
    amount_paid = Column(Float, default=0.0)
    amount_due = Column(Float, default=0.0)
    
    status = Column(String, default=InvoiceStatus.DRAFT.value)
    
    # GL posting
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vendor = relationship("Vendor")
    purchase_order = relationship("PurchaseOrder")
    items = relationship("PurchaseInvoiceItem", backref="invoice", cascade="all, delete-orphan")
    payments = relationship("APPayment", backref="invoice")


class PurchaseInvoiceItem(Base):
    __tablename__ = "ap_invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ap_invoices.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    description = Column(Text)
    
    quantity = Column(Float)
    unit_price = Column(Float)
    
    # Tax
    tax_code_id = Column(UUID(as_uuid=True), ForeignKey("tax_codes.id"), nullable=True)
    tax_amount = Column(Float, default=0.0)
    
    total_price = Column(Float)
    
    # Link to PO Item for matching
    po_item_id = Column(UUID(as_uuid=True), ForeignKey("po_lines.id"), nullable=True)
    
    # Expense account
    expense_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    
    # Cost center allocation
    cost_center_id = Column(UUID(as_uuid=True), nullable=True)

    product = relationship("Product")


class APPayment(Base):
    """Payments to vendors"""
    __tablename__ = "ap_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    payment_number = Column(String(50), nullable=False, index=True)
    
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ap_invoices.id"), nullable=True)
    
    payment_date = Column(DateTime, nullable=False)
    
    payment_method = Column(String(50), nullable=False)  # Bank Transfer, Cash, Check, Giro
    
    # Currency
    currency_code = Column(String(3), default="IDR")
    exchange_rate = Column(Float, default=1.0)
    
    amount = Column(Float, nullable=False)
    amount_in_base_currency = Column(Float, nullable=False)
    
    # Bank account
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=True)
    
    # Reference (check number, transfer ref)
    reference_number = Column(String(100))
    
    # Withholding tax
    withholding_tax_id = Column(UUID(as_uuid=True), ForeignKey("withholding_taxes.id"), nullable=True)
    withholding_amount = Column(Float, default=0.0)
    
    notes = Column(Text)
    
    # Journal entry
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    status = Column(String(20), default="completed")  # pending, completed, voided
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vendor = relationship("Vendor")


class DebitNote(Base):
    """Debit notes for purchase returns or adjustments"""
    __tablename__ = "ap_debit_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    debit_note_number = Column(String(50), nullable=False, index=True)
    
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ap_invoices.id"), nullable=True)
    
    date = Column(DateTime, nullable=False)
    
    # Reason
    reason = Column(String(100))  # "Purchase Return", "Price Adjustment", etc.
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
    applied_amount = Column(Float, default=0.0)
    
    # GL posting
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vendor = relationship("Vendor")
    items = relationship("DebitNoteItem", backref="debit_note", cascade="all, delete-orphan")


class DebitNoteItem(Base):
    """Line items for debit notes"""
    __tablename__ = "ap_debit_note_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    debit_note_id = Column(UUID(as_uuid=True), ForeignKey("ap_debit_notes.id"), nullable=False)
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    description = Column(Text, nullable=False)
    
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    tax_code_id = Column(UUID(as_uuid=True), ForeignKey("tax_codes.id"), nullable=True)
    tax_amount = Column(Float, default=0.0)
    
    total = Column(Float, default=0.0)
    
    product = relationship("Product")

