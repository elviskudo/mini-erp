import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from database import Base


class LocationType(str, enum.Enum):
    RECEIVING = "Receiving"
    STORAGE = "Storage"
    PRODUCTION = "Production"
    DISPATCH = "Dispatch"
    QUARANTINE = "Quarantine"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)

    locations = relationship("Location", back_populates="warehouse", cascade="all, delete-orphan")


class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    code = Column(String, nullable=False)  # e.g., "A-01-01"
    name = Column(String, nullable=False)
    type = Column(Enum(LocationType), default=LocationType.STORAGE)

    warehouse = relationship("Warehouse", back_populates="locations")
