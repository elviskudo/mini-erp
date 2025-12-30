"""
Maintenance Module Router
API endpoints for assets, work orders, schedules, and maintenance management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, date
from uuid import UUID
import uuid

import database, models
from auth import get_current_user
from models.models_maintenance import (
    Asset, MaintenanceType, MaintenanceWorkOrder, MaintenanceWorkOrderTask, 
    MaintenanceWorkOrderPart, MaintenanceWorkOrderCost, MaintenanceSchedule
)
from schemas.schemas_maintenance import (
    AssetCreate, AssetUpdate, AssetResponse,
    MaintenanceTypeCreate, MaintenanceTypeResponse,
    WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse,
    WorkOrderTaskCreate, WorkOrderTaskResponse,
    WorkOrderPartCreate, WorkOrderPartResponse,
    WorkOrderCostCreate, WorkOrderCostResponse,
    MaintenanceScheduleCreate, MaintenanceScheduleUpdate, MaintenanceScheduleResponse,
    MaintenanceStats
)

router = APIRouter(
    prefix="/maintenance",
    tags=["maintenance"]
)


# ==================== STATS ====================

@router.get("/stats", response_model=MaintenanceStats)
async def get_maintenance_stats(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get maintenance dashboard statistics"""
    tenant_id = current_user.tenant_id
    
    # Asset counts
    total_assets = await db.scalar(select(func.count()).select_from(Asset).where(Asset.tenant_id == tenant_id))
    operational = await db.scalar(select(func.count()).select_from(Asset).where(and_(Asset.tenant_id == tenant_id, Asset.status == 'OPERATIONAL')))
    under_maint = await db.scalar(select(func.count()).select_from(Asset).where(and_(Asset.tenant_id == tenant_id, Asset.status == 'UNDER_MAINTENANCE')))
    broken = await db.scalar(select(func.count()).select_from(Asset).where(and_(Asset.tenant_id == tenant_id, Asset.status == 'BROKEN')))
    
    # Work order counts
    total_wo = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrder).where(MaintenanceWorkOrder.tenant_id == tenant_id))
    pending_wo = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrder).where(and_(MaintenanceWorkOrder.tenant_id == tenant_id, MaintenanceWorkOrder.status.in_(['DRAFT', 'SCHEDULED']))))
    in_progress = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrder).where(and_(MaintenanceWorkOrder.tenant_id == tenant_id, MaintenanceWorkOrder.status == 'IN_PROGRESS')))
    
    # Completed this month
    first_of_month = date.today().replace(day=1)
    completed_month = await db.scalar(
        select(func.count()).select_from(MaintenanceWorkOrder).where(
            and_(MaintenanceWorkOrder.tenant_id == tenant_id, MaintenanceWorkOrder.status == 'COMPLETED', MaintenanceWorkOrder.completed_at >= first_of_month)
        )
    )
    
    # Schedule counts
    overdue = await db.scalar(
        select(func.count()).select_from(MaintenanceSchedule).where(
            and_(MaintenanceSchedule.tenant_id == tenant_id, MaintenanceSchedule.is_active == True, MaintenanceSchedule.next_due < date.today())
        )
    )
    upcoming = await db.scalar(
        select(func.count()).select_from(MaintenanceSchedule).where(
            and_(MaintenanceSchedule.tenant_id == tenant_id, MaintenanceSchedule.is_active == True, MaintenanceSchedule.next_due >= date.today())
        )
    )
    
    # Costs this month
    costs_result = await db.execute(
        select(func.sum(MaintenanceWorkOrderCost.amount)).join(MaintenanceWorkOrder).where(
            and_(MaintenanceWorkOrder.tenant_id == tenant_id, MaintenanceWorkOrderCost.date >= first_of_month)
        )
    )
    total_costs = costs_result.scalar() or 0
    
    return MaintenanceStats(
        total_assets=total_assets or 0,
        operational_assets=operational or 0,
        under_maintenance=under_maint or 0,
        broken_assets=broken or 0,
        total_work_orders=total_wo or 0,
        pending_work_orders=pending_wo or 0,
        in_progress_work_orders=in_progress or 0,
        completed_this_month=completed_month or 0,
        overdue_schedules=overdue or 0,
        upcoming_schedules=upcoming or 0,
        total_costs_this_month=total_costs
    )


# ==================== ASSETS ====================

