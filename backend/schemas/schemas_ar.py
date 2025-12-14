from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    credit_limit: float = 0.0

class CustomerResponse(BaseModel):
    id: uuid.UUID
    name: str
    credit_limit: float
    current_balance: float
    class Config:
        from_attributes = True

class SalesInvoiceItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float
    unit_price: float

class SalesInvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: uuid.UUID
    so_id: Optional[str] = None
    date: datetime = datetime.utcnow()
    items: List[SalesInvoiceItemCreate]

class SalesInvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    total_amount: float
    status: str
    class Config:
        from_attributes = True
