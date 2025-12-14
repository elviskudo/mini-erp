from pydantic import BaseModel
from typing import Optional

class SubscriptionCreate(BaseModel):
    tier: str  # MAKER, GROWTH, ENTERPRISE
    payment_method_id: str

class SubscriptionResponse(BaseModel):
    url: str # Stripe Checkout URL
