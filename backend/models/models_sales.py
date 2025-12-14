from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime
import enum


class SalesInvoiceStatus(str, enum.Enum):
    DRAFT = "Draft"
    POSTED = "Posted"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class Customer(Base):
    __tablename__ = "sales_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    credit_limit = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)  # Denormalized for performance


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_number = Column(String, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"))
    date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, default=0.0)
    status = Column(String, default=SalesInvoiceStatus.DRAFT)
    
    # Optional link to Delivery Order or Sales Order
    so_id = Column(String, nullable=True) 

    customer = relationship("Customer")
    items = relationship("SalesInvoiceItem", backref="invoice", cascade="all, delete-orphan")


class SalesInvoiceItem(Base):
    __tablename__ = "sales_invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)

    product = relationship("Product")
