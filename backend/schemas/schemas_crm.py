from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class SOItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float
    unit_price: float

class SOCreate(BaseModel):
    customer_id: uuid.UUID
    items: List[SOItemCreate]

class SOItemResponse(BaseModel):
    product_id: uuid.UUID
    quantity: float
    unit_price: float
    subtotal: float
    class Config:
        from_attributes = True

class SOResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    date: datetime
    status: str
    total_amount: float
    items: List[SOItemResponse] = []
    class Config:
        from_attributes = True
