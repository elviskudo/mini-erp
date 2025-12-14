from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base
from datetime import datetime


class SOStatus:
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    SHIPPED = "Shipped"
    CANCELLED = "Cancelled"


class OrderSource:
    MANUAL = "Manual"
    WEB = "Web"
    API = "API"


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"))
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default=SOStatus.DRAFT)
    source = Column(String, default=OrderSource.MANUAL)
    total_amount = Column(Float, default=0.0)
    
    # Relationships
    customer = relationship("Customer")
    items = relationship("SOItem", back_populates="order", cascade="all, delete-orphan")


class SOItem(Base):
    __tablename__ = "so_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product")
