import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base


class MovementType(str, enum.Enum):
    INBOUND = "Inbound"
    OUTBOUND = "Outbound"
    TRANSFER = "Transfer"
    ADJUSTMENT = "Adjustment"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    
    quantity_change = Column(Float, nullable=False)  # Positive for IN, Negative for OUT
    movement_type = Column(Enum(MovementType), nullable=False)
    
    reference_id = Column(String, nullable=True)  # e.g. PO Number, SO Number
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    notes = Column(String, nullable=True)

    product = relationship("Product")
    batch = relationship("InventoryBatch")
    location = relationship("Location")
    user = relationship("User", foreign_keys=[created_by])

