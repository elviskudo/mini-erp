from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class CartItem(BaseModel):
    product_id: uuid.UUID
    quantity: int

class CheckoutRequest(BaseModel):
    customer_id: uuid.UUID # In real app, this comes from auth token
    items: List[CartItem]

class ProductCatalogItem(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    available_stock: float

    class Config:
        from_attributes = True
