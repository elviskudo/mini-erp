from pydantic import BaseModel
from typing import List
import uuid

class MRPRunRequest(BaseModel):
    product_id: uuid.UUID
    quantity: float

class MaterialRequirementResponse(BaseModel):
    product_id: uuid.UUID
    required_qty: float
    action_type: str
    source: str
    class Config:
        from_attributes = True

class MRPRunResponse(BaseModel):
    id: uuid.UUID
    status: str
    requirements: List[MaterialRequirementResponse]
    class Config:
        from_attributes = True
