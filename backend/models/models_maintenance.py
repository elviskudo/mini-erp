from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
import uuid
from database import Base


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    CALIBRATION = "CALIBRATION"
    CORRECTIVE = "CORRECTIVE"


class MaintenanceStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MaintenanceOrder(Base):
    __tablename__ = "maintenance_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("fixed_assets.id"), nullable=False)
    type = Column(Enum(MaintenanceType), nullable=False)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.OPEN)
    
    scheduled_date = Column(DateTime, nullable=False)
    completion_date = Column(DateTime, nullable=True)
    
    description = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    technician = Column(String, nullable=True)  # Could be FK to Employee
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset = relationship("FixedAsset")
