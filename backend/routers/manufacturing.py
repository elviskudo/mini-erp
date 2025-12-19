from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
import database, models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/manufacturing",
    tags=["Manufacturing"]
)

# Work Center Endpoints
@router.post("/work-centers", response_model=schemas.WorkCenterResponse)
async def create_work_center(
    wc: schemas.WorkCenterCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    data = wc.dict()
    data['tenant_id'] = current_user.tenant_id  # Set tenant_id from current user
    new_wc = models.WorkCenter(**data)
    db.add(new_wc)
    try:
        await db.commit()
        await db.refresh(new_wc)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_wc

@router.get("/work-centers", response_model=List[schemas.WorkCenterResponse])
async def read_work_centers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.WorkCenter).offset(skip).limit(limit))
    return result.scalars().all()

@router.put("/work-centers/{wc_id}", response_model=schemas.WorkCenterResponse)
async def update_work_center(
    wc_id: str,
    wc: schemas.WorkCenterCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(select(models.WorkCenter).where(models.WorkCenter.id == wc_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Work center not found")
    
    # Update fields
    for key, value in wc.dict().items():
        setattr(existing, key, value)
    
    try:
        await db.commit()
        await db.refresh(existing)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return existing

@router.delete("/work-centers/{wc_id}")
async def delete_work_center(
    wc_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(select(models.WorkCenter).where(models.WorkCenter.id == wc_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Work center not found")
    
    await db.delete(existing)
    await db.commit()
    return {"message": "Work center deleted"}

# Product Endpoints
@router.post("/products", response_model=schemas.ProductResponse)
async def create_product(
    product: schemas.ProductCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    data = product.dict()
    data['tenant_id'] = current_user.tenant_id
    new_product = models.Product(**data)
    db.add(new_product)
    try:
        await db.commit()
        await db.refresh(new_product)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_product

@router.get("/products", response_model=List[schemas.ProductResponse])
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Product).offset(skip).limit(limit))
    return result.scalars().all()

@router.put("/products/{product_id}", response_model=schemas.ProductResponse)
async def update_product(
    product_id: str,
    product: schemas.ProductCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product.dict().items():
        setattr(existing, key, value)
    
    try:
        await db.commit()
        await db.refresh(existing)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return existing

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(existing)
    await db.commit()
    return {"message": "Product deleted"}

# BOM Endpoints
@router.post("/boms", response_model=schemas.BOMResponse)
async def create_bom(bom: schemas.BOMCreate, db: AsyncSession = Depends(database.get_db)):
    # Create Header
    new_bom = models.BillOfMaterial(
        product_id=bom.product_id,
        version=bom.version,
        is_active=bom.is_active
    )
    db.add(new_bom)
    await db.flush() # Get ID

    # Create Items
    for item in bom.items:
        new_item = models.BOMItem(
            bom_id=new_bom.id,
            component_id=item.component_id,
            quantity=item.quantity,
            waste_percentage=item.waste_percentage
        )
        db.add(new_item)
    
    try:
        await db.commit()
        # Reload with relationships
        query = select(models.BillOfMaterial)\
            .where(models.BillOfMaterial.id == new_bom.id)\
            .options(selectinload(models.BillOfMaterial.product), selectinload(models.BillOfMaterial.items).selectinload(models.BOMItem.component))
        result = await db.execute(query)
        final_bom = result.scalar_one()
        return final_bom
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/boms", response_model=List[schemas.BOMResponse])
async def read_boms(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    query = select(models.BillOfMaterial)\
        .options(selectinload(models.BillOfMaterial.product), selectinload(models.BillOfMaterial.items).selectinload(models.BOMItem.component))\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# Production Order Endpoints
@router.post("/production-orders", response_model=schemas.ProductionOrderResponse)
async def create_production_order(
    order: schemas.ProductionOrderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate order number
    count_result = await db.execute(select(models.ProductionOrder).where(models.ProductionOrder.tenant_id == current_user.tenant_id))
    count = len(count_result.scalars().all())
    order_no = f"PO-{str(count + 1).zfill(4)}"
    
    # Create production order
    new_order = models.ProductionOrder(
        tenant_id=current_user.tenant_id,
        order_no=order_no,
        quantity=order.quantity,
        notes=order.notes
    )
    if order.scheduled_date:
        from datetime import datetime
        new_order.scheduled_date = datetime.fromisoformat(order.scheduled_date)
    
    db.add(new_order)
    await db.flush()
    
    # Add products
    for product_id in order.product_ids:
        prod_item = models.ProductionOrderProduct(
            production_order_id=new_order.id,
            product_id=product_id
        )
        db.add(prod_item)
    
    # Add work centers
    for wc_id in order.work_center_ids:
        wc_item = models.ProductionOrderWorkCenter(
            production_order_id=new_order.id,
            work_center_id=wc_id
        )
        db.add(wc_item)
    
    try:
        await db.commit()
        # Reload with relationships
        query = select(models.ProductionOrder)\
            .where(models.ProductionOrder.id == new_order.id)\
            .options(
                selectinload(models.ProductionOrder.products).selectinload(models.ProductionOrderProduct.product),
                selectinload(models.ProductionOrder.work_centers).selectinload(models.ProductionOrderWorkCenter.work_center)
            )
        result = await db.execute(query)
        return result.scalar_one()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/production-orders", response_model=List[schemas.ProductionOrderResponse])
async def read_production_orders(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(models.ProductionOrder)\
        .where(models.ProductionOrder.tenant_id == current_user.tenant_id)\
        .options(
            selectinload(models.ProductionOrder.products).selectinload(models.ProductionOrderProduct.product),
            selectinload(models.ProductionOrder.work_centers).selectinload(models.ProductionOrderWorkCenter.work_center)
        )\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/production-orders/{order_id}/status")
async def update_production_order_status(
    order_id: str,
    status: str,
    progress: int = 0,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(select(models.ProductionOrder).where(models.ProductionOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    order.status = status
    order.progress = progress
    await db.commit()
    return {"message": "Status updated"}


@router.put("/production-orders/{order_id}", response_model=schemas.ProductionOrderResponse)
async def update_production_order(
    order_id: str,
    order_update: schemas.ProductionOrderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Find existing order
    result = await db.execute(select(models.ProductionOrder).where(models.ProductionOrder.id == order_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    # Update basic fields
    existing.quantity = order_update.quantity
    existing.notes = order_update.notes
    if order_update.scheduled_date:
        from datetime import datetime
        existing.scheduled_date = datetime.fromisoformat(order_update.scheduled_date)
    
    # Delete existing products and work centers
    await db.execute(
        models.ProductionOrderProduct.__table__.delete().where(
            models.ProductionOrderProduct.production_order_id == order_id
        )
    )
    await db.execute(
        models.ProductionOrderWorkCenter.__table__.delete().where(
            models.ProductionOrderWorkCenter.production_order_id == order_id
        )
    )
    
    # Add new products
    for product_id in order_update.product_ids:
        prod_item = models.ProductionOrderProduct(
            production_order_id=existing.id,
            product_id=product_id
        )
        db.add(prod_item)
    
    # Add new work centers
    for wc_id in order_update.work_center_ids:
        wc_item = models.ProductionOrderWorkCenter(
            production_order_id=existing.id,
            work_center_id=wc_id
        )
        db.add(wc_item)
    
    try:
        await db.commit()
        # Reload with relationships
        query = select(models.ProductionOrder)\
            .where(models.ProductionOrder.id == existing.id)\
            .options(
                selectinload(models.ProductionOrder.products).selectinload(models.ProductionOrderProduct.product),
                selectinload(models.ProductionOrder.work_centers).selectinload(models.ProductionOrderWorkCenter.work_center)
            )
        result = await db.execute(query)
        return result.scalar_one()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# HPP (Cost of Goods Manufactured) Endpoints
@router.post("/production-orders/{order_id}/calculate-hpp")
async def calculate_order_hpp(
    order_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate HPP for a production order"""
    from services.hpp_service import update_order_hpp
    
    labor_hours = payload.get('labor_hours', 0)
    hourly_rate = payload.get('hourly_rate', 0)
    overhead_rate = payload.get('overhead_rate', 0.15)
    
    result = await update_order_hpp(db, order_id, labor_hours, hourly_rate, overhead_rate)
    return result


@router.get("/production-orders/{order_id}/cost-breakdown")
async def get_cost_breakdown(
    order_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed cost breakdown for a production order"""
    from services.hpp_service import get_production_cost_breakdown
    return await get_production_cost_breakdown(db, order_id)


@router.post("/production-orders/{order_id}/record-progress")
async def record_production_progress(
    order_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record production progress (completed qty, good/defect/scrap)"""
    from datetime import datetime
    
    result = await db.execute(
        select(models.ProductionOrder).where(models.ProductionOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    completed_qty = payload.get('completed_qty', 0)
    
    # Update order progress
    order.completed_qty = (order.completed_qty or 0) + completed_qty
    
    # Calculate progress percentage
    if order.quantity > 0:
        order.progress = min(100, int((order.completed_qty / order.quantity) * 100))
    
    # Auto-complete if 100%
    if order.progress >= 100:
        order.status = models.ProductionOrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
    elif order.progress > 0 and order.status == models.ProductionOrderStatus.DRAFT:
        order.status = models.ProductionOrderStatus.IN_PROGRESS
        order.started_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Progress recorded",
        "completed_qty": order.completed_qty,
        "progress": order.progress,
        "status": order.status.value if hasattr(order.status, 'value') else str(order.status)
    }


# QC Recording Endpoints
@router.post("/production-orders/{order_id}/record-qc")
async def record_qc_result(
    order_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record QC result for a production order (Good/Defect/Scrap)"""
    from datetime import datetime
    
    # Get production order
    result = await db.execute(
        select(models.ProductionOrder)
        .where(models.ProductionOrder.id == order_id)
        .options(selectinload(models.ProductionOrder.products))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    # Get product_id (use first product if multiple)
    product_id = None
    if order.products and len(order.products) > 0:
        product_id = order.products[0].product_id
    
    # Create QC Result
    qc_result = models.ProductionQCResult(
        tenant_id=current_user.tenant_id,
        production_order_id=order_id,
        product_id=product_id,
        inspector_id=current_user.id,
        good_qty=payload.get('good_qty', 0),
        defect_qty=payload.get('defect_qty', 0),
        scrap_qty=payload.get('scrap_qty', 0),
        scrap_type=payload.get('scrap_type'),
        scrap_reason=payload.get('scrap_reason'),
        salvage_value=payload.get('salvage_value', 0),
        spoilage_expense=payload.get('spoilage_expense', 0),
        rework_cost=payload.get('rework_cost', 0),
        notes=payload.get('notes')
    )
    
    db.add(qc_result)
    
    # Update order completed_qty with good qty only
    order.completed_qty = (order.completed_qty or 0) + payload.get('good_qty', 0)
    if order.quantity > 0:
        order.progress = min(100, int((order.completed_qty / order.quantity) * 100))
    
    await db.commit()
    
    return {
        "message": "QC result recorded",
        "good_qty": qc_result.good_qty,
        "defect_qty": qc_result.defect_qty,
        "scrap_qty": qc_result.scrap_qty,
        "order_progress": order.progress
    }


@router.get("/production-orders/{order_id}/qc-results")
async def get_qc_results(
    order_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all QC results for a production order"""
    query = select(models.ProductionQCResult)\
        .where(models.ProductionQCResult.production_order_id == order_id)\
        .order_by(models.ProductionQCResult.recorded_at.desc())
    
    result = await db.execute(query)
    qc_results = result.scalars().all()
    
    # Calculate totals
    total_good = sum(r.good_qty or 0 for r in qc_results)
    total_defect = sum(r.defect_qty or 0 for r in qc_results)
    total_scrap = sum(r.scrap_qty or 0 for r in qc_results)
    total_spoilage = sum(r.spoilage_expense or 0 for r in qc_results)
    
    return {
        "results": [
            {
                "id": str(r.id),
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
                "good_qty": r.good_qty,
                "defect_qty": r.defect_qty,
                "scrap_qty": r.scrap_qty,
                "scrap_type": r.scrap_type.value if r.scrap_type and hasattr(r.scrap_type, 'value') else r.scrap_type,
                "scrap_reason": r.scrap_reason,
                "spoilage_expense": r.spoilage_expense,
                "notes": r.notes
            }
            for r in qc_results
        ],
        "totals": {
            "good": total_good,
            "defect": total_defect,
            "scrap": total_scrap,
            "total_produced": total_good + total_defect + total_scrap,
            "defect_rate": round((total_defect / (total_good + total_defect + total_scrap)) * 100, 2) if (total_good + total_defect + total_scrap) > 0 else 0,
            "spoilage_expense": total_spoilage
        }
    }
