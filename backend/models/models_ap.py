from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Enum
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
    PAID = "Paid"

class PurchaseInvoice(Base):
    __tablename__ = "ap_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String, unique=True, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, default=0.0)
    status = Column(String, default=InvoiceStatus.DRAFT)
    
    vendor = relationship("Vendor")
    purchase_order = relationship("PurchaseOrder")
    items = relationship("PurchaseInvoiceItem", backref="invoice", cascade="all, delete-orphan")

class PurchaseInvoiceItem(Base):
    __tablename__ = "ap_invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ap_invoices.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)
    
    # Link to PO Item for matching
    po_item_id = Column(UUID(as_uuid=True), ForeignKey("po_lines.id"), nullable=True)

    product = relationship("Product")
