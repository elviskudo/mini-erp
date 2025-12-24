import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from database import Base


class ProductType(str, enum.Enum):
    RAW_MATERIAL = "Raw Material"
    WIP = "WIP"
    FINISHED_GOODS = "Finished Goods"


class WorkCenter(Base):
    __tablename__ = "work_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    cost_per_hour = Column(Float, default=0.0)
    capacity_hours = Column(Float, default=8.0)
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)  # Product description
    type = Column(Enum(ProductType), default=ProductType.RAW_MATERIAL)
    uom = Column(String, default="pcs")  # Unit of Measure
    
    # Product origin
    is_manufactured = Column(Boolean, default=True)  # False = purchased externally
    image_url = Column(Text, nullable=True)  # Base64 or URL for product image
    
    # Cost & Pricing
    standard_cost = Column(Float, default=0.0)
    weighted_avg_cost = Column(Float, default=0.0)  # Updated on each receipt
    desired_margin = Column(Float, default=0.30)  # 30% default margin
    suggested_selling_price = Column(Float, default=0.0)  # HPP / (1 - margin)
    
    # Cold chain requirements
    requires_cold_chain = Column(Boolean, default=False)
    max_storage_temp = Column(Float, nullable=True)  # Max allowed temperature


class BillOfMaterial(Base):
    __tablename__ = "bill_of_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    version = Column(String, default="1.0")
    is_active = Column(Boolean, default=True)

    product = relationship("Product", backref="boms")
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")


class BOMItem(Base):
    __tablename__ = "bom_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    bom_id = Column(UUID(as_uuid=True), ForeignKey("bill_of_materials.id"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    waste_percentage = Column(Float, default=0.0)

    bom = relationship("BillOfMaterial", back_populates="items")
    component = relationship("Product", foreign_keys=[component_id])


class ProductionOrderStatus(str, enum.Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    order_no = Column(String, nullable=False, index=True)
    status = Column(Enum(ProductionOrderStatus), default=ProductionOrderStatus.DRAFT)
    
    # Quantity tracking
    target_qty = Column(Float, nullable=False, default=0.0)  # Daily target
    quantity = Column(Float, nullable=False)  # Planned quantity
    completed_qty = Column(Float, default=0.0)  # Actual completed
    progress = Column(Integer, default=0)  # Percentage 0-100
    
    # Scheduling
    scheduled_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Labor tracking
    labor_hours = Column(Float, default=0.0)
    hourly_rate = Column(Float, default=0.0)
    
    # Cost breakdown (HPP)
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    total_hpp = Column(Float, default=0.0)  # Total cost of goods manufactured
    hpp_per_unit = Column(Float, default=0.0)
    
    notes = Column(String, nullable=True)
    
    # Relationships
    products = relationship("ProductionOrderProduct", back_populates="production_order", cascade="all, delete-orphan")
    work_centers = relationship("ProductionOrderWorkCenter", back_populates="production_order", cascade="all, delete-orphan")



class ProductionOrderProduct(Base):
    __tablename__ = "production_order_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    production_order = relationship("ProductionOrder", back_populates="products")
    product = relationship("Product")


class ProductionOrderWorkCenter(Base):
    __tablename__ = "production_order_work_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    work_center_id = Column(UUID(as_uuid=True), ForeignKey("work_centers.id"), nullable=False)
    
    production_order = relationship("ProductionOrder", back_populates="work_centers")
    work_center = relationship("WorkCenter")
