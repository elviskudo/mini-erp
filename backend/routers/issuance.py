from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid
from datetime import datetime
import database
import models
from models import models_receiving
import schemas
from services.inventory_ledger import record_movement

router = APIRouter(
    prefix="/issuance",
    tags=["Material Issuance"]
)

@router.get("/available_batches/{product_id}", response_model=List[schemas.BatchSuggestion])
async def get_available_batches(product_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    """
    FEFO Logic: Suggest batches ordered by expiration date (ascending).
    If expiration date is null, they come last (or first depending on policy, assuming last here).
    """
    query = select(models_receiving.InventoryBatch)\
        .join(models.InventoryBatch.location)\
        .where(
            models.InventoryBatch.product_id == product_id,
            models.InventoryBatch.quantity_on_hand > 0
        )\
        .order_by(
            models.InventoryBatch.expiration_date.asc().nullslast()
        )
    result = await db.execute(query)
    batches = result.scalars().all()
    
    return [
        schemas.BatchSuggestion(
            batch_id=b.id,
            batch_number=b.batch_number,
            quantity_on_hand=b.quantity_on_hand,
            expiration_date=b.expiration_date,
            location_name=b.location.name
        ) for b in batches
    ]

@router.post("/issue")
async def issue_material(request: schemas.IssueRequest, db: AsyncSession = Depends(database.get_db)):
    # 1. Lock Batch
    batch = await db.get(models.InventoryBatch, request.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # 2. Validate
    if batch.quantity_on_hand < request.quantity:
        raise HTTPException(status_code=400, detail="Insufficient quantity in batch")
    if batch.product_id != request.product_id:
        raise HTTPException(status_code=400, detail="Product mismatch")
    
    # 3. Deduct Stock
    batch.quantity_on_hand -= request.quantity
    
    # 4. Record Ledger
    await record_movement(
        db,
        product_id=request.product_id,
        location_id=request.location_id,
        quantity_change=-request.quantity, # Negative for Issue
        movement_type=models.MovementType.OUT_ISSUE,
        batch_id=request.batch_id,
        reference_id=request.reference_id,
        project_id=request.project_id,
        notes=f"Issued to Production"
    )
    
    await db.commit()
    return {"status": "Issued", "remaining_qty": batch.quantity_on_hand}
