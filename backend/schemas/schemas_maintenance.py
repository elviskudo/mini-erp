"""
Maintenance Module Schemas
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ==================== ASSET SCHEMAS ====================

class AssetBase(BaseModel):
    code: str
    name: str
    category: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = 'OPERATIONAL'
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = 0.0
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    warranty_expiry: Optional[date] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    warranty_expiry: Optional[date] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


class AssetResponse(AssetBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    work_order_count: Optional[int] = 0
    pending_work_orders: Optional[int] = 0

    class Config:
        from_attributes = True


# ==================== MAINTENANCE TYPE SCHEMAS ====================

class MaintenanceTypeBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    is_scheduled: Optional[bool] = False


class MaintenanceTypeCreate(MaintenanceTypeBase):
    pass


class MaintenanceTypeResponse(MaintenanceTypeBase):
    id: UUID

    class Config:
        from_attributes = True


# ==================== WORK ORDER SCHEMAS ====================

class WorkOrderBase(BaseModel):
    asset_id: UUID
    type_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    priority: Optional[str] = 'MEDIUM'
    status: Optional[str] = 'DRAFT'
    scheduled_date: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    asset_id: Optional[UUID] = None
    type_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    id: UUID
    code: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reported_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    asset_name: Optional[str] = None
    asset_code: Optional[str] = None
    type_name: Optional[str] = None
    assigned_name: Optional[str] = None
    total_cost: Optional[float] = 0.0
    task_count: Optional[int] = 0
    completed_tasks: Optional[int] = 0

    class Config:
        from_attributes = True


# ==================== WORK ORDER TASK SCHEMAS ====================

class WorkOrderTaskBase(BaseModel):
    description: str
    is_completed: Optional[bool] = False


class WorkOrderTaskCreate(WorkOrderTaskBase):
    pass


class WorkOrderTaskResponse(WorkOrderTaskBase):
    id: UUID
    work_order_id: UUID
    completed_at: Optional[datetime] = None
    completed_by: Optional[UUID] = None

    class Config:
        from_attributes = True


# ==================== WORK ORDER PART SCHEMAS ====================

class WorkOrderPartBase(BaseModel):
    part_name: str
    part_number: Optional[str] = None
    quantity: Optional[int] = 1
    unit_cost: Optional[float] = 0.0


class WorkOrderPartCreate(WorkOrderPartBase):
    pass


class WorkOrderPartResponse(WorkOrderPartBase):
    id: UUID
    work_order_id: UUID
    total_cost: float

    class Config:
        from_attributes = True


# ==================== WORK ORDER COST SCHEMAS ====================

class WorkOrderCostBase(BaseModel):
    category: Optional[str] = 'OTHER'
    description: str
    amount: float
    date: Optional[date] = None


class WorkOrderCostCreate(WorkOrderCostBase):
    pass


class WorkOrderCostResponse(WorkOrderCostBase):
    id: UUID
    work_order_id: UUID

    class Config:
        from_attributes = True


# ==================== MAINTENANCE SCHEDULE SCHEMAS ====================

class MaintenanceScheduleBase(BaseModel):
    asset_id: UUID
    type_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    frequency: Optional[str] = 'MONTHLY'
    interval_days: Optional[int] = 30
    next_due: Optional[date] = None
    is_active: Optional[bool] = True


class MaintenanceScheduleCreate(MaintenanceScheduleBase):
    pass


class MaintenanceScheduleUpdate(BaseModel):
    asset_id: Optional[UUID] = None
    type_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    interval_days: Optional[int] = None
    next_due: Optional[date] = None
    is_active: Optional[bool] = None


class MaintenanceScheduleResponse(MaintenanceScheduleBase):
    id: UUID
    last_performed: Optional[date] = None
    created_at: Optional[datetime] = None
    asset_name: Optional[str] = None
    asset_code: Optional[str] = None
    type_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== DASHBOARD STATS ====================

class MaintenanceStats(BaseModel):
    total_assets: int = 0
    operational_assets: int = 0
    under_maintenance: int = 0
    broken_assets: int = 0
    total_work_orders: int = 0
    pending_work_orders: int = 0
    in_progress_work_orders: int = 0
    completed_this_month: int = 0
    overdue_schedules: int = 0
    upcoming_schedules: int = 0
    total_costs_this_month: float = 0.0
