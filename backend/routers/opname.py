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
    prefix="/opname",
    tags=["Stock Opname"]
)

@router.post("/create", response_model=schemas.OpnameResponse)
async def create_opname(request: schemas.OpnameCreate, db: AsyncSession = Depends(database.get_db)):
    # 1. Create Header
    new_opname = models.StockOpname(
        warehouse_id=request.warehouse_id,
        status=models.OpnameStatus.DRAFT,
        notes=request.notes
    )
    db.add(new_opname)
    await db.flush()

    # 2. Snapshot current stock in this warehouse
    # Query all batches in locations belonging to this warehouse
    # For MVP: We just grab all batches that have qty > 0 in this warehouse
    query = select(models.InventoryBatch)\
        .join(models.InventoryBatch.location)\
        .where(
            models.Location.warehouse_id == request.warehouse_id,
            models.InventoryBatch.quantity_on_hand > 0
        )
    result = await db.execute(query)
    batches = result.scalars().all()

    for batch in batches:
        detail = models.StockOpnameDetail(
            opname_id=new_opname.id,
            product_id=batch.product_id,
            batch_id=batch.id,
            system_qty=batch.quantity_on_hand,
            counted_qty=None # To be filled
        )
        db.add(detail)

    await db.commit()
    await db.refresh(new_opname)
    return new_opname

@router.post("/update_count")
async def update_count(updates: List[schemas.OpnameDetailUpdate], db: AsyncSession = Depends(database.get_db)):
    for update in updates:
        detail = await db.get(models.StockOpnameDetail, update.detail_id)
        if detail:
            detail.counted_qty = update.counted_qty
    
    await db.commit()
    return {"status": "Updated", "count": len(updates)}

@router.post("/post")
async def post_opname(payload: schemas.OpnamePostRequest, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch Opname
    query = select(models.StockOpname)\
        .where(models.StockOpname.id == payload.opname_id)\
        .options(selectinload(models.StockOpname.details))
    result = await db.execute(query)
    opname = result.scalar_one_or_none()

    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    if opname.status != models.OpnameStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Opname already posted")

    # 2. Process Adjustments
    for detail in opname.details:
        if detail.counted_qty is None:
            continue # Skip uncounted items? Or assume 0? For safety, skip.
        
        diff = detail.counted_qty - detail.system_qty
        
        if diff != 0:
            # Update Batch
            batch = await db.get(models.InventoryBatch, detail.batch_id)
            if batch:
                batch.quantity_on_hand = detail.counted_qty
                
                # Record Ledger
                await record_movement(
                    db,
                    product_id=detail.product_id,
                    location_id=batch.location_id,
                    quantity_change=diff, # + or -
                    movement_type=models.MovementType.ADJUSTMENT,
                    batch_id=batch.id,
                    reference_id=str(opname.id),
                    notes=f"Stock Opname Adjustment"
                )

    opname.status = models.OpnameStatus.POSTED
    
    await db.commit()
    return {"status": "Posted"}

@router.get("/list", response_model=List[schemas.OpnameResponse])
async def list_opnames(db: AsyncSession = Depends(database.get_db)):
    query = select(models.StockOpname).options(selectinload(models.StockOpname.warehouse))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{opname_id}", response_model=schemas.OpnameResponse)
async def get_opname(opname_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    query = select(models.StockOpname)\
        .where(models.StockOpname.id == opname_id)\
        .options(selectinload(models.StockOpname.warehouse), selectinload(models.StockOpname.details).selectinload(models.StockOpnameDetail.product))
    result = await db.execute(query)
    opname = result.scalar_one_or_none()
    if not opname:
         raise HTTPException(status_code=404, detail="Opname not found")
    return opname
