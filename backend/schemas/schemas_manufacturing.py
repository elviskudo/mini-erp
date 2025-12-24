from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from enum import Enum
from datetime import datetime

class ProductType(str, Enum):
    RAW_MATERIAL = "Raw Material"
    WIP = "WIP"
    FINISHED_GOODS = "Finished Goods"

# Work Center Schemas
class WorkCenterBase(BaseModel):
    code: str
    name: str
    cost_per_hour: float = 0.0
    capacity_hours: float = 8.0
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True

class WorkCenterCreate(WorkCenterBase):
    pass

class WorkCenterResponse(WorkCenterBase):
    id: UUID
    is_active: bool = True
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    type: ProductType = ProductType.RAW_MATERIAL
    uom: str = "pcs"
    image_url: Optional[str] = None
    is_manufactured: bool = True
    requires_cold_chain: bool = False
    max_storage_temp: Optional[float] = None
    desired_margin: Optional[float] = 0.3  # 30% default
    standard_cost: Optional[float] = 0.0

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: UUID
    class Config:
        from_attributes = True

# BOM Schemas
class BOMItemBase(BaseModel):
    component_id: UUID
    quantity: float
    waste_percentage: float = 0.0

class BOMItemCreate(BOMItemBase):
    pass

class BOMItemResponse(BOMItemBase):
    id: UUID
    component: ProductResponse # Nested info
    class Config:
        from_attributes = True

class BOMBase(BaseModel):
    product_id: UUID
    version: str = "1.0"
    is_active: bool = True

class BOMCreate(BOMBase):
    items: List[BOMItemCreate]

class BOMResponse(BOMBase):
    id: UUID
    product: ProductResponse
    items: List[BOMItemResponse]
    class Config:
        from_attributes = True


# Production Order Schemas
class ProductionOrderStatus(str, Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProductionOrderProductCreate(BaseModel):
    product_id: UUID


class ProductionOrderWorkCenterCreate(BaseModel):
    work_center_id: UUID


class ProductionOrderCreate(BaseModel):
    product_ids: List[UUID]
    work_center_ids: List[UUID] = []
    quantity: float
    scheduled_date: Optional[str] = None
    notes: Optional[str] = None


class ProductionOrderProductResponse(BaseModel):
    id: UUID
    product: ProductResponse
    class Config:
        from_attributes = True


class ProductionOrderWorkCenterResponse(BaseModel):
    id: UUID
    work_center: WorkCenterResponse
    class Config:
        from_attributes = True


class ProductionOrderResponse(BaseModel):
    id: UUID
    order_no: str
    status: ProductionOrderStatus
    quantity: float
    target_qty: float = 0.0
    completed_qty: float = 0.0
    progress: int
    scheduled_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    labor_hours: float = 0.0
    hourly_rate: float = 0.0
    material_cost: float = 0.0
    labor_cost: float = 0.0
    overhead_cost: float = 0.0
    total_hpp: float = 0.0
    hpp_per_unit: float = 0.0
    notes: Optional[str] = None
    products: List[ProductionOrderProductResponse] = []
    work_centers: List[ProductionOrderWorkCenterResponse] = []
    class Config:
        from_attributes = True
