from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

# ============ Schedule Schemas ============

class ScheduleCreate(BaseModel):
    warehouse_id: uuid.UUID
    name: str
    description: Optional[str] = None
    frequency: str = "Monthly"  # Daily, Weekly, Monthly, Quarterly, Yearly, Ad-hoc
    scheduled_date: datetime
    start_time: Optional[str] = None
    estimated_duration_hours: int = 4
    count_all_items: bool = True
    category_filter: Optional[str] = None
    location_filter: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    name: str
    description: Optional[str] = None
    frequency: str
    scheduled_date: datetime
    start_time: Optional[str] = None
    estimated_duration_hours: int
    is_active: bool
    warehouse: Optional["WarehouseBrief"] = None
    assignments: Optional[List["AssignmentBrief"]] = None
    
    class Config:
        from_attributes = True

class AssignmentCreate(BaseModel):
    schedule_id: uuid.UUID
    user_id: uuid.UUID
    role: str = "Counter"  # Counter, Supervisor, Approver
    assigned_locations: Optional[str] = None

class AssignmentBrief(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    user: Optional["UserBrief"] = None
    
    class Config:
        from_attributes = True

# ============ Opname Schemas ============

class OpnameCreate(BaseModel):
    warehouse_id: uuid.UUID
    schedule_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class OpnameStartCounting(BaseModel):
    opname_id: uuid.UUID

class OpnameDetailUpdate(BaseModel):
    detail_id: uuid.UUID
    counted_qty: float
    variance_reason: Optional[str] = None
    variance_notes: Optional[str] = None

class OpnameBulkCount(BaseModel):
    opname_id: uuid.UUID
    items: List[OpnameDetailUpdate]

class OpnameReview(BaseModel):
    opname_id: uuid.UUID
    notes: Optional[str] = None

class OpnameApproval(BaseModel):
    opname_id: uuid.UUID
    approved: bool
    rejection_reason: Optional[str] = None

class OpnamePostRequest(BaseModel):
    opname_id: uuid.UUID

# ============ Nested Schemas ============

class ProductBrief(BaseModel):
    id: uuid.UUID
    name: str
    code: Optional[str] = None
    
    class Config:
        from_attributes = True

class WarehouseBrief(BaseModel):
    id: uuid.UUID
    name: str
    
    class Config:
        from_attributes = True

class LocationBrief(BaseModel):
    id: uuid.UUID
    name: str
    code: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserBrief(BaseModel):
    id: uuid.UUID
    username: str
    
    class Config:
        from_attributes = True

class OpnameDetailResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    system_qty: float
    counted_qty: Optional[float] = None
    variance: float = 0
    variance_reason: Optional[str] = None
    variance_notes: Optional[str] = None
    unit_cost: float = 0
    variance_value: float = 0
    needs_recount: bool = False
    product: Optional[ProductBrief] = None
    location: Optional[LocationBrief] = None
    
    class Config:
        from_attributes = True

class OpnameResponse(BaseModel):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    schedule_id: Optional[uuid.UUID] = None
    opname_number: Optional[str] = None
    date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    total_items: int = 0
    counted_items: int = 0
    items_with_variance: int = 0
    total_system_value: float = 0
    total_counted_value: float = 0
    total_variance_value: float = 0
    warehouse: Optional[WarehouseBrief] = None
    details: Optional[List[OpnameDetailResponse]] = None
    
    class Config:
        from_attributes = True

# ============ Report Schemas ============

class VarianceItem(BaseModel):
    product_name: str
    product_code: Optional[str] = None
    location: Optional[str] = None
    system_qty: float
    counted_qty: float
    variance: float
    variance_reason: Optional[str] = None
    variance_value: float

class VarianceReport(BaseModel):
    opname_id: uuid.UUID
    opname_number: Optional[str] = None
    warehouse_name: str
    date: datetime
    status: str
    total_items: int
    items_with_variance: int
    total_variance_value: float
    variance_items: List[VarianceItem]
    
    class Config:
        from_attributes = True

class EvaluationStats(BaseModel):
    total_opnames: int
    completed_opnames: int
    total_variance_value: float
    avg_variance_per_opname: float
    common_variance_reasons: List[dict]
    monthly_trend: List[dict]

# ============ Print Sheet Schema ============

class CountSheetItem(BaseModel):
    product_code: str
    product_name: str
    location: Optional[str] = None
    system_qty: float
    uom: Optional[str] = None
    barcode: Optional[str] = None

class CountSheet(BaseModel):
    warehouse_name: str
    date: str
    items: List[CountSheetItem]
