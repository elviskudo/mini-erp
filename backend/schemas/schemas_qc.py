from pydantic import BaseModel
from typing import List
import uuid

class InspectionResultInput(BaseModel):
    parameter: str
    value: float

class InspectionCreate(BaseModel):
    product_id: uuid.UUID
    batch_number: str
    inspector_id: str
    results: List[InspectionResultInput]

class InspectionResponse(BaseModel):
    id: uuid.UUID
    batch_number: str
    verdict: str
    class Config:
        from_attributes = True
