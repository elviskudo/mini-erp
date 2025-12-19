from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from io import BytesIO
from datetime import datetime
import uuid
import database
import models
from models import models_procurement
import schemas
from services.pdf_service import generate_po_pdf, generate_simple_pdf

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


@router.get("/orders/{order_id}/pdf")
async def download_po_pdf(
    order_id: str,
    db: AsyncSession = Depends(database.get_db)
):
    """Generate and download PO as PDF"""
    # Get PO with vendor and items
    query = select(models.PurchaseOrder)\
        .where(models.PurchaseOrder.id == order_id)\
        .options(
            selectinload(models.PurchaseOrder.vendor),
            selectinload(models.PurchaseOrder.items).selectinload(models.POLine.product)
        )
    result = await db.execute(query)
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    
    # Prepare data for PDF
    items = []
    subtotal = 0
    for item in po.items:
        item_total = item.quantity * item.unit_price
        subtotal += item_total
        items.append({
            'product_name': item.product.name if item.product else 'Unknown',
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total': item_total
        })
    
    grand_total = subtotal + (po.shipping_cost or 0) + (po.insurance_cost or 0) + (po.customs_duty or 0)
    
    po_data = {
        'po_number': po.po_number if hasattr(po, 'po_number') and po.po_number else str(po.id)[:8].upper(),
        'po_date': po.created_at.strftime('%d %B %Y') if hasattr(po, 'created_at') and po.created_at else datetime.now().strftime('%d %B %Y'),
        'expected_date': po.expected_delivery.strftime('%d %B %Y') if hasattr(po, 'expected_delivery') and po.expected_delivery else '-',
        'tenant_name': 'PT. Mini ERP Indonesia',  # TODO: Get from tenant
        'tenant_logo': None,  # TODO: Get from tenant settings
        'tenant_address': 'Jakarta, Indonesia',
        'vendor_name': po.vendor.name if po.vendor else 'Unknown Vendor',
        'vendor_address': po.vendor.address if po.vendor and hasattr(po.vendor, 'address') else '',
        'vendor_email': po.vendor.email if po.vendor else '',
        'vendor_phone': po.vendor.phone if po.vendor and hasattr(po.vendor, 'phone') else '',
        'ship_to_name': 'Warehouse',
        'ship_to_address': 'Main Warehouse',
        'items': items,
        'subtotal': subtotal,
        'shipping_cost': po.shipping_cost or 0,
        'insurance_cost': po.insurance_cost or 0,
        'customs_duty': po.customs_duty or 0,
        'grand_total': grand_total
    }
    
    # Generate PDF using fallback (FPDF2) for reliability
    try:
        pdf_bytes = generate_simple_pdf(po_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
    
    # Return as downloadable file
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=PO-{po_data['po_number']}.pdf"
        }
    )


@router.post("/orders/{order_id}/send")
async def send_po_to_vendor(
    order_id: str,
    db: AsyncSession = Depends(database.get_db)
):
    """Send PO to vendor - changes status from Draft to Open"""
    result = await db.execute(select(models.PurchaseOrder).where(models.PurchaseOrder.id == order_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    
    if po.status != models.POStatus.DRAFT:
        raise HTTPException(status_code=400, detail="PO must be in Draft status")
    
    po.status = models.POStatus.OPEN
    await db.commit()
    return {"message": "PO sent to vendor", "status": "Open"}


@router.post("/orders/{order_id}/receive")
async def receive_goods(
    order_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db)
):
    """Receive goods against PO with landed cost calculation"""
    # 1. Get PO with items
    query = select(models.PurchaseOrder)\
        .where(models.PurchaseOrder.id == order_id)\
        .options(selectinload(models.PurchaseOrder.items).selectinload(models.POLine.product))
    result = await db.execute(query)
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    
    if po.status not in [models.POStatus.OPEN, models.POStatus.PARTIAL_RECEIVE]:
        raise HTTPException(status_code=400, detail="PO must be Open or Partial Receive")
    
    # 2. Update received quantities
    items_to_receive = payload.get('items', [])
    total_received_value = 0
    
    for item_data in items_to_receive:
        po_line_id = item_data.get('po_line_id')
        qty = item_data.get('quantity', 0)
        
        # Find the PO line
        for line in po.items:
            if str(line.id) == str(po_line_id):
                line.received_qty = (line.received_qty or 0) + qty
                total_received_value += qty * line.unit_price
                break
    
    # 3. Calculate landed cost
    shipping_cost = payload.get('shipping_cost', 0) or 0
    insurance_cost = payload.get('insurance_cost', 0) or 0
    customs_duty = payload.get('customs_duty', 0) or 0
    total_landed_cost = shipping_cost + insurance_cost + customs_duty
    
    # Update PO landed cost fields
    po.shipping_cost = (po.shipping_cost or 0) + shipping_cost
    po.insurance_cost = (po.insurance_cost or 0) + insurance_cost
    po.customs_duty = (po.customs_duty or 0) + customs_duty
    
    # 4. Check if fully received
    all_received = all(
        (line.received_qty or 0) >= line.quantity 
        for line in po.items
    )
    
    if all_received:
        po.status = models.POStatus.CLOSED
    else:
        po.status = models.POStatus.PARTIAL_RECEIVE
    
    # 5. Update weighted average cost for products (if landed cost > 0)
    if total_received_value > 0 and total_landed_cost > 0:
        allocation_ratio = total_landed_cost / total_received_value
        
        for item_data in items_to_receive:
            product_id = item_data.get('product_id')
            qty = item_data.get('quantity', 0)
            
            if qty > 0:
                prod_result = await db.execute(
                    select(models.Product).where(models.Product.id == product_id)
                )
                product = prod_result.scalar_one_or_none()
                
                if product:
                    # Find unit price from PO line
                    unit_price = 0
                    for line in po.items:
                        if str(line.product_id) == str(product_id):
                            unit_price = line.unit_price
                            break
                    
                    # Calculate landed unit cost
                    landed_unit_cost = unit_price * (1 + allocation_ratio)
                    
                    # Update weighted average cost (simplified)
                    if product.weighted_avg_cost == 0:
                        product.weighted_avg_cost = landed_unit_cost
                    else:
                        # Weighted average formula
                        product.weighted_avg_cost = (
                            (product.weighted_avg_cost + landed_unit_cost) / 2
                        )
    
    await db.commit()
    
    return {
        "message": "Goods received successfully",
        "status": str(po.status.value if hasattr(po.status, 'value') else po.status),
        "total_landed_cost": total_landed_cost
    }
