from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import uuid
from datetime import datetime
import database
import models
from models import models_ledger
import schemas
from services.inventory_ledger import record_movement

router = APIRouter(
    prefix="/receiving",
    tags=["Goods Receipt"]
)

@router.post("/receive", response_model=schemas.GRResponse)
async def receive_goods(payload: schemas.ReceivePORequest, db: AsyncSession = Depends(database.get_db)):
    # 1. Validate PO
    po = await db.get(models.PurchaseOrder, payload.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    if po.status != models.POStatus.SENT and po.status != models.POStatus.DRAFT:
         # allowing DRAFT for flexibility in testing, but usually SENT
         pass

    # 2. Create Goods Receipt Header
    gr = models.GoodsReceipt(
        po_id=payload.po_id,
        warehouse_id=payload.warehouse_id
    )
    db.add(gr)
    await db.flush()

    # 3. Create Batches and Record Ledger
    for item in payload.items:
        batch = models.InventoryBatch(
            product_id=item.product_id,
            batch_number=item.batch_number,
            quantity_on_hand=item.quantity,
            expiration_date=item.expiration_date,
            location_id=item.location_id,
            goods_receipt_id=gr.id
        )
        db.add(batch)
        await db.flush() # Need ID for ledger

        # Record Ledger Entry
        await record_movement(
            db,
            product_id=item.product_id,
            location_id=item.location_id,
            quantity_change=item.quantity,
            movement_type=models_ledger.MovementType.INBOUND,
            batch_id=batch.id,
            reference_id=str(gr.id),
            notes=f"Goods Receipt from PO {payload.po_id}"
        )
    
    # 4. Update PO Status
    po.status = models.POStatus.COMPLETED
    
    await db.commit()
    await db.refresh(gr)
    
    return {
        "id": gr.id,
        "po_id": gr.po_id,
        "batches_created": len(payload.items)
    }
