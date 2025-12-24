import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base


class VendorRating(str, enum.Enum):
    A = "A"  # Excellent - On-time delivery, quality products
    B = "B"  # Good - Occasional delays
    C = "C"  # Fair - Needs improvement


class VendorCategory(str, enum.Enum):
    RAW_MATERIAL = "Raw Material"
    FINISHED_GOODS = "Finished Goods"
    BOTH = "Both"


class PRStatus(str, enum.Enum):
    DRAFT = "Draft"
    PENDING_APPROVAL = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CONVERTED = "Converted"  # To PO


class POStatus(str, enum.Enum):
    DRAFT = "Draft"
    PENDING_APPROVAL = "Pending Approval"
    OPEN = "Open"  # Sent to Vendor
    PARTIAL_RECEIVE = "Partial Receive"
    CLOSED = "Closed"  # Fully received
    CANCELLED = "Cancelled"


class PaymentTerm(str, enum.Enum):
    CASH = "Cash"              # Bayar Lunas
    NET_7 = "Net 7"            # 7 hari
    NET_15 = "Net 15"          # 15 hari
    NET_30 = "Net 30"          # 30 hari
    NET_60 = "Net 60"          # 60 hari
    INSTALLMENT_3 = "3 Termin" # 3x bayar
    INSTALLMENT_6 = "6 Termin" # 6x bayar
    INSTALLMENT_12 = "12 Termin" # 12x bayar


class PaymentStatus(str, enum.Enum):
    UNPAID = "Unpaid"
    PARTIAL = "Partial"
    PAID = "Paid"


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    rating = Column(Enum(VendorRating), default=VendorRating.B)
    category = Column(Enum(VendorCategory), default=VendorCategory.RAW_MATERIAL)
    
    # Location - UNCOMMENT AFTER RUNNING MIGRATION:
    # alembic revision --autogenerate -m "Add vendor lat lng"
    # alembic upgrade head
    # latitude = Column(Float, nullable=True)
    # longitude = Column(Float, nullable=True)
    
    # Payment Terms
    payment_term = Column(Enum(PaymentTerm), default=PaymentTerm.NET_30)
    credit_limit = Column(Float, default=0.0)  # Maximum outstanding credit
    
    # Relationships
    supplied_items = relationship("SupplierItem", back_populates="vendor", cascade="all, delete-orphan")


class SupplierItem(Base):
    """Mapping of items that can be purchased from a specific supplier"""
    __tablename__ = "supplier_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    agreed_price = Column(Float, default=0.0)  # Contracted price
    lead_time_days = Column(Integer, default=7)  # Delivery lead time
    min_order_qty = Column(Float, default=1.0)
    is_preferred = Column(Boolean, default=False)  # Preferred supplier for this item
    
    vendor = relationship("Vendor", back_populates="supplied_items")
    product = relationship("Product")
    
    __table_args__ = (
        UniqueConstraint('vendor_id', 'product_id', name='uq_vendor_product'),
    )


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    pr_number = Column(String, index=True, nullable=False)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    required_date = Column(DateTime, nullable=True)
    status = Column(Enum(PRStatus), default=PRStatus.DRAFT)
    notes = Column(String, nullable=True)
    
    # Approval fields
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Rejection fields
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    reject_reason = Column(String, nullable=True)
    
    items = relationship("PRLine", back_populates="pr", cascade="all, delete-orphan")


class PRLine(Base):
    __tablename__ = "pr_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    pr_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requests.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    estimated_price = Column(Float, default=0.0)

    pr = relationship("PurchaseRequest", back_populates="items")
    product = relationship("Product")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    po_number = Column(String, index=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    pr_id = Column(UUID(as_uuid=True), ForeignKey("purchase_requests.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expected_delivery = Column(DateTime, nullable=True)
    status = Column(Enum(POStatus), default=POStatus.DRAFT)
    
    # Budget & Approval
    budget_checked = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Landed Cost components
    subtotal = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    insurance_cost = Column(Float, default=0.0)
    customs_duty = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Payment & Progress
    payment_term = Column(Enum(PaymentTerm), default=PaymentTerm.NET_30)
    due_date = Column(DateTime, nullable=True)
    amount_paid = Column(Float, default=0.0)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    progress = Column(Float, default=0.0)  # 0-100%
    
    # Multi-level approval
    current_approval_level = Column(Integer, default=0)
    required_approval_level = Column(Integer, default=1)
    
    notes = Column(String, nullable=True)

    items = relationship("POLine", back_populates="po", cascade="all, delete-orphan")
    vendor = relationship("Vendor")


class POLine(Base):
    __tablename__ = "po_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    received_qty = Column(Float, default=0.0)  # For partial receiving
    unit_price = Column(Float, default=0.0)
    line_total = Column(Float, default=0.0)

    po = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
