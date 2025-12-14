from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class BatchSuggestion(BaseModel):
    batch_id: uuid.UUID
    batch_number: str
    quantity_on_hand: float
    expiration_date: datetime | None
    location_name: str
    class Config:
        from_attributes = True

class IssueRequest(BaseModel):
    product_id: uuid.UUID
    batch_id: uuid.UUID
    location_id: uuid.UUID
    quantity: float
    reference_id: str | None = None # e.g. Work Order ID
    project_id: str | None = None
