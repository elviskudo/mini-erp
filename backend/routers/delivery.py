from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
import uuid
from datetime import datetime
import database
import models
import schemas
from services.inventory_ledger import record_movement
from auth import get_current_user

router = APIRouter(
    prefix="/delivery",
    tags=["Delivery & Logistics"]
)


# Enhanced schemas
class DeliveryItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    batch_id: Optional[UUID] = None


class DeliveryOrderCreate(BaseModel):
    so_id: Optional[str] = None
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    items: List[DeliveryItemCreate]


class DeliveryItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: Optional[str] = None
    quantity: float
    batch_id: Optional[UUID] = None
    batch_number: Optional[str] = None

    class Config:
        from_attributes = True


class DeliveryOrderResponse(BaseModel):
    id: UUID
    do_number: Optional[str] = None
    so_id: Optional[str] = None
    customer_name: Optional[str] = None
    shipping_address: Optional[str] = None
    status: str
    items_count: int = 0
    created_at: datetime
    items: List[DeliveryItemResponse] = []

    class Config:
        from_attributes = True


@router.get("/orders", response_model=List[DeliveryOrderResponse])
async def list_dos(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(models.DeliveryOrder)\
        .where(models.DeliveryOrder.tenant_id == current_user.tenant_id)\
        .options(
            selectinload(models.DeliveryOrder.items).selectinload(models.DeliveryItem.product),
            selectinload(models.DeliveryOrder.items).selectinload(models.DeliveryItem.batch)
        )\
        .order_by(models.DeliveryOrder.created_at.desc())
    result = await db.execute(query)
    orders = result.scalars().all()
    
    responses = []
    for do in orders:
        # Generate DO number if not exists
        do_number = f"DO-{do.created_at.strftime('%Y%m')}-{str(do.id)[:8].upper()}"
        
        items = []
        for item in do.items:
            items.append(DeliveryItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else None,
                quantity=item.quantity,
                batch_id=item.batch_id,
                batch_number=item.batch.batch_number if item.batch else None
            ))
        
        responses.append(DeliveryOrderResponse(
            id=do.id,
            do_number=do_number,
            so_id=do.so_id,
            customer_name=getattr(do, 'customer_name', None),
            shipping_address=getattr(do, 'shipping_address', None),
            status=do.status.value,
            items_count=len(do.items),
            created_at=do.created_at,
            items=items
        ))
    
    return responses


@router.post("/create", response_model=DeliveryOrderResponse)
async def create_delivery(
    payload: DeliveryOrderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Create DO Header with tenant_id
    new_do = models.DeliveryOrder(
        tenant_id=current_user.tenant_id,
        so_id=payload.so_id,
        customer_id=payload.customer_id,
        status=models.DeliveryStatus.DRAFT
    )
    db.add(new_do)
    await db.flush()

    # Add Items with tenant_id
    for item in payload.items:
        do_item = models.DeliveryItem(
            tenant_id=current_user.tenant_id,
            delivery_order_id=new_do.id,
            product_id=item.product_id,
            quantity=item.quantity,
            batch_id=item.batch_id
        )
        db.add(do_item)
    
    await db.commit()
    await db.refresh(new_do)
    
    # Generate DO number
    do_number = f"DO-{new_do.created_at.strftime('%Y%m')}-{str(new_do.id)[:8].upper()}"
    
    return DeliveryOrderResponse(
        id=new_do.id,
        do_number=do_number,
        so_id=new_do.so_id,
        customer_name=getattr(new_do, 'customer_name', None),
        shipping_address=getattr(new_do, 'shipping_address', None),
        status=new_do.status.value,
        items_count=len(payload.items),
        created_at=new_do.created_at,
        items=[]
    )


@router.post("/{do_id}/ship")
async def ship_delivery(
    do_id: uuid.UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch DO
    query = select(models.DeliveryOrder)\
        .where(
            models.DeliveryOrder.id == do_id,
            models.DeliveryOrder.tenant_id == current_user.tenant_id
        )\
        .options(selectinload(models.DeliveryOrder.items))
    result = await db.execute(query)
    do = result.scalar_one_or_none()

    if not do:
        raise HTTPException(status_code=404, detail="Delivery Order not found")
    if do.status != models.DeliveryStatus.DRAFT:
        raise HTTPException(status_code=400, detail="DO already shipped or delivered")

    # Deduct Stock & Record Ledger
    for item in do.items:
        if item.batch_id:
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

    # Update Status
    do.status = models.DeliveryStatus.SHIPPED
    await db.commit()
    
    return {"detail": "Delivery order shipped successfully"}


@router.get("/{do_id}", response_model=DeliveryOrderResponse)
async def get_delivery_order(
    do_id: uuid.UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(models.DeliveryOrder)\
        .where(
            models.DeliveryOrder.id == do_id,
            models.DeliveryOrder.tenant_id == current_user.tenant_id
        )\
        .options(
            selectinload(models.DeliveryOrder.items).selectinload(models.DeliveryItem.product),
            selectinload(models.DeliveryOrder.items).selectinload(models.DeliveryItem.batch)
        )
    result = await db.execute(query)
    do = result.scalar_one_or_none()
    
    if not do:
        raise HTTPException(status_code=404, detail="Delivery Order not found")
    
    do_number = f"DO-{do.created_at.strftime('%Y%m')}-{str(do.id)[:8].upper()}"
    
    items = []
    for item in do.items:
        items.append(DeliveryItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            quantity=item.quantity,
            batch_id=item.batch_id,
            batch_number=item.batch.batch_number if item.batch else None
        ))
    
    return DeliveryOrderResponse(
        id=do.id,
        do_number=do_number,
        so_id=do.so_id,
        customer_name=getattr(do, 'customer_name', None),
        shipping_address=getattr(do, 'shipping_address', None),
        status=do.status.value,
        items_count=len(do.items),
        created_at=do.created_at,
        items=items
    )
