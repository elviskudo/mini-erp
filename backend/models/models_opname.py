import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

class OpnameStatus(str, enum.Enum):
    DRAFT = "Draft"
    POSTED = "Posted"

class StockOpname(Base):
    __tablename__ = "stock_opnames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OpnameStatus), default=OpnameStatus.DRAFT)
    notes = Column(String, nullable=True)

    details = relationship("StockOpnameDetail", back_populates="opname", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse")

class StockOpnameDetail(Base):
    __tablename__ = "stock_opname_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opname_id = Column(UUID(as_uuid=True), ForeignKey("stock_opnames.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=True)
    
    system_qty = Column(Float, nullable=False)
    counted_qty = Column(Float, nullable=True) # Nullable until counted

    opname = relationship("StockOpname", back_populates="details")
    product = relationship("Product")
    batch = relationship("InventoryBatch")