@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all assets"""
    result = await db.execute(
        select(Asset).where(Asset.tenant_id == current_user.tenant_id).order_by(Asset.code)
    )
    assets = result.scalars().all()
    
    response = []
    for a in assets:
        wo_count = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrder).where(MaintenanceWorkOrder.asset_id == a.id))
        pending = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrder).where(and_(MaintenanceWorkOrder.asset_id == a.id, MaintenanceWorkOrder.status.in_(['DRAFT', 'SCHEDULED', 'IN_PROGRESS']))))
        response.append(AssetResponse(
            id=a.id, code=a.code, name=a.name, category=a.category, location=a.location, status=a.status,
            purchase_date=a.purchase_date, purchase_cost=a.purchase_cost, serial_number=a.serial_number,
            manufacturer=a.manufacturer, model=a.model, warranty_expiry=a.warranty_expiry,
            notes=a.notes, image_url=a.image_url, created_at=a.created_at, updated_at=a.updated_at,
            work_order_count=wo_count or 0, pending_work_orders=pending or 0
        ))
    return response


@router.post("/assets", response_model=AssetResponse)
async def create_asset(
    asset: AssetCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new asset"""
    db_asset = Asset(tenant_id=current_user.tenant_id, **asset.model_dump())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset


@router.get("/assets/{id}", response_model=AssetResponse)
async def get_asset(
    id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get asset by ID"""
    result = await db.execute(select(Asset).where(and_(Asset.id == id, Asset.tenant_id == current_user.tenant_id)))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/assets/{id}", response_model=AssetResponse)
async def update_asset(
    id: UUID,
    asset_update: AssetUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an asset"""
    result = await db.execute(select(Asset).where(and_(Asset.id == id, Asset.tenant_id == current_user.tenant_id)))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    for key, value in asset_update.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    
    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/assets/{id}")
async def delete_asset(
    id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an asset"""
    result = await db.execute(select(Asset).where(and_(Asset.id == id, Asset.tenant_id == current_user.tenant_id)))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(asset)
    await db.commit()
    return {"message": "Asset deleted"}


# ==================== MAINTENANCE TYPES ====================

@router.get("/types", response_model=List[MaintenanceTypeResponse])
async def list_maintenance_types(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List maintenance types"""
    result = await db.execute(select(MaintenanceType).where(MaintenanceType.tenant_id == current_user.tenant_id))
    return result.scalars().all()


@router.post("/types", response_model=MaintenanceTypeResponse)
async def create_maintenance_type(
    mtype: MaintenanceTypeCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create maintenance type"""
    db_type = MaintenanceType(tenant_id=current_user.tenant_id, **mtype.model_dump())
    db.add(db_type)
    await db.commit()
    await db.refresh(db_type)
    return db_type


# ==================== WORK ORDERS ====================

@router.get("/work-orders", response_model=List[WorkOrderResponse])
async def list_work_orders(
    status: str = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all work orders"""
    query = select(MaintenanceWorkOrder).where(MaintenanceWorkOrder.tenant_id == current_user.tenant_id)
    if status:
        query = query.where(MaintenanceWorkOrder.status == status)
    query = query.order_by(MaintenanceWorkOrder.created_at.desc())
    
    result = await db.execute(query)
    work_orders = result.scalars().all()
    
    response = []
    for wo in work_orders:
        # Get related data
        asset_result = await db.execute(select(Asset).where(Asset.id == wo.asset_id))
        asset = asset_result.scalar_one_or_none()
        
        assigned_name = None
        if wo.assigned_to:
            user_result = await db.execute(select(models.User).where(models.User.id == wo.assigned_to))
            user = user_result.scalar_one_or_none()
            assigned_name = user.username if user else None
        
        # Get costs
        costs_result = await db.execute(select(func.sum(MaintenanceWorkOrderCost.amount)).where(MaintenanceWorkOrderCost.work_order_id == wo.id))
        total_cost = costs_result.scalar() or 0
        
        # Get task counts
        task_count = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrderTask).where(MaintenanceWorkOrderTask.work_order_id == wo.id))
        completed_tasks = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrderTask).where(and_(MaintenanceWorkOrderTask.work_order_id == wo.id, MaintenanceWorkOrderTask.is_completed == True)))
        
        response.append(WorkOrderResponse(
            id=wo.id, code=wo.code, asset_id=wo.asset_id, type_id=wo.type_id,
            title=wo.title, description=wo.description, priority=wo.priority, status=wo.status,
            scheduled_date=wo.scheduled_date, started_at=wo.started_at, completed_at=wo.completed_at,
            assigned_to=wo.assigned_to, reported_by=wo.reported_by, notes=wo.notes,
            created_at=wo.created_at, updated_at=wo.updated_at,
            asset_name=asset.name if asset else None, asset_code=asset.code if asset else None,
            assigned_name=assigned_name, total_cost=total_cost, task_count=task_count or 0, completed_tasks=completed_tasks or 0
        ))
    return response


