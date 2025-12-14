from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.models_maintenance import MaintenanceType, MaintenanceStatus

class MaintenanceOrderBase(BaseModel):
    asset_id: str
    type: MaintenanceType
    scheduled_date: datetime
    description: Optional[str] = None
    technician: Optional[str] = None

class MaintenanceOrderCreate(MaintenanceOrderBase):
    pass

class MaintenanceOrderResponse(MaintenanceOrderBase):
    id: str
    status: MaintenanceStatus
    completion_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CompleteOrderRequest(BaseModel):
    notes: Optional[str] = None
    next_calibration_date: Optional[datetime] = None # If calibration type
