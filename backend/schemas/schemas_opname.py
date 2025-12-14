from pydantic import BaseModel
from typing import List, Optional
import uuid

class OpnameCreate(BaseModel):
    warehouse_id: uuid.UUID
    notes: Optional[str] = None

class OpnameDetailUpdate(BaseModel):
    detail_id: uuid.UUID
    counted_qty: float

class OpnamePostRequest(BaseModel):
    opname_id: uuid.UUID

class OpnameResponse(BaseModel):
    id: uuid.UUID
    status: str
    warehouse_id: uuid.UUID
    class Config:
        from_attributes = True
