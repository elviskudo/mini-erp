import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class OriginType(str, enum.Enum):
    MANUFACTURED = "Manufactured"  # Produced in-house
    PURCHASED = "Purchased"  # Externally purchased


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    grn_number = Column(String, index=True, nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    receive_date = Column(DateTime, default=datetime.utcnow)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Landed cost allocation
    allocated_shipping = Column(Float, default=0.0)
    allocated_insurance = Column(Float, default=0.0)
    allocated_customs = Column(Float, default=0.0)
    total_landed_cost = Column(Float, default=0.0)
    
    # Cold chain check
    received_temp = Column(Float, nullable=True)  # Temperature at receiving
    temp_check_passed = Column(Boolean, default=True)
    temp_rejection_reason = Column(String, nullable=True)
    
    notes = Column(String, nullable=True)
    
    items = relationship("GoodsReceiptLine", back_populates="grn", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    grn_id = Column(UUID(as_uuid=True), ForeignKey("goods_receipts.id"), nullable=False)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("po_lines.id"), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity_received = Column(Float, nullable=False)
    unit_cost = Column(Float, default=0.0)  # Original PO price
    landed_unit_cost = Column(Float, default=0.0)  # After allocation
    
    grn = relationship("GoodsReceipt", back_populates="items")
    product = relationship("Product")


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_number = Column(String, nullable=False, index=True)
    quantity_on_hand = Column(Float, default=0.0)
    expiration_date = Column(DateTime, nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    
    # Origin tracking for traceability
    origin_type = Column(Enum(OriginType), default=OriginType.PURCHASED)
    unit_cost = Column(Float, default=0.0)  # Landed cost per unit
    
    # Traceability links
    goods_receipt_id = Column(UUID(as_uuid=True), ForeignKey("goods_receipts.id"), nullable=True)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)  # For purchased items
    
    # QR Code data
    qr_code_data = Column(String, nullable=True)

    product = relationship("Product")
    location = relationship("Location")
    goods_receipt = relationship("GoodsReceipt")
