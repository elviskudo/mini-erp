from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime
import database
import models
from models import models_ledger, models_procurement
import schemas
from services.inventory_ledger import record_movement
from services.notification_service import notify_goods_receipt
from auth import get_current_user

router = APIRouter(
    prefix="/receiving",
    tags=["Goods Receipt"]
)

@router.post("/receive", response_model=schemas.GRResponse)
async def receive_goods(
    payload: schemas.ReceivePORequest, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Validate PO and load items
    query = select(models_procurement.PurchaseOrder).where(
        models_procurement.PurchaseOrder.id == payload.po_id
    ).options(selectinload(models_procurement.PurchaseOrder.items))
    result = await db.execute(query)
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    if po.status not in [models_procurement.POStatus.OPEN, models_procurement.POStatus.PARTIAL_RECEIVE]:
        raise HTTPException(status_code=400, detail=f"PO status must be OPEN or PARTIAL_RECEIVE to receive goods. Current: {po.status}")

    # 2. Create Goods Receipt Header
    gr = models.GoodsReceipt(
        po_id=payload.po_id,
        warehouse_id=payload.warehouse_id,
        tenant_id=current_user.tenant_id,
        received_by=current_user.id,
        notes=payload.notes
    )
    db.add(gr)
    await db.flush()

    # 3. Create Batches, Record Ledger, and Update POLine received_qty
    total_received_this_time = 0
    for item in payload.items:
        # Convert timezone-aware datetime to naive datetime if needed
        exp_date = item.expiration_date
        if exp_date and hasattr(exp_date, 'tzinfo') and exp_date.tzinfo is not None:
            exp_date = exp_date.replace(tzinfo=None)
        
        batch = models.InventoryBatch(
            product_id=item.product_id,
            batch_number=item.batch_number,
            quantity_on_hand=item.quantity,
            expiration_date=exp_date,
            location_id=item.location_id,
            goods_receipt_id=gr.id,
            tenant_id=current_user.tenant_id
        )
        db.add(batch)
        await db.flush()

        # Record Ledger Entry
        await record_movement(
            db,
            product_id=item.product_id,
            location_id=item.location_id,
            quantity_change=item.quantity,
            movement_type=models_ledger.MovementType.INBOUND,
            batch_id=batch.id,
            reference_id=str(gr.id),
            notes=f"Goods Receipt from PO {payload.po_id}",
            tenant_id=current_user.tenant_id
        )
        
        # Update POLine received_qty
        for po_line in po.items:
            if po_line.product_id == item.product_id:
                po_line.received_qty = (po_line.received_qty or 0) + item.quantity
                break
        
        total_received_this_time += item.quantity
    
    # 4. Calculate Progress and Update PO Status
    total_ordered = sum(line.quantity or 0 for line in po.items)
    total_received = sum(line.received_qty or 0 for line in po.items)
    
    if total_ordered > 0:
        progress = (total_received / total_ordered) * 100
        po.progress = min(progress, 100.0)  # Cap at 100%
    else:
        po.progress = 100.0
    
    # Set status based on progress
    if po.progress >= 100:
        po.status = models_procurement.POStatus.CLOSED
    else:
        po.status = models_procurement.POStatus.PARTIAL_RECEIVE
    
    await db.commit()
    await db.refresh(gr)
    
    # Send notification to realtime server
    try:
        await notify_goods_receipt(
            tenant_id=str(current_user.tenant_id),
            po_number=po.po_number or str(po.id)[:8],
            batches_created=len(payload.items),
            progress=po.progress,
            status=po.status.value,
            received_by=str(current_user.id)
        )
    except Exception as e:
        print(f"Notification failed: {e}")
    
    return {
        "id": gr.id,
        "po_id": gr.po_id,
        "batches_created": len(payload.items),
        "progress": po.progress,
        "status": po.status.value
    }
