from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List
import uuid
import database
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

# Warehouse Endpoints
@router.post("/warehouses", response_model=schemas.WarehouseResponse)
async def create_warehouse(
    warehouse: schemas.WarehouseCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    data = warehouse.dict()
    data['tenant_id'] = current_user.tenant_id  # Set tenant_id from current user
    new_wh = models.Warehouse(**data)
    db.add(new_wh)
    try:
        await db.commit()
        # Re-fetch with selectinload to properly load locations for response
        result = await db.execute(
            select(models.Warehouse)
            .options(selectinload(models.Warehouse.locations))
            .where(models.Warehouse.id == new_wh.id)
        )
        return result.scalar_one()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/warehouses", response_model=List[schemas.WarehouseResponse])
async def read_warehouses(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    query = select(models.Warehouse)\
        .options(selectinload(models.Warehouse.locations))\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

# Location Endpoints
@router.post("/warehouses/{warehouse_id}/locations", response_model=schemas.LocationResponse)
async def create_location(warehouse_id: uuid.UUID, location: schemas.LocationCreate, db: AsyncSession = Depends(database.get_db)):
    new_loc = models.Location(
        warehouse_id=warehouse_id,
        **location.dict()
    )
    db.add(new_loc)
    try:
        await db.commit()
        await db.refresh(new_loc)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_loc

@router.get("/stock")
async def list_stock(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Return all inventory batches with qty > 0 for current tenant.
    Includes product, location, and warehouse information.
    
    Expiration date is set when:
    - Goods Receipt: from PO line or manual entry
    - Production Transfer: can be set based on product shelf life
    """
    query = select(models.InventoryBatch)\
        .where(
            models.InventoryBatch.tenant_id == current_user.tenant_id,
            models.InventoryBatch.quantity_on_hand > 0
        )\
        .options(
            selectinload(models.InventoryBatch.product),
            selectinload(models.InventoryBatch.location).selectinload(models.Location.warehouse)
        )
    result = await db.execute(query)
    batches = result.scalars().all()
    
    # Transform to include warehouse name
    return [
        {
            "id": str(b.id),
            "product": {
                "id": str(b.product.id) if b.product else None,
                "name": b.product.name if b.product else "Unknown",
                "code": b.product.code if b.product else "",
                "image_url": b.product.image_url if b.product else None
            },
            "batch_number": b.batch_number,
            "quantity_on_hand": b.quantity_on_hand,
            "expiration_date": b.expiration_date.isoformat() if b.expiration_date else None,
            "location": {
                "id": str(b.location.id) if b.location else None,
                "name": b.location.name if b.location else "Unknown",
                "code": b.location.code if b.location else ""
            },
            "warehouse": {
                "id": str(b.location.warehouse.id) if b.location and b.location.warehouse else None,
                "name": b.location.warehouse.name if b.location and b.location.warehouse else "Unknown"
            },
            "origin_type": b.origin_type.value if b.origin_type else "UNKNOWN",
            "unit_cost": b.unit_cost or 0,
            "qr_code_data": b.qr_code_data
        }
        for b in batches
    ]


@router.put("/stock/{batch_id}/set-expiry")
async def set_batch_expiry(
    batch_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Set or update expiration date for an inventory batch"""
    from datetime import datetime
    
    result = await db.execute(
        select(models.InventoryBatch)
        .where(
            models.InventoryBatch.id == batch_id,
            models.InventoryBatch.tenant_id == current_user.tenant_id
        )
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    expiry_date_str = payload.get('expiration_date')
    if expiry_date_str:
        batch.expiration_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
    else:
        batch.expiration_date = None
    
    await db.commit()
    
    return {
        "message": "Expiration date updated",
        "batch_id": str(batch.id),
        "expiration_date": batch.expiration_date.isoformat() if batch.expiration_date else None
    }


@router.put("/stock/{batch_id}/move-location")
async def move_batch_location(
    batch_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Move batch to a new location within a warehouse"""
    result = await db.execute(
        select(models.InventoryBatch)
        .where(
            models.InventoryBatch.id == batch_id,
            models.InventoryBatch.tenant_id == current_user.tenant_id
        )
        .options(selectinload(models.InventoryBatch.location))
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    new_location_id = payload.get('location_id')
    if not new_location_id:
        raise HTTPException(status_code=400, detail="location_id is required")
    
    # Verify the new location exists and belongs to same tenant
    loc_result = await db.execute(
        select(models.Location)
        .where(
            models.Location.id == new_location_id,
            models.Location.tenant_id == current_user.tenant_id
        )
        .options(selectinload(models.Location.warehouse))
    )
    new_location = loc_result.scalar_one_or_none()
    
    if not new_location:
        raise HTTPException(status_code=404, detail="Target location not found")
    
    old_location_name = batch.location.name if batch.location else "Unknown"
    old_location_id = batch.location_id
    
    # Update batch location
    batch.location_id = new_location_id
    
    # Create transfer movement record
    from models import models_ledger
    import uuid as uuid_lib
    
    movement = models_ledger.StockMovement(
        id=uuid_lib.uuid4(),
        tenant_id=current_user.tenant_id,
        product_id=batch.product_id,
        batch_id=batch.id,
        location_id=new_location_id,
        quantity_change=batch.quantity_on_hand,  # Positive = transfer IN to new location
        movement_type=models_ledger.MovementType.TRANSFER,
        reference_id=f"MOVE:{str(batch.id)[:8]}",
        created_by=current_user.id,
        notes=f"Transferred from {old_location_name} to {new_location.name}"
    )
    db.add(movement)
    
    await db.commit()
    
    return {
        "message": f"Moved from {old_location_name} to {new_location.name}",
        "batch_id": str(batch.id),
        "new_location": new_location.name,
        "warehouse": new_location.warehouse.name if new_location.warehouse else "Unknown"
    }


@router.get("/locations-for-move")
async def get_locations_for_move(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all locations for the move dropdown"""
    result = await db.execute(
        select(models.Location)
        .where(models.Location.tenant_id == current_user.tenant_id)
        .options(selectinload(models.Location.warehouse))
    )
    locations = result.scalars().all()
    
    return [
        {
            "id": str(loc.id),
            "name": loc.name,
            "code": loc.code,
            "warehouse": loc.warehouse.name if loc.warehouse else "Unknown"
        }
        for loc in locations
    ]


@router.get("/movements")
async def list_movements(
    movement_type: str = None,
    warehouse_id: str = None,
    date_from: str = None,
    date_to: str = None,
    user_id: str = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get stock movements history with filters"""
    from models import models_ledger
    from datetime import datetime
    
    # Build query with filters
    query = select(models_ledger.StockMovement)\
        .where(models_ledger.StockMovement.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if movement_type:
        try:
            mt = models_ledger.MovementType(movement_type)
            query = query.where(models_ledger.StockMovement.movement_type == mt)
        except ValueError:
            # Try matching by name (INBOUND, OUTBOUND, etc)
            mt_map = {e.value: e for e in models_ledger.MovementType}
            if movement_type in mt_map:
                query = query.where(models_ledger.StockMovement.movement_type == mt_map[movement_type])
    
    if warehouse_id:
        # Join with location to filter by warehouse
        query = query.join(models.Location, models_ledger.StockMovement.location_id == models.Location.id)\
            .where(models.Location.warehouse_id == warehouse_id)
    
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.where(models_ledger.StockMovement.timestamp >= dt_from)
        except:
            pass
    
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.where(models_ledger.StockMovement.timestamp <= dt_to)
        except:
            pass
    
    if user_id:
        query = query.where(models_ledger.StockMovement.created_by == user_id)
    
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply sorting
    sort_column = getattr(models_ledger.StockMovement, sort_by, models_ledger.StockMovement.timestamp)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Add eager loading
    query = query.options(
        selectinload(models_ledger.StockMovement.product),
        selectinload(models_ledger.StockMovement.location).selectinload(models.Location.warehouse),
        selectinload(models_ledger.StockMovement.user)
    )
    
    result = await db.execute(query)
    movements = result.scalars().all()
    
    # Calculate stats from all data (without pagination)
    stats_query = select(models_ledger.StockMovement)\
        .where(models_ledger.StockMovement.tenant_id == current_user.tenant_id)
    stats_result = await db.execute(stats_query)
    all_movements = stats_result.scalars().all()
    
    inbound = sum(1 for m in all_movements if m.movement_type and m.movement_type.value == 'Inbound')
    outbound = sum(1 for m in all_movements if m.movement_type and m.movement_type.value == 'Outbound')
    transfer = sum(1 for m in all_movements if m.movement_type and m.movement_type.value == 'Transfer')
    adjustment = sum(1 for m in all_movements if m.movement_type and m.movement_type.value == 'Adjustment')
    
    return {
        "movements": [
            {
                "id": str(m.id),
                "reference": m.reference_id or f"MOV-{str(m.id)[:8]}",
                "type": m.movement_type.value if m.movement_type else "Unknown",
                "item": m.product.name if m.product else "Unknown",
                "quantity": m.quantity_change,
                "warehouse": m.location.warehouse.name if m.location and hasattr(m.location, 'warehouse') and m.location.warehouse else "Unknown",
                "location": m.location.name if m.location else "Unknown",
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "user": m.user.username if m.user else "System",
                "notes": m.notes
            }
            for m in movements
        ],
        "stats": {
            "inbound": inbound,
            "outbound": outbound,
            "transfer": transfer,
            "adjustment": adjustment
        },
        "total": total,
        "limit": limit,
        "offset": offset
    }


# Storage Zone Endpoints
@router.post("/storage-zones", response_model=schemas.StorageZoneResponse)
async def create_storage_zone(
    zone: schemas.StorageZoneCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_zone = models.StorageZone(
        tenant_id=current_user.tenant_id,
        **zone.dict()
    )
    db.add(new_zone)
    try:
        await db.commit()
        await db.refresh(new_zone)
        return new_zone
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/storage-zones", response_model=List[schemas.StorageZoneResponse])
async def read_storage_zones(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(models.StorageZone)\
        .where(models.StorageZone.tenant_id == current_user.tenant_id)\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/storage-zones/{zone_id}", response_model=schemas.StorageZoneResponse)
async def read_storage_zone(
    zone_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.StorageZone).where(models.StorageZone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Storage zone not found")
    return zone


@router.put("/storage-zones/{zone_id}", response_model=schemas.StorageZoneResponse)
async def update_storage_zone(
    zone_id: str,
    zone_update: schemas.StorageZoneUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.StorageZone).where(models.StorageZone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Storage zone not found")
    
    update_data = zone_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(zone, key, value)
    
    try:
        await db.commit()
        await db.refresh(zone)
        return zone
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/storage-zones/{zone_id}")
async def delete_storage_zone(
    zone_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.StorageZone).where(models.StorageZone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Storage zone not found")
    
    await db.delete(zone)
    await db.commit()
    return {"message": "Storage zone deleted"}


# ============ OVERHEAD REPORTING ============

@router.get("/overhead/summary")
async def get_overhead_summary(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get overall overhead cost summary across all storage zones"""
    from sqlalchemy import func
    
    # Get all storage zones for tenant
    query = select(models.StorageZone).where(
        models.StorageZone.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    zones = result.scalars().all()
    
    # Calculate totals
    total_energy_kwh = sum(z.daily_kwh_usage or 0 for z in zones) * 30  # Monthly estimate
    total_energy_cost = sum(z.monthly_energy_cost or 0 for z in zones)
    
    # Group by zone type
    by_zone_type = {}
    for z in zones:
        zone_type = z.zone_type.value if hasattr(z.zone_type, 'value') else str(z.zone_type)
        if zone_type not in by_zone_type:
            by_zone_type[zone_type] = {
                "count": 0,
                "total_kwh": 0,
                "total_cost": 0,
                "capacity_used": 0
            }
        by_zone_type[zone_type]["count"] += 1
        by_zone_type[zone_type]["total_kwh"] += (z.daily_kwh_usage or 0) * 30
        by_zone_type[zone_type]["total_cost"] += z.monthly_energy_cost or 0
        by_zone_type[zone_type]["capacity_used"] += z.used_units or 0
    
    # Calculate average cost per unit storage
    total_capacity = sum(z.capacity_units or 0 for z in zones)
    total_used = sum(z.used_units or 0 for z in zones)
    cost_per_unit = round(total_energy_cost / total_used, 2) if total_used > 0 else 0
    
    return {
        "total_zones": len(zones),
        "total_monthly_kwh": round(total_energy_kwh, 2),
        "total_monthly_cost": round(total_energy_cost, 2),
        "total_capacity": total_capacity,
        "total_used": total_used,
        "utilization_percent": round((total_used / total_capacity * 100) if total_capacity > 0 else 0, 1),
        "cost_per_unit_stored": cost_per_unit,
        "by_zone_type": [
            {
                "zone_type": zone_type,
                "count": data["count"],
                "monthly_kwh": round(data["total_kwh"], 2),
                "monthly_cost": round(data["total_cost"], 2),
                "capacity_used": data["capacity_used"]
            }
            for zone_type, data in by_zone_type.items()
        ]
    }


@router.get("/overhead/zones")
async def get_zone_energy_report(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed energy report per storage zone"""
    query = select(models.StorageZone).where(
        models.StorageZone.tenant_id == current_user.tenant_id
    ).options(selectinload(models.StorageZone.warehouse))
    result = await db.execute(query)
    zones = result.scalars().all()
    
    report = []
    for z in zones:
        daily_cost = (z.daily_kwh_usage or 0) * (z.electricity_tariff or 0)
        monthly_estimated = daily_cost * 30
        
        # Efficiency rating based on type
        efficiency = "Good"
        if z.zone_type and z.zone_type.value in ["CHILLER", "FROZEN"]:
            if z.current_temp and z.max_temp:
                if z.current_temp > z.max_temp:
                    efficiency = "Over Temp - Check"
                elif z.current_temp > (z.max_temp - 2):
                    efficiency = "Near Limit"
        
        report.append({
            "id": str(z.id),
            "zone_name": z.zone_name,
            "zone_type": z.zone_type.value if hasattr(z.zone_type, 'value') else str(z.zone_type),
            "warehouse": z.warehouse.name if z.warehouse else "N/A",
            "daily_kwh": z.daily_kwh_usage or 0,
            "tariff_per_kwh": z.electricity_tariff or 0,
            "daily_cost": round(daily_cost, 2),
            "monthly_cost": round(z.monthly_energy_cost or monthly_estimated, 2),
            "capacity_units": z.capacity_units or 0,
            "used_units": z.used_units or 0,
            "utilization": round((z.used_units / z.capacity_units * 100) if z.capacity_units else 0, 1),
            "current_temp": z.current_temp,
            "temp_range": f"{z.min_temp}°C - {z.max_temp}°C" if z.min_temp and z.max_temp else "N/A",
            "efficiency": efficiency
        })
    
    return {"zones": report}


@router.post("/overhead/log-energy/{zone_id}")
async def log_zone_energy(
    zone_id: str,
    payload: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Log daily energy usage for a storage zone and recalculate monthly cost"""
    result = await db.execute(
        select(models.StorageZone).where(models.StorageZone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Storage zone not found")
    
    daily_kwh = payload.get("daily_kwh", 0)
    current_temp = payload.get("current_temp")
    
    # Update zone energy data
    zone.daily_kwh_usage = daily_kwh
    if current_temp is not None:
        zone.current_temp = current_temp
    
    # Recalculate monthly cost (assuming 30 days)
    zone.monthly_energy_cost = daily_kwh * (zone.electricity_tariff or 0) * 30
    
    await db.commit()
    await db.refresh(zone)
    
    return {
        "message": "Energy logged successfully",
        "zone_name": zone.zone_name,
        "daily_kwh": zone.daily_kwh_usage,
        "monthly_cost": zone.monthly_energy_cost,
        "current_temp": zone.current_temp
    }


@router.get("/overhead/allocation")
async def get_overhead_allocation(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get overhead cost allocation for production cost calculation"""
    query = select(models.StorageZone).where(
        models.StorageZone.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    zones = result.scalars().all()
    
    # Calculate total overhead
    total_monthly_overhead = sum(z.monthly_energy_cost or 0 for z in zones)
    total_units_stored = sum(z.used_units or 0 for z in zones)
    
    # Allocation methods
    per_unit_allocation = round(total_monthly_overhead / total_units_stored, 2) if total_units_stored > 0 else 0
    
    # By zone type for cold chain premium
    zone_type_costs = {}
    for z in zones:
        zone_type = z.zone_type.value if hasattr(z.zone_type, 'value') else str(z.zone_type)
        if zone_type not in zone_type_costs:
            zone_type_costs[zone_type] = {"cost": 0, "units": 0}
        zone_type_costs[zone_type]["cost"] += z.monthly_energy_cost or 0
        zone_type_costs[zone_type]["units"] += z.used_units or 0
    
    allocation_rates = {}
    for zone_type, data in zone_type_costs.items():
        rate = round(data["cost"] / data["units"], 2) if data["units"] > 0 else 0
        allocation_rates[zone_type] = {
            "monthly_cost": round(data["cost"], 2),
            "units_stored": data["units"],
            "rate_per_unit": rate
        }
    
    return {
        "total_monthly_overhead": round(total_monthly_overhead, 2),
        "total_units_stored": total_units_stored,
        "simple_per_unit_rate": per_unit_allocation,
        "by_zone_type": allocation_rates,
        "recommendation": "Use zone-specific rates for accurate product costing, especially for cold chain products."
    }
