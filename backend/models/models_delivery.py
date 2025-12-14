import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base


class DeliveryStatus(str, enum.Enum):
    DRAFT = "Draft"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"


class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    so_id = Column(String, nullable=True)  # Sales Order ID
    customer_id = Column(UUID(as_uuid=True), nullable=True)  # Link to Customer
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.DRAFT)
    
    items = relationship("DeliveryItem", back_populates="delivery_order", cascade="all, delete-orphan")


class DeliveryItem(Base):
    __tablename__ = "delivery_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    delivery_order_id = Column(UUID(as_uuid=True), ForeignKey("delivery_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=True)

    delivery_order = relationship("DeliveryOrder", back_populates="items")
    product = relationship("Product")
    batch = relationship("InventoryBatch")
