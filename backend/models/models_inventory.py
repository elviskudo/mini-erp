import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, UniqueConstraint
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


class ZoneType(str, enum.Enum):
    AMBIENT = "Ambient"  # 25-30°C
    CHILLER = "Chiller"  # 2-8°C
    FROZEN = "Frozen"   # -18 to -25°C
    DANGEROUS = "Dangerous"  # Hazardous materials


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_floors = Column(Integer, default=1)

    locations = relationship("Location", back_populates="warehouse", cascade="all, delete-orphan")
    zones = relationship("StorageZone", back_populates="warehouse", cascade="all, delete-orphan")
    floors = relationship("Floor", back_populates="warehouse", cascade="all, delete-orphan", order_by="Floor.floor_number")
    
    # Unique address per tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'address', name='uq_tenant_warehouse_address'),
    )


class Floor(Base):
    """Floor within a warehouse"""
    __tablename__ = "floors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    floor_number = Column(Integer, nullable=False)
    floor_name = Column(String, nullable=False)
    area_sqm = Column(Float, default=0)

    warehouse = relationship("Warehouse", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan", order_by="Room.room_code")


class Room(Base):
    """Room/Storage area within a floor"""
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    floor_id = Column(UUID(as_uuid=True), ForeignKey("floors.id"), nullable=False)
    room_code = Column(String, nullable=False)
    room_name = Column(String, nullable=False)
    capacity = Column(Integer, default=0)
    area_sqm = Column(Float, default=0)
    barcode = Column(String, nullable=True)
    qr_code = Column(String, nullable=True)

    floor = relationship("Floor", back_populates="rooms")


class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("storage_zones.id"), nullable=True)
    code = Column(String, nullable=False)  # e.g., "A-01-01"
    name = Column(String, nullable=False)
    type = Column(Enum(LocationType), default=LocationType.STORAGE)

    warehouse = relationship("Warehouse", back_populates="locations")
    zone = relationship("StorageZone", back_populates="locations")


class StorageZone(Base):
    """Storage zones with temperature control and energy monitoring"""
    __tablename__ = "storage_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    zone_name = Column(String, nullable=False)
    zone_type = Column(Enum(ZoneType), default=ZoneType.AMBIENT)
    
    # Temperature settings
    min_temp = Column(Float, nullable=True)  # Minimum allowed temperature
    max_temp = Column(Float, nullable=True)  # Maximum allowed temperature
    current_temp = Column(Float, nullable=True)  # Current reading from sensor
    
    # Capacity
    capacity_units = Column(Integer, default=0)  # Max storage units
    used_units = Column(Integer, default=0)
    
    # Energy monitoring
    daily_kwh_usage = Column(Float, default=0.0)
    electricity_tariff = Column(Float, default=0.0)  # Cost per kWh
    monthly_energy_cost = Column(Float, default=0.0)
    
    # IoT integration (optional)
    sensor_id = Column(String, nullable=True)
    electricity_meter_id = Column(String, nullable=True)
    
    warehouse = relationship("Warehouse", back_populates="zones")
    locations = relationship("Location", back_populates="zone")
