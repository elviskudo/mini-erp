from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid
import database
import models
from models import models_procurement
import schemas

router = APIRouter(
    prefix="/procurement",
    tags=["Procurement"]
)

# Vendor Endpoints
@router.post("/vendors", response_model=schemas.POResponse) 
async def create_vendor(vendor: schemas.VendorCreate, db: AsyncSession = Depends(database.get_db)):
    new_vendor = models.Vendor(**vendor.dict())
    db.add(new_vendor)
    try:
        await db.commit()
        await db.refresh(new_vendor)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": new_vendor.id, "status": "Active", "vendor_id": new_vendor.id}

@router.get("/vendors", response_model=List[schemas.POResponse]) 
async def list_vendors(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Vendor))
    return result.scalars().all()

@router.get("/pr", response_model=List[schemas.PRResponse])
async def list_prs(db: AsyncSession = Depends(database.get_db)):
    query = select(models.PurchaseRequest).options(selectinload(models.PurchaseRequest.items).selectinload(models.PRLine.product))
    result = await db.execute(query)
    return result.scalars().all()

# PR Endpoints
@router.post("/pr", response_model=schemas.PRResponse)
async def create_pr(pr: schemas.PRCreate, db: AsyncSession = Depends(database.get_db)):
    new_pr = models.PurchaseRequest()
    db.add(new_pr)
    await db.flush()

    for item in pr.items:
        line = models.PRLine(
            pr_id=new_pr.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(new_pr)
    return new_pr

@router.post("/pr/{pr_id}/approve")
async def approve_pr(pr_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    pr = await db.get(models.PurchaseRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    
    pr.status = models.PRStatus.APPROVED
    await db.commit()
    return {"status": "Approved"}

# PO Endpoints
@router.post("/po/create_from_pr", response_model=schemas.POResponse)
async def convert_pr_to_po(payload: schemas.POCreateFromPR, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch PR
    query = select(models_procurement.PurchaseRequest)\
        .where(models_procurement.PurchaseRequest.id == payload.pr_id)\
        .options(selectinload(models_procurement.PurchaseRequest.items))
    result = await db.execute(query)
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    if pr.status != models_procurement.PRStatus.APPROVED:
        raise HTTPException(status_code=400, detail="PR must be approved")

    # 2. Create PO
    new_po = models.PurchaseOrder(
        vendor_id=payload.vendor_id,
        pr_id=pr.id,
        status=models.POStatus.DRAFT
    )
    db.add(new_po)
    await db.flush()

    # 3. Copy items
    for item in pr.items:
        price = payload.price_map.get(str(item.product_id), 0.0)
        po_line = models.POLine(
            po_id=new_po.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=price
        )
        db.add(po_line)
    
    # 4. Update PR
    pr.status = models_procurement.PRStatus.CONVERTED
    
    await db.commit()
    await db.refresh(new_po)
    return new_po

@router.post("/orders", response_model=schemas.PurchaseOrderResponse)
async def create_purchase_order(
    order: schemas.PurchaseOrderCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db)
):
    # 1. Create PO Header
    db_order = models.PurchaseOrder(
        id=str(uuid.uuid4()),
        vendor_id=order.vendor_id,
        order_date=order.order_date,
        expected_date=order.expected_date,
        status="Draft",
        total_amount=0.0
    )
    db.add(db_order)
    await db.flush()
    
    total = 0.0
    
    # 2. Add Items
    for item in order.items:
        # Get standard cost from Product
        # Assuming models.Product exists and has standard_cost
        # and that models.POLine is the correct model for PO items
        product_result = await db.execute(select(models.Product).where(models.Product.id == item.product_id))
        prod = product_result.scalar_one_or_none()
        unit_price = prod.standard_cost if prod else 0.0
        
        db_item = models.POLine( # Changed from PurchaseOrderItem to POLine
            id=str(uuid.uuid4()), # Assuming POLine has an 'id' field
            po_id=db_order.id, # Changed from purchase_order_id to po_id
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=unit_price,
            subtotal=item.quantity * unit_price # Assuming POLine has a 'subtotal' field
        )
        db.add(db_item)
        total += db_item.subtotal
        
    db_order.total_amount = total
    await db.commit()
    await db.refresh(db_order)
    
    # Send Notification
    # Assuming 'notifications' module is in the parent directory
    from ..notifications import send_notification 
    background_tasks.add_task(
        send_notification, 
        user_id="all", 
        title="New PO Created", 
        message=f"PO {db_order.id} created for ${total}"
    )
    
    return db_order

@router.get("/orders", response_model=List[schemas.POResponse])
async def list_pos(db: AsyncSession = Depends(database.get_db)):
    query = select(models.PurchaseOrder).options(selectinload(models.PurchaseOrder.vendor), selectinload(models.PurchaseOrder.items).selectinload(models.POLine.product))
    result = await db.execute(query)
    return result.scalars().all()
