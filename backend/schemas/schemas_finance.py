from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class JournalDetailCreate(BaseModel):
    account_id: uuid.UUID
    debit: float = 0
    credit: float = 0

class JournalEntryCreate(BaseModel):
    date: Optional[datetime] = None
    description: str
    reference: Optional[str] = None  # From frontend
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    lines: Optional[List[JournalDetailCreate]] = None  # From frontend
    details: Optional[List[JournalDetailCreate]] = None  # Alternative name
    
    def get_details(self) -> List[JournalDetailCreate]:
        """Returns the journal details, preferring 'lines' if present"""
        return self.lines or self.details or []
    
    def get_reference_id(self) -> Optional[str]:
        """Returns reference_id, falling back to reference"""
        return self.reference_id or self.reference

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
