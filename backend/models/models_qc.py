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


class ScrapType(str, enum.Enum):
    TOTAL_LOSS = "Total Loss"  # Complete waste, disposed
    GRADE_B = "Grade B"  # Defective but sellable at lower price
    REWORK = "Rework"  # Can be reprocessed


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


class ProductionQCResult(Base):
    """QC results for production orders - tracks Good/Defect/Scrap quantities"""
    __tablename__ = "production_qc_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Quantity breakdown
    good_qty = Column(Float, default=0.0)  # Passed QC
    defect_qty = Column(Float, default=0.0)  # Has defects
    scrap_qty = Column(Float, default=0.0)  # Total waste
    
    # Scrap handling
    scrap_type = Column(Enum(ScrapType), nullable=True)
    scrap_reason = Column(String, nullable=True)  # "Suhu Oven Tidak Stabil" etc
    
    # Financial impact
    salvage_value = Column(Float, default=0.0)  # Value recovered from Grade B
    spoilage_expense = Column(Float, default=0.0)  # Cost of total loss
    rework_cost = Column(Float, default=0.0)  # Additional cost for rework
    
    # Grade B product (if applicable)
    grade_b_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    notes = Column(String, nullable=True)
    
    product = relationship("Product", foreign_keys=[product_id])
    grade_b_product = relationship("Product", foreign_keys=[grade_b_product_id])
