import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base


class InspectionStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"


class Verdict(str, enum.Enum):
    PASS = "Pass"
    FAIL = "Fail"
    PENDING = "Pending"


class InspectionOrder(Base):
    __tablename__ = "inspection_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_number = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(InspectionStatus), default=InspectionStatus.PENDING)
    verdict = Column(Enum(Verdict), default=Verdict.PENDING)
    inspector_id = Column(String, nullable=True)  # User ID

    results = relationship("InspectionResult", back_populates="inspection_order", cascade="all, delete-orphan")
    product = relationship("Product")


class InspectionResult(Base):
    __tablename__ = "inspection_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    inspection_order_id = Column(UUID(as_uuid=True), ForeignKey("inspection_orders.id"), nullable=False)
    parameter_name = Column(String, nullable=False)  # e.g. "pH", "Viscosity"
    value_measured = Column(Float, nullable=False)
    spec_min = Column(Float, nullable=True)
    spec_max = Column(Float, nullable=True)
    passed = Column(Boolean, default=False)

    inspection_order = relationship("InspectionOrder", back_populates="results")
