from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid
import database
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

# Warehouse Endpoints
@router.post("/warehouses", response_model=schemas.WarehouseResponse)
async def create_warehouse(
    warehouse: schemas.WarehouseCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    data = warehouse.dict()
    data['tenant_id'] = current_user.tenant_id  # Set tenant_id from current user
    new_wh = models.Warehouse(**data)
    db.add(new_wh)
    try:
        await db.commit()
        # Re-fetch with selectinload to properly load locations for response
        result = await db.execute(
            select(models.Warehouse)
            .options(selectinload(models.Warehouse.locations))
            .where(models.Warehouse.id == new_wh.id)
        )
        return result.scalar_one()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/warehouses", response_model=List[schemas.WarehouseResponse])
async def read_warehouses(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    query = select(models.Warehouse)\
        .options(selectinload(models.Warehouse.locations))\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

# Location Endpoints
@router.post("/warehouses/{warehouse_id}/locations", response_model=schemas.LocationResponse)
async def create_location(warehouse_id: uuid.UUID, location: schemas.LocationCreate, db: AsyncSession = Depends(database.get_db)):
    new_loc = models.Location(
        warehouse_id=warehouse_id,
        **location.dict()
    )
    db.add(new_loc)
    try:
        await db.commit()
        await db.refresh(new_loc)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_loc

@router.get("/stock")
async def list_stock(db: AsyncSession = Depends(database.get_db)):
    # Return all batches with qty > 0
    query = select(models.InventoryBatch)\
        .where(models.InventoryBatch.quantity_on_hand > 0)\
        .options(selectinload(models.InventoryBatch.product), selectinload(models.InventoryBatch.location))
    result = await db.execute(query)
    return result.scalars().all()
