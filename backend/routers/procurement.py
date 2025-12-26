from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List, Optional
from io import BytesIO
from datetime import datetime
import uuid
import database
import models
from models import models_procurement
import schemas
from services.pdf_service import generate_po_pdf, generate_simple_pdf
from auth import get_current_user

router = APIRouter(
    prefix="/procurement",
    tags=["Procurement"]
)

# Vendor Endpoints
@router.post("/vendors")
async def create_vendor(
    vendor: schemas.VendorCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate vendor code
    count_result = await db.execute(
        select(func.count(models.Vendor.id)).where(
            models.Vendor.tenant_id == current_user.tenant_id
        )
    )
    count = count_result.scalar() or 0
    vendor_code = vendor.code if vendor.code else f"V-{count + 1:04d}"
    
    # Convert string values to proper Enum types
    rating_val = models_procurement.VendorRating.B
    if vendor.rating:
        for r in models_procurement.VendorRating:
            if r.value == vendor.rating or r.name == vendor.rating:
                rating_val = r
                break
    
    category_val = models_procurement.VendorCategory.RAW_MATERIAL
    if vendor.category:
        for c in models_procurement.VendorCategory:
            if c.value == vendor.category or c.name == vendor.category:
                category_val = c
                break
    
    payment_term_val = models_procurement.PaymentTerm.NET_30
    if vendor.payment_term:
        for p in models_procurement.PaymentTerm:
            if p.value == vendor.payment_term or p.name == vendor.payment_term:
                payment_term_val = p
                break
    
    new_vendor = models.Vendor(
        tenant_id=current_user.tenant_id,
        code=vendor_code,
        name=vendor.name,
        email=vendor.email,
        phone=vendor.phone,
        address=vendor.address,
        rating=rating_val,
        category=category_val,
        payment_term=payment_term_val,
        credit_limit=vendor.credit_limit if vendor.credit_limit else 0.0
        # NOTE: latitude/longitude temporarily disabled - run migration first:
        # alembic revision --autogenerate -m "Add vendor lat lng"
        # alembic upgrade head
    )
    
    db.add(new_vendor)
    try:
        await db.commit()
        await db.refresh(new_vendor)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_vendor

@router.get("/vendors")
async def list_vendors(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Vendor).where(models.Vendor.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()

@router.get("/pr")
async def list_prs(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(models.PurchaseRequest).where(
        models.PurchaseRequest.tenant_id == current_user.tenant_id
    ).options(selectinload(models.PurchaseRequest.items).selectinload(models.PRLine.product))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/stock/{product_id}")
async def get_product_stock(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get available stock for a product with warehouse breakdown"""
    from models.models_receiving import InventoryBatch
    from models.models_inventory import Warehouse, Location
    
    # Get stock breakdown by warehouse
    stock_result = await db.execute(
        select(
            InventoryBatch.location_id,
            func.sum(InventoryBatch.quantity_on_hand).label('qty')
        ).where(
            InventoryBatch.product_id == product_id,
            InventoryBatch.tenant_id == current_user.tenant_id
        ).group_by(InventoryBatch.location_id)
    )
    stock_rows = stock_result.all()
    
    # Get warehouse info for each location
    warehouses_stock = []
    total_stock = 0
    for row in stock_rows:
        if row.location_id:
            location = await db.get(Location, row.location_id)
            warehouse = await db.get(Warehouse, location.warehouse_id) if location else None
            warehouses_stock.append({
                "warehouse_name": warehouse.name if warehouse else "Unknown",
                "location_code": location.code if location else "Unknown",
                "quantity": float(row.qty or 0)
            })
            total_stock += float(row.qty or 0)
    
    return {
        "product_id": str(product_id), 
        "available_stock": total_stock,
        "warehouses": warehouses_stock
    }

# PR Endpoints
@router.post("/pr", response_model=schemas.PRResponse)
async def create_pr(
    pr: schemas.PRCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate PR number
    count_result = await db.execute(
        select(func.count(models.PurchaseRequest.id)).where(
            models.PurchaseRequest.tenant_id == current_user.tenant_id
        )
    )
    count = count_result.scalar() or 0
    pr_number = f"PR-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    
    # Import InventoryBatch for stock check
    from models.models_receiving import InventoryBatch
    
    # Validate - check that requested products exist and qty doesn't exceed stock
    for item in pr.items:
        product = await db.get(models.Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=400, 
                detail=f"Product {item.product_id} not found"
            )
        
        # Get current stock for this product
        stock_result = await db.execute(
            select(func.coalesce(func.sum(InventoryBatch.quantity_on_hand), 0)).where(
                InventoryBatch.product_id == item.product_id,
                InventoryBatch.tenant_id == current_user.tenant_id
            )
        )
        current_stock = stock_result.scalar() or 0
        
        # Qty requested cannot exceed available stock
        if item.quantity > current_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Qty ({item.quantity}) untuk produk '{product.name}' melebihi stok tersedia ({current_stock})"
            )
    
    new_pr = models.PurchaseRequest(
        tenant_id=current_user.tenant_id,
        pr_number=pr_number,
        requester_id=current_user.id,
        department=pr.department if hasattr(pr, 'department') else None,
        required_date=pr.required_date if hasattr(pr, 'required_date') else None,
        notes=pr.notes if hasattr(pr, 'notes') else None,
        status=models.PRStatus.DRAFT
    )
    db.add(new_pr)
    await db.flush()

    for item in pr.items:
        line = models.PRLine(
            tenant_id=current_user.tenant_id,
            pr_id=new_pr.id,
            product_id=item.product_id,
            quantity=item.quantity,
            estimated_price=item.estimated_price if hasattr(item, 'estimated_price') else 0.0
        )
        db.add(line)
        
        # Deduct stock from InventoryBatch (FIFO - oldest batches first)
        remaining_qty = item.quantity
        batch_result = await db.execute(
            select(InventoryBatch).where(
                InventoryBatch.product_id == item.product_id,
                InventoryBatch.tenant_id == current_user.tenant_id,
                InventoryBatch.quantity_on_hand > 0
            ).order_by(InventoryBatch.id)  # FIFO order
        )
        batches = batch_result.scalars().all()
        
        for batch in batches:
            if remaining_qty <= 0:
                break
            deduct = min(batch.quantity_on_hand, remaining_qty)
            batch.quantity_on_hand -= deduct
            remaining_qty -= deduct
    
    await db.commit()
    await db.refresh(new_pr)
    return new_pr

@router.post("/pr/{pr_id}/approve")
async def approve_pr(
    pr_id: uuid.UUID, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    pr = await db.get(models.PurchaseRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    
    # Get the requester (creator of the PR)
    requester = await db.get(models.User, pr.requester_id)
    if not requester:
        raise HTTPException(status_code=404, detail="PR requester not found")
    
    # Check approval rules - but ADMIN can always approve
    approver_role = current_user.role.value
    requester_role = requester.role.value
    
    if approver_role != "ADMIN":
        # Check if there's an approval rule allowing this approver to approve this requester
        from models.models_approval import ApprovalRule
        rule_query = select(ApprovalRule).where(
            ApprovalRule.tenant_id == current_user.tenant_id,
            ApprovalRule.requester_role == requester_role,
            ApprovalRule.approver_role == approver_role
        )
        rule_result = await db.execute(rule_query)
        rule = rule_result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=403, 
                detail=f"Your role ({approver_role}) is not authorized to approve requests from {requester_role}"
            )
    
    # Cannot approve own request (unless ADMIN)
    if pr.requester_id == current_user.id and approver_role != "ADMIN":
        raise HTTPException(status_code=403, detail="You cannot approve your own request")
    
    pr.status = models.PRStatus.APPROVED
    pr.approved_by = current_user.id
    pr.approved_at = datetime.now()
    await db.commit()
    return {"status": "Approved", "approved_by": str(current_user.id), "approved_at": pr.approved_at.isoformat()}

@router.post("/pr/{pr_id}/reject")
async def reject_pr(
    pr_id: uuid.UUID,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    pr = await db.get(models.PurchaseRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    
    reason = payload.get("reason", "")
    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required")
    
    pr.status = models.PRStatus.REJECTED
    pr.rejected_by = current_user.id
    pr.rejected_at = datetime.now()
    pr.reject_reason = reason
    await db.commit()
    return {
        "status": "Rejected", 
        "rejected_by": str(current_user.id), 
        "rejected_at": pr.rejected_at.isoformat(),
        "reason": reason
    }

# PO Endpoints
@router.post("/po/create_from_pr", response_model=schemas.POResponse)
async def convert_pr_to_po(
    payload: schemas.POCreateFromPR, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
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

    # 2. Generate PO number
    count_result = await db.execute(
        select(func.count(models_procurement.PurchaseOrder.id)).where(
            models_procurement.PurchaseOrder.tenant_id == current_user.tenant_id
        )
    )
    count = count_result.scalar() or 0
    po_number = f"PO-{count + 1:05d}"

    # 3. Create PO
    new_po = models_procurement.PurchaseOrder(
        tenant_id=current_user.tenant_id,
        po_number=po_number,
        vendor_id=payload.vendor_id,
        pr_id=pr.id,
        status=models_procurement.POStatus.DRAFT
    )
    db.add(new_po)
    await db.flush()

    # 4. Copy items
    for item in pr.items:
        price = payload.price_map.get(str(item.product_id), 0.0)
        po_line = models_procurement.POLine(
            tenant_id=current_user.tenant_id,
            po_id=new_po.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=price
        )
        db.add(po_line)
    
    # 5. Update PR status
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

@router.get("/orders")
async def list_pos(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(models_procurement.PurchaseOrder).where(
        models_procurement.PurchaseOrder.tenant_id == current_user.tenant_id
    ).options(
        selectinload(models_procurement.PurchaseOrder.vendor),
        selectinload(models_procurement.PurchaseOrder.items).selectinload(models_procurement.POLine.product)
    ).order_by(models_procurement.PurchaseOrder.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/orders/{order_id}/pdf")
async def download_po_pdf(
    order_id: str,
    db: AsyncSession = Depends(database.get_db)
):
    """Generate and download PO as PDF"""
    # Get PO with vendor and items
    query = select(models_procurement.PurchaseOrder)\
        .where(models_procurement.PurchaseOrder.id == order_id)\
        .options(
            selectinload(models_procurement.PurchaseOrder.vendor),
            selectinload(models_procurement.PurchaseOrder.items).selectinload(models_procurement.POLine.product)
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
    payload: Optional[dict] = Body(default=None),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Send PO to vendor - changes status from Draft to Open"""
    try:
        result = await db.execute(
            select(models_procurement.PurchaseOrder).where(
                models_procurement.PurchaseOrder.id == order_id
            )
        )
        po = result.scalar_one_or_none()
        if not po:
            raise HTTPException(status_code=404, detail="PO not found")
        
        if po.status != models_procurement.POStatus.DRAFT:
            raise HTTPException(status_code=400, detail=f"PO must be in Draft status, current status: {po.status}")
        
        po.status = models_procurement.POStatus.OPEN
        # Save notes if provided
        if payload and payload.get('notes'):
            po.notes = payload.get('notes')
        await db.commit()
        return {"message": "PO sent to vendor", "status": "Open"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending PO: {str(e)}")


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


# ============ RFQ ENDPOINTS ============

@router.get("/rfqs")
async def list_rfqs(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all RFQs"""
    from models.models_procurement import RequestForQuotation, RFQLine, RFQVendor
    
    query = select(RequestForQuotation).where(
        RequestForQuotation.tenant_id == current_user.tenant_id
    ).order_by(RequestForQuotation.created_at.desc())
    
    result = await db.execute(query)
    rfqs = result.scalars().all()
    
    return [
        {
            "id": str(r.id),
            "rfq_number": r.rfq_number,
            "deadline": r.deadline.isoformat() if r.deadline else None,
            "status": r.status,
            "notes": r.notes,
            "items_count": 0,  # Will be populated if needed
            "vendors_count": 0
        }
        for r in rfqs
    ]


@router.post("/rfqs")
async def create_rfq(
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new RFQ"""
    from models.models_procurement import RequestForQuotation, RFQLine, RFQVendor
    
    # Generate RFQ number
    count_result = await db.execute(
        select(func.count(RequestForQuotation.id)).where(
            RequestForQuotation.tenant_id == current_user.tenant_id
        )
    )
    count = count_result.scalar() or 0
    rfq_number = f"RFQ-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    
    rfq = RequestForQuotation(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        rfq_number=rfq_number,
        pr_id=payload.get("pr_id") or None,
        deadline=datetime.fromisoformat(payload["deadline"]) if payload.get("deadline") else None,
        status="Draft",
        notes=payload.get("notes")
    )
    db.add(rfq)
    await db.flush()
    
    # Add items
    for item in payload.get("items", []):
        line = RFQLine(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            rfq_id=rfq.id,
            product_id=item.get("product_id"),
            quantity=item.get("quantity", 1),
            specifications=item.get("specifications")
        )
        db.add(line)
    
    # Add vendors
    for vendor_id in payload.get("vendor_ids", []):
        rfq_vendor = RFQVendor(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            rfq_id=rfq.id,
            vendor_id=vendor_id
        )
        db.add(rfq_vendor)
    
    await db.commit()
    return {"message": "RFQ created", "rfq_number": rfq_number, "id": str(rfq.id)}


@router.put("/rfqs/{rfq_id}/send")
async def send_rfq(
    rfq_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Send RFQ to vendors"""
    from models.models_procurement import RequestForQuotation
    
    result = await db.execute(select(RequestForQuotation).where(RequestForQuotation.id == rfq_id))
    rfq = result.scalar_one_or_none()
    
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    rfq.status = "Sent"
    await db.commit()
    return {"message": "RFQ sent to vendors", "status": "Sent"}


# ============ VENDOR BILL ENDPOINTS ============

@router.get("/bills")
async def list_bills(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all vendor bills"""
    from models.models_procurement import VendorBill
    
    query = select(VendorBill).where(
        VendorBill.tenant_id == current_user.tenant_id
    ).options(
        selectinload(VendorBill.vendor)
    ).order_by(VendorBill.bill_date.desc())
    
    result = await db.execute(query)
    bills = result.scalars().all()
    
    return [
        {
            "id": str(b.id),
            "bill_number": b.bill_number,
            "vendor_invoice": b.vendor_invoice,
            "vendor_id": str(b.vendor_id),
            "vendor_name": b.vendor.name if b.vendor else "Unknown",
            "bill_date": b.bill_date.isoformat() if b.bill_date else None,
            "due_date": b.due_date.isoformat() if b.due_date else None,
            "status": b.status,
            "total_amount": b.total_amount,
            "amount_paid": b.amount_paid,
            "balance_due": b.balance_due
        }
        for b in bills
    ]


@router.post("/bills")
async def create_bill(
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a vendor bill"""
    from models.models_procurement import VendorBill, VendorBillLine
    
    # Generate bill number
    count_result = await db.execute(
        select(func.count(VendorBill.id)).where(
            VendorBill.tenant_id == current_user.tenant_id
        )
    )
    count = count_result.scalar() or 0
    bill_number = f"BILL-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    
    bill = VendorBill(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        bill_number=bill_number,
        vendor_invoice=payload.get("vendor_invoice"),
        vendor_id=payload.get("vendor_id"),
        po_id=payload.get("po_id") or None,
        grn_id=payload.get("grn_id") or None,
        bill_date=datetime.fromisoformat(payload["bill_date"]) if payload.get("bill_date") else datetime.utcnow(),
        due_date=datetime.fromisoformat(payload["due_date"]) if payload.get("due_date") else None,
        status="Pending",
        total_amount=payload.get("total_amount", 0),
        balance_due=payload.get("balance_due", payload.get("total_amount", 0)),
        notes=payload.get("notes")
    )
    db.add(bill)
    await db.flush()
    
    # Add line items
    for item in payload.get("items", []):
        line = VendorBillLine(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            bill_id=bill.id,
            product_id=item.get("product_id") or None,
            description=item.get("description"),
            quantity=item.get("quantity", 1),
            unit_price=item.get("unit_price", 0),
            line_total=item.get("quantity", 1) * item.get("unit_price", 0)
        )
        db.add(line)
    
    await db.commit()
    return {"message": "Bill created", "bill_number": bill_number, "id": str(bill.id)}


@router.put("/bills/{bill_id}/approve")
async def approve_bill(
    bill_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Approve a vendor bill"""
    from models.models_procurement import VendorBill
    
    result = await db.execute(select(VendorBill).where(VendorBill.id == bill_id))
    bill = result.scalar_one_or_none()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    bill.status = "Approved"
    bill.approved_by = current_user.id
    bill.approved_at = datetime.utcnow()
    await db.commit()
    return {"message": "Bill approved"}


@router.post("/bills/{bill_id}/payments")
async def record_bill_payment(
    bill_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record a payment for a vendor bill"""
    from models.models_procurement import VendorBill, VendorPayment
    
    result = await db.execute(select(VendorBill).where(VendorBill.id == bill_id))
    bill = result.scalar_one_or_none()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    amount = payload.get("amount", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    
    if amount > bill.balance_due:
        raise HTTPException(status_code=400, detail=f"Amount exceeds balance due ({bill.balance_due})")
    
    # Create payment record
    payment = VendorPayment(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        bill_id=bill.id,
        payment_date=datetime.utcnow(),
        amount=amount,
        payment_method=payload.get("payment_method", "Bank Transfer"),
        reference=payload.get("reference"),
        notes=payload.get("notes"),
        paid_by=current_user.id
    )
    db.add(payment)
    
    # Update bill
    bill.amount_paid = (bill.amount_paid or 0) + amount
    bill.balance_due = (bill.total_amount or 0) - bill.amount_paid
    
    if bill.balance_due <= 0:
        bill.status = "Paid"
    else:
        bill.status = "Partial Paid"
    
    await db.commit()
    return {"message": "Payment recorded", "new_balance": bill.balance_due}


# ============ PAYMENTS LISTING ============

@router.get("/payments")
async def list_payments(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all vendor payments"""
    from models.models_procurement import VendorPayment, VendorBill
    
    query = select(VendorPayment, VendorBill).join(
        VendorBill, VendorPayment.bill_id == VendorBill.id
    ).where(
        VendorPayment.tenant_id == current_user.tenant_id
    ).order_by(VendorPayment.payment_date.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    payments = []
    for payment, bill in rows:
        # Get vendor name
        vendor = await db.get(models.Vendor, bill.vendor_id) if bill.vendor_id else None
        payments.append({
            "id": str(payment.id),
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "bill_id": str(payment.bill_id),
            "bill_number": bill.bill_number,
            "vendor_id": str(bill.vendor_id) if bill.vendor_id else None,
            "vendor_name": vendor.name if vendor else "Unknown",
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "reference": payment.reference,
            "notes": payment.notes
        })
    
    return payments


# ============ ANALYTICS ============

@router.get("/analytics/summary")
async def procurement_analytics_summary(
    period: str = "this_month",
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get procurement analytics summary"""
    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "this_month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0)
    elif period == "3_months":
        start_date = (now.replace(day=1) - timedelta(days=60)).replace(day=1)
    else:  # this_year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0)
    
    # Get total purchases
    po_result = await db.execute(
        select(func.sum(models_procurement.PurchaseOrder.total_amount)).where(
            models_procurement.PurchaseOrder.tenant_id == current_user.tenant_id,
            models_procurement.PurchaseOrder.created_at >= start_date
        )
    )
    total_purchases = po_result.scalar() or 0
    
    # Get order count
    order_count_result = await db.execute(
        select(func.count(models_procurement.PurchaseOrder.id)).where(
            models_procurement.PurchaseOrder.tenant_id == current_user.tenant_id,
            models_procurement.PurchaseOrder.created_at >= start_date
        )
    )
    total_orders = order_count_result.scalar() or 0
    
    # Get active vendors
    vendor_result = await db.execute(
        select(func.count(func.distinct(models_procurement.PurchaseOrder.vendor_id))).where(
            models_procurement.PurchaseOrder.tenant_id == current_user.tenant_id,
            models_procurement.PurchaseOrder.created_at >= start_date
        )
    )
    active_vendors = vendor_result.scalar() or 0
    
    return {
        "total_purchases": total_purchases,
        "total_orders": total_orders,
        "active_vendors": active_vendors,
        "avg_lead_time": 7,  # Mock for now
        "growth_percent": 0  # Would need previous period data
    }


# ============ SUPPLIER ITEMS ============

@router.post("/supplier-items")
async def create_supplier_item(
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Link a product to a vendor with pricing"""
    from models.models_procurement import SupplierItem
    
    supplier_item = SupplierItem(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        vendor_id=payload.get("vendor_id"),
        product_id=payload.get("product_id"),
        agreed_price=payload.get("agreed_price", 0),
        lead_time_days=payload.get("lead_time_days", 7),
        min_order_qty=payload.get("min_order_qty", 1),
        is_preferred=payload.get("is_preferred", False)
    )
    db.add(supplier_item)
    
    try:
        await db.commit()
        return {"message": "Supplier item linked"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


from datetime import timedelta
