from pydantic import BaseModel
from typing import List
import uuid

class PRItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float

class PRCreate(BaseModel):
    items: List[PRItemCreate]

class VendorCreate(BaseModel):
    code: str
    name: str
    email: str

class POCreateFromPR(BaseModel):
    pr_id: uuid.UUID
    vendor_id: uuid.UUID
    price_map: dict = {} # product_id (str) -> unit_price

class PRResponse(BaseModel):
    id: uuid.UUID
    status: str
    class Config:
        from_attributes = True

class POResponse(BaseModel):
    id: uuid.UUID
    status: str
    vendor_id: uuid.UUID
    class Config:
        from_attributes = True

# Aliases for router compatibility
PurchaseOrderResponse = POResponse

class PurchaseOrderCreate(BaseModel):
    vendor_id: uuid.UUID
    order_date: str = None
    expected_date: str = None
    items: List[PRItemCreate] = []
