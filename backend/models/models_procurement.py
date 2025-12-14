import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

class PRStatus(str, enum.Enum):
    DRAFT = "Draft"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CONVERTED = "Converted" # To PO

class POStatus(str, enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    COMPLETED = "Completed" # Goods Received

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(String, nullable=True) # User ID
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(PRStatus), default=PRStatus.DRAFT)
    
    items = relationship("PRLine", back_populates="pr", cascade="all, delete-orphan")

class PRLine(Base):
    __tablename__ = "pr_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requests.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)

    pr = relationship("PurchaseRequest", back_populates="items")
    product = relationship("Product")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(POStatus), default=POStatus.DRAFT)
    pr_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requests.id"), nullable=True) # Link back to PR

    items = relationship("POLine", back_populates="po", cascade="all, delete-orphan")
    vendor = relationship("Vendor")

class POLine(Base):
    __tablename__ = "po_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, default=0.0)

    po = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