@router.post("/work-orders", response_model=WorkOrderResponse)
async def create_work_order(
    wo: WorkOrderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new work order"""
    # Generate code
    today = date.today()
    count = await db.scalar(select(func.count()).select_from(MaintenanceWorkOrder).where(MaintenanceWorkOrder.tenant_id == current_user.tenant_id))
    code = f"WO-{today.year}-{(count or 0) + 1:04d}"
    
    db_wo = MaintenanceWorkOrder(
        tenant_id=current_user.tenant_id,
        code=code,
        reported_by=current_user.id,
        **wo.model_dump()
    )
    db.add(db_wo)
    await db.commit()
    await db.refresh(db_wo)
    
    return WorkOrderResponse(
        id=db_wo.id, code=db_wo.code, asset_id=db_wo.asset_id, type_id=db_wo.type_id,
        title=db_wo.title, description=db_wo.description, priority=db_wo.priority, status=db_wo.status,
        scheduled_date=db_wo.scheduled_date, assigned_to=db_wo.assigned_to, notes=db_wo.notes,
        created_at=db_wo.created_at
    )


@router.get("/work-orders/{id}", response_model=WorkOrderResponse)
async def get_work_order(
    id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get work order by ID"""
    result = await db.execute(select(MaintenanceWorkOrder).where(and_(MaintenanceWorkOrder.id == id, MaintenanceWorkOrder.tenant_id == current_user.tenant_id)))
    wo = result.scalar_one_or_none()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return wo


@router.put("/work-orders/{id}", response_model=WorkOrderResponse)
async def update_work_order(
    id: UUID,
    wo_update: WorkOrderUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a work order"""
    result = await db.execute(select(MaintenanceWorkOrder).where(and_(MaintenanceWorkOrder.id == id, MaintenanceWorkOrder.tenant_id == current_user.tenant_id)))
    wo = result.scalar_one_or_none()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    update_data = wo_update.model_dump(exclude_unset=True)
    
    # Handle status transitions
    new_status = update_data.get('status')
    if new_status == 'IN_PROGRESS' and not wo.started_at:
        wo.started_at = datetime.utcnow()
        # Update asset status
        asset_result = await db.execute(select(Asset).where(Asset.id == wo.asset_id))
        asset = asset_result.scalar_one_or_none()
        if asset:
            asset.status = 'UNDER_MAINTENANCE'
    elif new_status == 'COMPLETED' and not wo.completed_at:
        wo.completed_at = datetime.utcnow()
        # Update asset status back to operational
        asset_result = await db.execute(select(Asset).where(Asset.id == wo.asset_id))
        asset = asset_result.scalar_one_or_none()
        if asset:
            asset.status = 'OPERATIONAL'
    
    for key, value in update_data.items():
        setattr(wo, key, value)
    
    await db.commit()
    await db.refresh(wo)
    return wo


@router.delete("/work-orders/{id}")
async def delete_work_order(
    id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a work order"""
    result = await db.execute(select(MaintenanceWorkOrder).where(and_(MaintenanceWorkOrder.id == id, MaintenanceWorkOrder.tenant_id == current_user.tenant_id)))
    wo = result.scalar_one_or_none()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    await db.delete(wo)
    await db.commit()
    return {"message": "Work order deleted"}


# ==================== WORK ORDER TASKS ====================

@router.get("/work-orders/{wo_id}/tasks", response_model=List[WorkOrderTaskResponse])
async def list_work_order_tasks(
    wo_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List tasks for a work order"""
    result = await db.execute(select(MaintenanceWorkOrderTask).where(MaintenanceWorkOrderTask.work_order_id == wo_id))
    return result.scalars().all()


@router.post("/work-orders/{wo_id}/tasks", response_model=WorkOrderTaskResponse)
async def add_work_order_task(
    wo_id: UUID,
    task: WorkOrderTaskCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add task to work order"""
    db_task = MaintenanceWorkOrderTask(work_order_id=wo_id, **task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.put("/work-orders/{wo_id}/tasks/{task_id}/complete")
async def complete_work_order_task(
    wo_id: UUID,
    task_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark task as complete"""
    result = await db.execute(select(MaintenanceWorkOrderTask).where(MaintenanceWorkOrderTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_completed = True
    task.completed_at = datetime.utcnow()
    task.completed_by = current_user.id
    await db.commit()
    return {"message": "Task completed"}


# ==================== WORK ORDER PARTS ====================

@router.get("/work-orders/{wo_id}/parts", response_model=List[WorkOrderPartResponse])
async def list_work_order_parts(
    wo_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List spare parts for a work order"""
    result = await db.execute(select(MaintenanceWorkOrderPart).where(MaintenanceWorkOrderPart.work_order_id == wo_id))
    return result.scalars().all()


@router.post("/work-orders/{wo_id}/parts", response_model=WorkOrderPartResponse)
async def add_work_order_part(
    wo_id: UUID,
    part: WorkOrderPartCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add spare part to work order"""
    total_cost = (part.quantity or 1) * (part.unit_cost or 0)
    db_part = MaintenanceWorkOrderPart(work_order_id=wo_id, total_cost=total_cost, **part.model_dump())
    db.add(db_part)
    await db.commit()
    await db.refresh(db_part)
    return db_part


# ==================== WORK ORDER COSTS ====================

@router.get("/work-orders/{wo_id}/costs", response_model=List[WorkOrderCostResponse])
async def list_work_order_costs(
    wo_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List costs for a work order"""
    result = await db.execute(select(MaintenanceWorkOrderCost).where(MaintenanceWorkOrderCost.work_order_id == wo_id))
    return result.scalars().all()


@router.post("/work-orders/{wo_id}/costs", response_model=WorkOrderCostResponse)
async def add_work_order_cost(
    wo_id: UUID,
    cost: WorkOrderCostCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add cost to work order"""
    db_cost = MaintenanceWorkOrderCost(work_order_id=wo_id, **cost.model_dump())
    db.add(db_cost)
    await db.commit()
    await db.refresh(db_cost)
    return db_cost


# ==================== MAINTENANCE SCHEDULES ====================

@router.get("/schedules", response_model=List[MaintenanceScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List maintenance schedules"""
    result = await db.execute(
        select(MaintenanceSchedule).where(MaintenanceSchedule.tenant_id == current_user.tenant_id).order_by(MaintenanceSchedule.next_due)
    )
    schedules = result.scalars().all()
    
    response = []
    for s in schedules:
        asset_result = await db.execute(select(Asset).where(Asset.id == s.asset_id))
        asset = asset_result.scalar_one_or_none()
        response.append(MaintenanceScheduleResponse(
            id=s.id, asset_id=s.asset_id, type_id=s.type_id, title=s.title, description=s.description,
            frequency=s.frequency, interval_days=s.interval_days, next_due=s.next_due, is_active=s.is_active,
            last_performed=s.last_performed, created_at=s.created_at,
            asset_name=asset.name if asset else None, asset_code=asset.code if asset else None
        ))
    return response


@router.post("/schedules", response_model=MaintenanceScheduleResponse)
async def create_schedule(
    schedule: MaintenanceScheduleCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create maintenance schedule"""
    db_schedule = MaintenanceSchedule(tenant_id=current_user.tenant_id, **schedule.model_dump())
    db.add(db_schedule)
    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule


@router.put("/schedules/{id}", response_model=MaintenanceScheduleResponse)
async def update_schedule(
    id: UUID,
    schedule_update: MaintenanceScheduleUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update maintenance schedule"""
    result = await db.execute(select(MaintenanceSchedule).where(and_(MaintenanceSchedule.id == id, MaintenanceSchedule.tenant_id == current_user.tenant_id)))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    for key, value in schedule_update.model_dump(exclude_unset=True).items():
        setattr(schedule, key, value)
    
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/schedules/{id}")
async def delete_schedule(
    id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete maintenance schedule"""
    result = await db.execute(select(MaintenanceSchedule).where(and_(MaintenanceSchedule.id == id, MaintenanceSchedule.tenant_id == current_user.tenant_id)))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
    await db.commit()
    return {"message": "Schedule deleted"}
