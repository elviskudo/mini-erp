from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime
import database
import models
from models import models_opname
import schemas
from schemas import schemas_opname
from services.inventory_ledger import record_movement
from auth import get_current_user

router = APIRouter(
    prefix="/opname",
    tags=["Stock Opname"]
)

# ============ SCHEDULE ENDPOINTS ============

@router.post("/schedule", response_model=schemas_opname.ScheduleResponse)
async def create_schedule(
    request: schemas_opname.ScheduleCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new opname schedule"""
    schedule = models_opname.OpnameSchedule(
        tenant_id=current_user.tenant_id,
        warehouse_id=request.warehouse_id,
        name=request.name,
        description=request.description,
        frequency=models_opname.OpnameFrequency(request.frequency) if request.frequency else models_opname.OpnameFrequency.MONTHLY,
        scheduled_date=request.scheduled_date,
        start_time=request.start_time,
        estimated_duration_hours=request.estimated_duration_hours,
        count_all_items=request.count_all_items,
        category_filter=request.category_filter,
        location_filter=request.location_filter,
        created_by=current_user.id
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.get("/schedules", response_model=List[schemas_opname.ScheduleResponse])
async def list_schedules(
    active_only: bool = True,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all opname schedules"""
    query = select(models_opname.OpnameSchedule).where(
        models_opname.OpnameSchedule.tenant_id == current_user.tenant_id
    ).options(
        selectinload(models_opname.OpnameSchedule.warehouse),
        selectinload(models_opname.OpnameSchedule.assignments).selectinload(models_opname.OpnameAssignment.user)
    ).order_by(models_opname.OpnameSchedule.scheduled_date.desc())
    
    if active_only:
        query = query.where(models_opname.OpnameSchedule.is_active == True)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/assign-team")
async def assign_team(
    request: schemas_opname.AssignmentCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Assign a team member to a schedule"""
    assignment = models_opname.OpnameAssignment(
        tenant_id=current_user.tenant_id,
        schedule_id=request.schedule_id,
        user_id=request.user_id,
        role=request.role,
        assigned_locations=request.assigned_locations
    )
    db.add(assignment)
    await db.commit()
    return {"status": "Assigned", "id": str(assignment.id)}


# ============ OPNAME CRUD ============

@router.post("/create", response_model=schemas_opname.OpnameResponse)
async def create_opname(
    request: schemas_opname.OpnameCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new stock opname and snapshot current stock"""
    # Generate opname number
    today = datetime.now().strftime("%Y%m%d")
    count_query = select(func.count(models_opname.StockOpname.id)).where(
        models_opname.StockOpname.tenant_id == current_user.tenant_id,
        func.date(models_opname.StockOpname.created_at) == func.date(datetime.now())
    )
    result = await db.execute(count_query)
    count = result.scalar() or 0
    opname_number = f"OPN-{today}-{str(count + 1).zfill(3)}"
    
    # Create opname header
    new_opname = models_opname.StockOpname(
        warehouse_id=request.warehouse_id,
        schedule_id=request.schedule_id,
        opname_number=opname_number,
        status=models_opname.OpnameStatus.SCHEDULED,
        notes=request.notes,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(new_opname)
    await db.flush()

    # Snapshot current stock in this warehouse
    query = select(models.InventoryBatch)\
        .join(models.InventoryBatch.location)\
        .where(
            models.Location.warehouse_id == request.warehouse_id,
            models.InventoryBatch.quantity_on_hand > 0
        )
    result = await db.execute(query)
    batches = result.scalars().all()

    total_items = 0
    total_system_value = 0
    
    for batch in batches:
        # Get product cost
        product = await db.get(models.Product, batch.product_id)
        unit_cost = product.standard_cost if product and product.standard_cost else 0
        system_value = batch.quantity_on_hand * unit_cost
        
        detail = models_opname.StockOpnameDetail(
            opname_id=new_opname.id,
            product_id=batch.product_id,
            batch_id=batch.id,
            location_id=batch.location_id,
            system_qty=batch.quantity_on_hand,
            counted_qty=None,
            unit_cost=unit_cost,
            system_value=system_value,
            tenant_id=current_user.tenant_id
        )
        db.add(detail)
        total_items += 1
        total_system_value += system_value
    
    new_opname.total_items = total_items
    new_opname.total_system_value = total_system_value

    await db.commit()
    await db.refresh(new_opname)
    return new_opname


@router.post("/start-counting")
async def start_counting(
    request: schemas_opname.OpnameStartCounting,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Start the counting process for an opname"""
    opname = await db.get(models_opname.StockOpname, request.opname_id)
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    if opname.status not in [models_opname.OpnameStatus.SCHEDULED]:
        raise HTTPException(status_code=400, detail=f"Cannot start counting. Current status: {opname.status}")
    
    opname.status = models_opname.OpnameStatus.IN_PROGRESS
    opname.counting_started_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "Counting started", "opname_id": str(opname.id)}


@router.post("/update-count")
async def update_count(
    request: schemas_opname.OpnameBulkCount,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update counted quantities for multiple items"""
    opname = await db.get(models_opname.StockOpname, request.opname_id)
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    
    # Update opname status to IN_PROGRESS if still SCHEDULED
    if opname.status == models_opname.OpnameStatus.SCHEDULED:
        opname.status = models_opname.OpnameStatus.IN_PROGRESS
        opname.counting_started_at = datetime.utcnow()
    
    counted = 0
    variance_count = 0
    total_counted_value = 0
    total_variance_value = 0
    
    for item in request.items:
        detail = await db.get(models_opname.StockOpnameDetail, item.detail_id)
        if detail and detail.opname_id == request.opname_id:
            detail.counted_qty = item.counted_qty
            detail.variance = item.counted_qty - detail.system_qty
            detail.counted_value = item.counted_qty * detail.unit_cost
            detail.variance_value = detail.variance * detail.unit_cost
            detail.counted_at = datetime.utcnow()
            detail.counted_by = current_user.id
            
            if item.variance_reason:
                try:
                    detail.variance_reason = models_opname.VarianceReason(item.variance_reason)
                except:
                    detail.variance_reason = models_opname.VarianceReason.OTHER
            detail.variance_notes = item.variance_notes
            
            counted += 1
            total_counted_value += detail.counted_value
            if detail.variance != 0:
                variance_count += 1
                total_variance_value += detail.variance_value
    
    # Update opname totals
    opname.counted_items = counted
    opname.items_with_variance = variance_count
    opname.total_counted_value = total_counted_value
    opname.total_variance_value = total_variance_value
    
    await db.commit()
    return {"status": "Updated", "count": counted, "variance_items": variance_count}


@router.post("/complete-counting")
async def complete_counting(
    opname_id: uuid.UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark counting as complete, ready for review"""
    opname = await db.get(models_opname.StockOpname, opname_id)
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    
    opname.status = models_opname.OpnameStatus.COUNTING_DONE
    opname.counting_completed_at = datetime.utcnow()
    
    # Calculate final totals
    query = select(models_opname.StockOpnameDetail).where(
        models_opname.StockOpnameDetail.opname_id == opname_id
    )
    result = await db.execute(query)
    details = result.scalars().all()
    
    opname.counted_items = sum(1 for d in details if d.counted_qty is not None)
    opname.items_with_variance = sum(1 for d in details if d.variance != 0)
    opname.total_counted_value = sum(d.counted_value or 0 for d in details)
    opname.total_variance_value = sum(d.variance_value or 0 for d in details)
    
    await db.commit()
    return {"status": "Counting complete", "ready_for_review": True}


@router.post("/review")
async def review_opname(
    request: schemas_opname.OpnameReview,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Review opname and mark as reviewed"""
    opname = await db.get(models_opname.StockOpname, request.opname_id)
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    
    if opname.status != models_opname.OpnameStatus.COUNTING_DONE:
        raise HTTPException(status_code=400, detail="Opname must be in COUNTING_DONE status to review")
    
    opname.status = models_opname.OpnameStatus.REVIEWED
    opname.reviewed_at = datetime.utcnow()
    opname.reviewed_by = current_user.id
    if request.notes:
        opname.notes = (opname.notes or "") + f"\n[Review] {request.notes}"
    
    await db.commit()
    return {"status": "Reviewed", "ready_for_approval": True}


@router.post("/approve")
async def approve_opname(
    request: schemas_opname.OpnameApproval,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Approve or reject opname for posting"""
    opname = await db.get(models_opname.StockOpname, request.opname_id)
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    
    if opname.status != models_opname.OpnameStatus.REVIEWED:
        raise HTTPException(status_code=400, detail="Opname must be REVIEWED before approval")
    
    if request.approved:
        opname.status = models_opname.OpnameStatus.APPROVED
        opname.approved_at = datetime.utcnow()
        opname.approved_by = current_user.id
        return {"status": "Approved", "ready_for_posting": True}
    else:
        opname.status = models_opname.OpnameStatus.COUNTING_DONE  # Send back for recount
        opname.notes = (opname.notes or "") + f"\n[Rejected] {request.rejection_reason}"
        await db.commit()
        return {"status": "Rejected", "reason": request.rejection_reason}


@router.post("/post")
async def post_opname(
    payload: schemas_opname.OpnamePostRequest, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Post opname adjustments to inventory"""
    query = select(models_opname.StockOpname)\
        .where(models_opname.StockOpname.id == payload.opname_id)\
        .options(selectinload(models_opname.StockOpname.details))
    result = await db.execute(query)
    opname = result.scalar_one_or_none()

    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    if opname.status not in [models_opname.OpnameStatus.APPROVED, models_opname.OpnameStatus.REVIEWED]:
        raise HTTPException(status_code=400, detail=f"Cannot post. Status must be APPROVED or REVIEWED. Current: {opname.status}")

    adjustments_made = 0
    for detail in opname.details:
        if detail.counted_qty is None:
            continue
        
        diff = detail.counted_qty - detail.system_qty
        
        if diff != 0:
            batch = await db.get(models.InventoryBatch, detail.batch_id)
            if batch:
                batch.quantity_on_hand = detail.counted_qty
                
                await record_movement(
                    db,
                    product_id=detail.product_id,
                    location_id=batch.location_id,
                    quantity_change=diff,
                    movement_type=models.MovementType.ADJUSTMENT,
                    batch_id=batch.id,
                    reference_id=str(opname.id),
                    notes=f"Stock Opname Adjustment - {detail.variance_reason.value if detail.variance_reason else 'Adjustment'}",
                    tenant_id=current_user.tenant_id
                )
                adjustments_made += 1

    opname.status = models_opname.OpnameStatus.POSTED
    opname.posted_at = datetime.utcnow()
    opname.posted_by = current_user.id
    
    await db.commit()
    return {"status": "Posted", "adjustments_made": adjustments_made}


# ============ LIST & GET ============

@router.get("/list", response_model=List[schemas_opname.OpnameResponse])
async def list_opnames(
    status: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all opnames"""
    query = select(models_opname.StockOpname).where(
        models_opname.StockOpname.tenant_id == current_user.tenant_id
    ).options(
        selectinload(models_opname.StockOpname.warehouse),
        selectinload(models_opname.StockOpname.details).selectinload(models_opname.StockOpnameDetail.product)
    ).order_by(models_opname.StockOpname.date.desc())
    
    if status:
        try:
            status_enum = models_opname.OpnameStatus(status)
            query = query.where(models_opname.StockOpname.status == status_enum)
        except:
            pass
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{opname_id}", response_model=schemas_opname.OpnameResponse)
async def get_opname(
    opname_id: uuid.UUID, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get opname details"""
    query = select(models_opname.StockOpname)\
        .where(
            models_opname.StockOpname.id == opname_id,
            models_opname.StockOpname.tenant_id == current_user.tenant_id
        )\
        .options(
            selectinload(models_opname.StockOpname.warehouse), 
            selectinload(models_opname.StockOpname.details).selectinload(models_opname.StockOpnameDetail.product),
            selectinload(models_opname.StockOpname.details).selectinload(models_opname.StockOpnameDetail.location)
        )
    result = await db.execute(query)
    opname = result.scalar_one_or_none()
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    return opname


# ============ REPORTS ============

@router.get("/variance-report/{opname_id}", response_model=schemas_opname.VarianceReport)
async def get_variance_report(
    opname_id: uuid.UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get variance report for an opname"""
    query = select(models_opname.StockOpname)\
        .where(models_opname.StockOpname.id == opname_id)\
        .options(
            selectinload(models_opname.StockOpname.warehouse),
            selectinload(models_opname.StockOpname.details).selectinload(models_opname.StockOpnameDetail.product),
            selectinload(models_opname.StockOpname.details).selectinload(models_opname.StockOpnameDetail.location)
        )
    result = await db.execute(query)
    opname = result.scalar_one_or_none()
    
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    
    variance_items = []
    for d in opname.details:
        if d.variance != 0:
            variance_items.append({
                "product_name": d.product.name if d.product else "Unknown",
                "product_code": d.product.code if d.product else None,
                "location": d.location.name if d.location else None,
                "system_qty": d.system_qty,
                "counted_qty": d.counted_qty or 0,
                "variance": d.variance,
                "variance_reason": d.variance_reason.value if d.variance_reason else None,
                "variance_value": d.variance_value
            })
    
    return {
        "opname_id": opname.id,
        "opname_number": opname.opname_number,
        "warehouse_name": opname.warehouse.name if opname.warehouse else "-",
        "date": opname.date,
        "status": opname.status.value if hasattr(opname.status, 'value') else str(opname.status),
        "total_items": opname.total_items,
        "items_with_variance": opname.items_with_variance,
        "total_variance_value": opname.total_variance_value,
        "variance_items": variance_items
    }


@router.get("/evaluation/stats", response_model=schemas_opname.EvaluationStats)
async def get_evaluation_stats(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get evaluation statistics for opnames"""
    # Total opnames
    total_query = select(func.count(models_opname.StockOpname.id)).where(
        models_opname.StockOpname.tenant_id == current_user.tenant_id
    )
    total = (await db.execute(total_query)).scalar() or 0
    
    # Completed opnames
    completed_query = select(func.count(models_opname.StockOpname.id)).where(
        models_opname.StockOpname.tenant_id == current_user.tenant_id,
        models_opname.StockOpname.status == models_opname.OpnameStatus.POSTED
    )
    completed = (await db.execute(completed_query)).scalar() or 0
    
    # Total variance
    variance_query = select(func.sum(models_opname.StockOpname.total_variance_value)).where(
        models_opname.StockOpname.tenant_id == current_user.tenant_id,
        models_opname.StockOpname.status == models_opname.OpnameStatus.POSTED
    )
    total_variance = (await db.execute(variance_query)).scalar() or 0
    
    avg_variance = total_variance / completed if completed > 0 else 0
    
    # Common variance reasons
    reason_query = select(
        models_opname.StockOpnameDetail.variance_reason,
        func.count(models_opname.StockOpnameDetail.id)
    ).where(
        models_opname.StockOpnameDetail.tenant_id == current_user.tenant_id,
        models_opname.StockOpnameDetail.variance_reason != None
    ).group_by(models_opname.StockOpnameDetail.variance_reason)
    
    reasons = (await db.execute(reason_query)).all()
    common_reasons = [{"reason": r.value if r else "Unknown", "count": c} for r, c in reasons]
    
    return {
        "total_opnames": total,
        "completed_opnames": completed,
        "total_variance_value": total_variance,
        "avg_variance_per_opname": avg_variance,
        "common_variance_reasons": common_reasons,
        "monthly_trend": []  # TODO: Implement monthly trend
    }


# ============ PRINT SHEET ============

@router.get("/print-list/{warehouse_id}")
async def get_print_list(
    warehouse_id: uuid.UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate a printable count sheet for a warehouse"""
    # Get warehouse
    warehouse = await db.get(models.Warehouse, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get all batches with stock
    query = select(models.InventoryBatch)\
        .join(models.InventoryBatch.location)\
        .join(models.InventoryBatch.product)\
        .where(
            models.Location.warehouse_id == warehouse_id,
            models.InventoryBatch.quantity_on_hand > 0
        )\
        .options(
            selectinload(models.InventoryBatch.product),
            selectinload(models.InventoryBatch.location)
        )
    result = await db.execute(query)
    batches = result.scalars().all()
    
    items = []
    for batch in batches:
        items.append({
            "product_code": batch.product.code if batch.product else "-",
            "product_name": batch.product.name if batch.product else "Unknown",
            "location": batch.location.name if batch.location else "-",
            "system_qty": batch.quantity_on_hand,
            "uom": batch.product.uom if batch.product else "-",
            "barcode": batch.product.code if batch.product else None
        })
    
    return {
        "warehouse_name": warehouse.name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "items": items
    }
