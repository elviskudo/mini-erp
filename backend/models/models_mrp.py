import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

class MRPActionType(str, enum.Enum):
    MAKE = "Make" # Produce internally
    BUY = "Buy"   # Purchase from vendor

class MRPRun(Base):
    __tablename__ = "mrp_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending") # Pending, Completed, Failed
    notes = Column(String, nullable=True)

    requirements = relationship("MaterialRequirement", back_populates="mrp_run", cascade="all, delete-orphan")

class MaterialRequirement(Base):
    __tablename__ = "material_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mrp_run_id = Column(UUID(as_uuid=True), ForeignKey("mrp_runs.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    required_qty = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=True)
    action_type = Column(Enum(MRPActionType), default=MRPActionType.MAKE)
    source = Column(String, default="MRP Calculation") 

    mrp_run = relationship("MRPRun", back_populates="requirements")
    product = relationship("Product")
