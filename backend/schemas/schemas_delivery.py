from pydantic import BaseModel
from typing import List, Optional
import uuid

class DeliveryItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float
    batch_id: uuid.UUID

class DeliveryOrderCreate(BaseModel):
    so_id: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None
    items: List[DeliveryItemCreate]

class DeliveryOrderResponse(BaseModel):
    id: uuid.UUID
    status: str
    so_id: Optional[str]
    class Config:
        from_attributes = True
