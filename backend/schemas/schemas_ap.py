from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class InvoiceItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float
    unit_price: float
    po_item_id: Optional[uuid.UUID] = None

class InvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: uuid.UUID
    po_id: Optional[uuid.UUID] = None
    date: datetime = None  # Will default to now on backend
    due_date: Optional[datetime] = None
    items: List[InvoiceItemCreate] = []  # Allow empty list
    total_amount: Optional[float] = None  # Direct total if no items
    notes: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    status: str
    total_amount: float
    class Config:
        from_attributes = True
