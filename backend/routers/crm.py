from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid
import database
from models import models_crm
from models import models_sales
from models import models_receiving
import schemas

router = APIRouter(
    prefix="/crm",
    tags=["CRM & Sales"]
)

@router.post("/orders", response_model=schemas.SOResponse)
async def create_order(order: schemas.SOCreate, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch Customer & Check Credit Limit
    customer = await db.get(models_sales.Customer, order.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    total_order_amount = sum(item.quantity * item.unit_price for item in order.items)
    
    if customer.current_balance + total_order_amount > customer.credit_limit:
        raise HTTPException(status_code=400, detail="Credit limit exceeded")

    # 2. Check Stock Availability (Optional: Can be done at confirmation, but good to check now)
    # Strategy: Sum up quantity needed per product and check total on hand across all batches?
    # Or strict check? Let's do a simple check.
    
    for item in order.items:
        # Sum quantity on hand for this product
        res = await db.execute(
            select(models_receiving.InventoryBatch)
            .where(models_receiving.InventoryBatch.product_id == item.product_id)
        )
        batches = res.scalars().all()
        total_on_hand = sum(b.quantity_on_hand for b in batches)
        
        if total_on_hand < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {item.product_id}. Available: {total_on_hand}")

    # 3. Create Order
    new_so = models_crm.SalesOrder(
        customer_id=order.customer_id,
        status=models_crm.SOStatus.DRAFT,
        total_amount=total_order_amount
    )
    db.add(new_so)
    await db.flush()
    
    for item in order.items:
        so_item = models_crm.SOItem(
            sales_order_id=new_so.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.quantity * item.unit_price
        )
        db.add(so_item)
        
    await db.commit()
    await db.refresh(new_so)
    return new_so

@router.post("/orders/{id}/confirm", response_model=schemas.SOResponse)
async def confirm_order(id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch Order
    query = select(models_crm.SalesOrder).where(models_crm.SalesOrder.id == id).options(selectinload(models_crm.SalesOrder.items))
    result = await db.execute(query)
    so = result.scalar_one_or_none()
    
    if not so:
        raise HTTPException(status_code=404, detail="Order not found")
    if so.status != models_crm.SOStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Order already confirmed or cancelled")
        
    # 2. Reserve Stock?
    # For MVP, we just change status. Real reservation would involve deducting 'Allocated' qty.
    # We will assume "Confirmed" means ready for Delivery.
    
    so.status = models_crm.SOStatus.CONFIRMED
    await db.commit()
    return so

@router.get("/orders", response_model=List[schemas.SOResponse])
async def list_orders(db: AsyncSession = Depends(database.get_db)):
    query = select(models_crm.SalesOrder).options(selectinload(models_crm.SalesOrder.items))
    result = await db.execute(query)
    return result.scalars().all()
