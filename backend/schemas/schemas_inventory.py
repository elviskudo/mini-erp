from pydantic import BaseModel
from typing import List, Optional
import uuid
from enum import Enum

class ZoneType(str, Enum):
    AMBIENT = "Ambient"
    CHILLER = "Chiller"
    FROZEN = "Frozen"
    DANGEROUS = "Dangerous"


# ===== Room Schemas =====
class RoomBase(BaseModel):
    room_code: str
    room_name: str
    capacity: int = 0
    area_sqm: float = 0

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    room_code: Optional[str] = None
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    area_sqm: Optional[float] = None

class RoomResponse(RoomBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    floor_id: uuid.UUID
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Floor Schemas =====
class FloorBase(BaseModel):
    floor_number: int
    floor_name: str
    area_sqm: float = 0

class FloorCreate(FloorBase):
    pass

class FloorUpdate(BaseModel):
    floor_number: Optional[int] = None
    floor_name: Optional[str] = None
    area_sqm: Optional[float] = None

class FloorResponse(FloorBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    warehouse_id: uuid.UUID
    rooms: List[RoomResponse] = []
    class Config:
        from_attributes = True


# ===== Location Schemas =====
class LocationBase(BaseModel):
    code: str
    name: str
    type: str

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: uuid.UUID
    class Config:
        from_attributes = True


# ===== Warehouse Schemas =====
class WarehouseBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_floors: int = 1

class FloorCreateInline(BaseModel):
    """For creating floors inline with warehouse"""
    floor_number: int
    floor_name: str
    area_sqm: float = 0

class WarehouseCreate(WarehouseBase):
    floors: Optional[List[FloorCreateInline]] = None

class WarehouseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_floors: Optional[int] = None

class WarehouseResponse(WarehouseBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    locations: List[LocationResponse] = []
    floors: List[FloorResponse] = []
    class Config:
        from_attributes = True


# ===== Storage Zone Schemas =====
class StorageZoneBase(BaseModel):
    warehouse_id: uuid.UUID
    zone_name: str
    zone_type: ZoneType = ZoneType.AMBIENT
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    capacity_units: int = 0
    electricity_tariff: float = 0.0
    sensor_id: Optional[str] = None
    electricity_meter_id: Optional[str] = None


class StorageZoneCreate(StorageZoneBase):
    pass


class StorageZoneUpdate(BaseModel):
    zone_name: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    capacity_units: Optional[int] = None
    daily_kwh_usage: Optional[float] = None
    electricity_tariff: Optional[float] = None
    monthly_energy_cost: Optional[float] = None
    sensor_id: Optional[str] = None
    electricity_meter_id: Optional[str] = None


class StorageZoneResponse(StorageZoneBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    daily_kwh_usage: float = 0.0
    monthly_energy_cost: float = 0.0
    current_temp: Optional[float] = None
    used_units: int = 0
    class Config:
        from_attributes = True
