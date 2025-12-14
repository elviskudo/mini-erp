from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime
import database
import models
import schemas
from services.inventory_ledger import record_movement

router = APIRouter(
    prefix="/delivery",
    tags=["Delivery & Logistics"]
)

@router.post("/create", response_model=schemas.DeliveryOrderResponse)
async def create_delivery(payload: schemas.DeliveryOrderCreate, db: AsyncSession = Depends(database.get_db)):
    # 1. Create DO Header
    new_do = models.DeliveryOrder(
        so_id=payload.so_id,
        customer_id=payload.customer_id,
        status=models.DeliveryStatus.DRAFT
    )
    db.add(new_do)
    await db.flush()

    # 2. Add Items
    for item in payload.items:
        do_item = models.DeliveryItem(
            delivery_order_id=new_do.id,
            product_id=item.product_id,
            quantity=item.quantity,
            batch_id=item.batch_id
        )
        db.add(do_item)
    
    await db.commit()
    await db.refresh(new_do)
    return new_do

@router.post("/{do_id}/ship", response_model=schemas.DeliveryOrderResponse)
async def ship_delivery(do_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch DO
    query = select(models.DeliveryOrder)\
        .where(models.DeliveryOrder.id == do_id)\
        .options(selectinload(models.DeliveryOrder.items))
    result = await db.execute(query)
    do = result.scalar_one_or_none()

    if not do:
        raise HTTPException(status_code=404, detail="Delivery Order not found")
    if do.status != models.DeliveryStatus.DRAFT:
        raise HTTPException(status_code=400, detail="DO already shipped or delivered")

    # 2. Deduct Stock & Record Ledger
    for item in do.items:
        # Lock Batch
        batch = await db.get(models.InventoryBatch, item.batch_id)
        if not batch:
             raise HTTPException(status_code=400, detail=f"Batch {item.batch_id} not found")
        
        if batch.quantity_on_hand < item.quantity:
             raise HTTPException(status_code=400, detail=f"Insufficient stock in batch {batch.batch_number}")
        
        # Deduct
        batch.quantity_on_hand -= item.quantity

        # Ledger
        await record_movement(
            db,
            product_id=item.product_id,
            location_id=batch.location_id,
            quantity_change=-item.quantity,
            movement_type=models.MovementType.OUT_DELIVERY,
            batch_id=batch.id,
            reference_id=str(do.id),
            notes=f"Shipped via DO {do.so_id or 'Direct'}"
        )

    # 3. Update Status
    do.status = models.DeliveryStatus.SHIPPED
    await db.commit()
    await db.refresh(do)
    return do

@router.get("/orders", response_model=List[schemas.DeliveryOrderResponse])
async def list_dos(db: AsyncSession = Depends(database.get_db)):
    query = select(models.DeliveryOrder).options(selectinload(models.DeliveryOrder.items).selectinload(models.DeliveryItem.product))
    result = await db.execute(query)
    return result.scalars().all()
