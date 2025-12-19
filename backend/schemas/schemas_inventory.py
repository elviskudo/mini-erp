from pydantic import BaseModel
from typing import List, Optional
import uuid
from enum import Enum

class ZoneType(str, Enum):
    AMBIENT = "Ambient"
    CHILLER = "Chiller"
    FROZEN = "Frozen"
    DANGEROUS = "Dangerous"


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

class WarehouseBase(BaseModel):
    code: str
    name: str
    address: str

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseResponse(WarehouseBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    locations: List[LocationResponse] = []
    class Config:
        from_attributes = True


# Storage Zone Schemas
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
