from pydantic import BaseModel, field_validator
from typing import List, Optional, Any
import uuid
from datetime import datetime

class CustomerCreate(BaseModel):
    name: str
    code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: float = 0.0
    payment_term: Optional[str] = None

class CustomerResponse(BaseModel):
    id: uuid.UUID
    name: str
    credit_limit: float
    current_balance: float
    class Config:
        from_attributes = True

class SalesInvoiceItemCreate(BaseModel):
    product_id: Optional[str] = None
    description: Optional[str] = None
    # Accept both frontend names (qty/price) and backend names (quantity/unit_price)
    qty: float = 1
    price: float = 0
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    
    @property
    def actual_quantity(self):
        return self.quantity if self.quantity is not None else self.qty
    
    @property
    def actual_unit_price(self):
        return self.unit_price if self.unit_price is not None else self.price

class SalesInvoiceCreate(BaseModel):
    invoice_number: Optional[str] = None
    customer_id: Any  # Accept string, object, or UUID
    so_id: Optional[str] = None
    # Accept both date and invoice_date
    date: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    payment_terms: Optional[str] = None
    items: List[SalesInvoiceItemCreate] = []
    total_amount: Optional[float] = None
    notes: Optional[str] = None
    
    @field_validator('customer_id', mode='before')
    @classmethod
    def extract_customer_id(cls, v):
        if isinstance(v, dict) and 'value' in v:
            return v['value']
        return v

class SalesInvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    total_amount: float
    status: str
    class Config:
        from_attributes = True


