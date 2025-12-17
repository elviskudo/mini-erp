from pydantic import BaseModel
from typing import List, Optional
import uuid

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
