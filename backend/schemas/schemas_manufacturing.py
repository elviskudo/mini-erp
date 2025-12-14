from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from enum import Enum

class ProductType(str, Enum):
    RAW_MATERIAL = "Raw Material"
    WIP = "WIP"
    FINISHED_GOODS = "Finished Goods"

# Work Center Schemas
class WorkCenterBase(BaseModel):
    code: str
    name: str
    hourly_rate: float = 0.0
    capacity_per_hour: float = 0.0

class WorkCenterCreate(WorkCenterBase):
    pass

class WorkCenterResponse(WorkCenterBase):
    id: UUID
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    code: str
    name: str
    type: ProductType = ProductType.RAW_MATERIAL
    uom: str = "pcs"

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
