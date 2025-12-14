from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class ReceiveItem(BaseModel):
    product_id: uuid.UUID
    quantity: float
    batch_number: str
    expiration_date: Optional[datetime] = None
    location_id: uuid.UUID

class ReceivePORequest(BaseModel):
    po_id: uuid.UUID
    warehouse_id: uuid.UUID
    items: List[ReceiveItem]

class GRResponse(BaseModel):
    id: uuid.UUID
    po_id: uuid.UUID
    batches_created: int
    class Config:
        from_attributes = True
