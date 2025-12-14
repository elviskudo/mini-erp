import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime
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
    hourly_rate = Column(Float, default=0.0)
    capacity_per_hour = Column(Float, default=0.0)


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(ProductType), default=ProductType.RAW_MATERIAL)
    uom = Column(String, default="pcs")  # Unit of Measure 
    standard_cost = Column(Float, default=0.0)


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
