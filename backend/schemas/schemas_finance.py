from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class JournalDetailCreate(BaseModel):
    account_id: uuid.UUID
    debit: float
    credit: float

class JournalEntryCreate(BaseModel):
    date: datetime = datetime.utcnow()
    description: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    details: List[JournalDetailCreate]

class JournalDetailResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    debit: float
    credit: float
    class Config:
        from_attributes = True

class JournalEntryResponse(BaseModel):
    id: uuid.UUID
    date: datetime
    description: str
    reference_id: Optional[str]
    details: List[JournalDetailResponse]
    class Config:
        from_attributes = True

class AssetCreate(BaseModel):
    name: str
    purchase_date: datetime
    cost: float
    salvage_value: float = 0.0
    useful_life_years: int
    asset_account_id: uuid.UUID
    depr_expense_account_id: uuid.UUID
    acc_depr_account_id: uuid.UUID

class AssetResponse(BaseModel):
    id: uuid.UUID
    name: str
    cost: float
    status: str
    class Config:
        from_attributes = True
