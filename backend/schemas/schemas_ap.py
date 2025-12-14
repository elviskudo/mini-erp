from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class InvoiceItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float
    unit_price: float
    po_item_id: Optional[uuid.UUID]

class InvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: uuid.UUID
    po_id: Optional[uuid.UUID]
    date: datetime = datetime.utcnow()
    due_date: Optional[datetime]
    items: List[InvoiceItemCreate]

class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    status: str
    total_amount: float
    class Config:
        from_attributes = True
