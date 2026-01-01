"""
Fleet Management Router
API endpoints for vehicles, bookings, fuel logs, maintenance, expenses, and reminders
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date, datetime, timedelta
from uuid import UUID
import qrcode
import io
import base64

import database
import models
from auth import get_current_user
from schemas.schemas_fleet import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    BookingCreate, BookingUpdate, BookingResponse, BookingStatus,
    FuelLogCreate, FuelLogUpdate, FuelLogResponse,
    MaintenanceLogCreate, MaintenanceLogUpdate, MaintenanceLogResponse,
    ExpenseCreate, ExpenseResponse,
    ReminderCreate, ReminderUpdate, ReminderResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DriverCreate, DriverUpdate, DriverResponse,
    VendorCreate, VendorUpdate, VendorResponse,
    FleetStats
)

router = APIRouter(
    prefix="/fleet",
    tags=["fleet"]
)


# ==================== STATS ====================

@router.get("/stats", response_model=FleetStats)
async def get_fleet_stats(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get fleet dashboard statistics"""
    tenant_id = current_user.tenant_id
    today = date.today()
    month_start = today.replace(day=1)
    
    # Vehicle counts
    total = await db.scalar(select(func.count()).select_from(models.Vehicle).where(models.Vehicle.tenant_id == tenant_id))
    available = await db.scalar(select(func.count()).select_from(models.Vehicle).where(and_(models.Vehicle.tenant_id == tenant_id, models.Vehicle.status == 'AVAILABLE')))
    in_use = await db.scalar(select(func.count()).select_from(models.Vehicle).where(and_(models.Vehicle.tenant_id == tenant_id, models.Vehicle.status == 'IN_USE')))
    maintenance = await db.scalar(select(func.count()).select_from(models.Vehicle).where(and_(models.Vehicle.tenant_id == tenant_id, models.Vehicle.status == 'MAINTENANCE')))
    broken = await db.scalar(select(func.count()).select_from(models.Vehicle).where(and_(models.Vehicle.tenant_id == tenant_id, models.Vehicle.status == 'BROKEN')))
    
    # Active bookings
    active_bookings = await db.scalar(
        select(func.count()).select_from(models.VehicleBooking)
        .where(and_(
            models.VehicleBooking.tenant_id == tenant_id,
            models.VehicleBooking.status.in_(['PENDING', 'APPROVED', 'IN_USE'])
        ))
    )
    
    # Pending reminders (due within 30 days)
    pending_reminders = await db.scalar(
        select(func.count()).select_from(models.VehicleReminder)
        .where(and_(
            models.VehicleReminder.tenant_id == tenant_id,
            models.VehicleReminder.is_completed == False,
            models.VehicleReminder.due_date <= today + timedelta(days=30)
        ))
    )
    
    # Monthly costs
    fuel_cost = await db.scalar(
        select(func.coalesce(func.sum(models.VehicleFuelLog.total_cost), 0))
        .where(and_(
            models.VehicleFuelLog.tenant_id == tenant_id,
            models.VehicleFuelLog.date >= month_start
        ))
    )
    
    maint_cost = await db.scalar(
        select(func.coalesce(func.sum(models.VehicleMaintenanceLog.total_cost), 0))
        .where(and_(
            models.VehicleMaintenanceLog.tenant_id == tenant_id,
            models.VehicleMaintenanceLog.date >= month_start
        ))
    )
    
    expense_cost = await db.scalar(
        select(func.coalesce(func.sum(models.VehicleExpense.amount), 0))
        .where(and_(
            models.VehicleExpense.tenant_id == tenant_id,
            models.VehicleExpense.date >= month_start
        ))
    )
    
    return FleetStats(
        total_vehicles=total or 0,
        available_vehicles=available or 0,
        in_use_vehicles=in_use or 0,
        maintenance_vehicles=maintenance or 0,
        broken_vehicles=broken or 0,
        active_bookings=active_bookings or 0,
        pending_reminders=pending_reminders or 0,
        total_fuel_cost_month=fuel_cost or 0,
        total_maintenance_cost_month=maint_cost or 0,
        total_expense_month=expense_cost or 0
    )


# ==================== DEPARTMENTS ====================

@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all departments"""
    query = select(models.FleetDepartment).where(
        models.FleetDepartment.tenant_id == current_user.tenant_id,
        models.FleetDepartment.is_active == True
    ).order_by(models.FleetDepartment.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept: DepartmentCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a department"""
    db_dept = models.FleetDepartment(
        tenant_id=current_user.tenant_id,
        **dept.model_dump()
    )
    db.add(db_dept)
    await db.commit()
    await db.refresh(db_dept)
    return db_dept


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: UUID,
    dept_update: DepartmentUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a department"""
    result = await db.execute(
        select(models.FleetDepartment).where(
            models.FleetDepartment.id == dept_id,
            models.FleetDepartment.tenant_id == current_user.tenant_id
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    for key, value in dept_update.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    
    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a department (soft delete)"""
    result = await db.execute(
        select(models.FleetDepartment).where(
            models.FleetDepartment.id == dept_id,
            models.FleetDepartment.tenant_id == current_user.tenant_id
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    dept.is_active = False
    await db.commit()
    return {"message": "Department deleted successfully"}


# ==================== ORIGIN LOCATIONS ====================

@router.get("/origin-locations")
async def get_origin_locations(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get available origin locations (warehouses and storage zones)"""
    # Get warehouses
    wh_result = await db.execute(
        select(models.Warehouse)
        .where(models.Warehouse.tenant_id == current_user.tenant_id)
        .options(selectinload(models.Warehouse.zones))
    )
    warehouses = wh_result.scalars().all()
    
    locations = {
        "warehouses": [
            {"id": str(wh.id), "name": wh.name, "code": wh.code, "address": wh.address}
            for wh in warehouses
        ],
        "storage_zones": []
    }
    
    for wh in warehouses:
        for zone in wh.zones or []:
            locations["storage_zones"].append({
                "id": str(zone.id),
                "name": zone.zone_name,
                "warehouse_name": wh.name,
                "type": zone.zone_type.value if zone.zone_type else None
            })
    
    return locations


# ==================== DRIVERS ====================

def generate_qr_code(data: str) -> str:
    """Generate QR code as base64 data URI"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all drivers"""
    query = select(models.FleetDriver).where(
        models.FleetDriver.tenant_id == current_user.tenant_id,
        models.FleetDriver.is_active == True
    ).order_by(models.FleetDriver.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/drivers", response_model=DriverResponse)
async def create_driver(
    driver: DriverCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a driver with QR code"""
    # Generate code if not provided
    if not driver.code:
        count = await db.scalar(
            select(func.count()).select_from(models.FleetDriver)
            .where(models.FleetDriver.tenant_id == current_user.tenant_id)
        )
        driver_code = f"DR-{(count or 0) + 1:04d}"
    else:
        driver_code = driver.code
    
    # Generate QR code
    qr_data = f"DRIVER:{driver_code}:{driver.name}"
    qr_code = generate_qr_code(qr_data)
    
    db_driver = models.FleetDriver(
        tenant_id=current_user.tenant_id,
        code=driver_code,
        qr_code=qr_code,
        **driver.model_dump(exclude={'code'})
    )
    db.add(db_driver)
    await db.commit()
    await db.refresh(db_driver)
    return db_driver


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: UUID,
    driver_update: DriverUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a driver"""
    result = await db.execute(
        select(models.FleetDriver).where(
            models.FleetDriver.id == driver_id,
            models.FleetDriver.tenant_id == current_user.tenant_id
        )
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    for key, value in driver_update.model_dump(exclude_unset=True).items():
        setattr(driver, key, value)
    
    await db.commit()
    await db.refresh(driver)
    return driver


@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a driver (soft delete)"""
    result = await db.execute(
        select(models.FleetDriver).where(
            models.FleetDriver.id == driver_id,
            models.FleetDriver.tenant_id == current_user.tenant_id
        )
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    driver.is_active = False
    await db.commit()
    return {"message": "Driver deleted successfully"}


# ==================== VENDORS ====================

@router.get("/vendors", response_model=List[VendorResponse])
async def list_vendors(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all vendors"""
    query = select(models.FleetVendor).where(
        models.FleetVendor.tenant_id == current_user.tenant_id,
        models.FleetVendor.is_active == True
    ).order_by(models.FleetVendor.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    vendor: VendorCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a vendor"""
    # Generate code if not provided
    if not vendor.code:
        count = await db.scalar(
            select(func.count()).select_from(models.FleetVendor)
            .where(models.FleetVendor.tenant_id == current_user.tenant_id)
        )
        vendor_code = f"VND-{(count or 0) + 1:04d}"
    else:
        vendor_code = vendor.code
    
    db_vendor = models.FleetVendor(
        tenant_id=current_user.tenant_id,
        code=vendor_code,
        **vendor.model_dump(exclude={'code'})
    )
    db.add(db_vendor)
    await db.commit()
    await db.refresh(db_vendor)
    return db_vendor


@router.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: UUID,
    vendor_update: VendorUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a vendor"""
    result = await db.execute(
        select(models.FleetVendor).where(
            models.FleetVendor.id == vendor_id,
            models.FleetVendor.tenant_id == current_user.tenant_id
        )
    )
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    for key, value in vendor_update.model_dump(exclude_unset=True).items():
        setattr(vendor, key, value)
    
    await db.commit()
    await db.refresh(vendor)
    return vendor


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a vendor (soft delete)"""
    result = await db.execute(
        select(models.FleetVendor).where(
            models.FleetVendor.id == vendor_id,
            models.FleetVendor.tenant_id == current_user.tenant_id
        )
    )
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_active = False
    await db.commit()
    return {"message": "Vendor deleted successfully"}



# ==================== VEHICLES ====================

@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    status: str = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all vehicles"""
    query = select(models.Vehicle).where(models.Vehicle.tenant_id == current_user.tenant_id)
    if status:
        query = query.where(models.Vehicle.status == status)
    query = query.order_by(models.Vehicle.code)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/vehicles", response_model=VehicleResponse)
async def create_vehicle(
    vehicle: VehicleCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new vehicle"""
    # Generate code if not provided
    if not vehicle.code:
        count = await db.scalar(
            select(func.count()).select_from(models.Vehicle)
            .where(models.Vehicle.tenant_id == current_user.tenant_id)
        )
        vehicle.code = f"VH-{(count or 0) + 1:04d}"
    
    db_vehicle = models.Vehicle(
        tenant_id=current_user.tenant_id,
        **vehicle.model_dump()
    )
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get vehicle by ID"""
    result = await db.execute(
        select(models.Vehicle).where(
            models.Vehicle.id == vehicle_id,
            models.Vehicle.tenant_id == current_user.tenant_id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_update: VehicleUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a vehicle"""
    result = await db.execute(
        select(models.Vehicle).where(
            models.Vehicle.id == vehicle_id,
            models.Vehicle.tenant_id == current_user.tenant_id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    for key, value in vehicle_update.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)
    
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a vehicle"""
    result = await db.execute(
        select(models.Vehicle).where(
            models.Vehicle.id == vehicle_id,
            models.Vehicle.tenant_id == current_user.tenant_id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    await db.delete(vehicle)
    await db.commit()
    return {"message": "Vehicle deleted successfully"}


# ==================== BOOKINGS ====================

@router.get("/bookings", response_model=List[BookingResponse])
async def list_bookings(
    status: str = None,
    vehicle_id: UUID = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all bookings"""
    query = select(models.VehicleBooking).where(models.VehicleBooking.tenant_id == current_user.tenant_id)
    if status:
        query = query.where(models.VehicleBooking.status == status)
    if vehicle_id:
        query = query.where(models.VehicleBooking.vehicle_id == vehicle_id)
    query = query.order_by(models.VehicleBooking.start_datetime.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking: BookingCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new booking"""
    # Generate code
    today = date.today()
    count = await db.scalar(
        select(func.count()).select_from(models.VehicleBooking)
        .where(models.VehicleBooking.tenant_id == current_user.tenant_id)
    )
    code = f"BK-{today.year}-{(count or 0) + 1:04d}"
    
    # Handle timezone-aware datetime
    booking_data = booking.model_dump()
    if booking_data.get('start_datetime') and hasattr(booking_data['start_datetime'], 'replace'):
        booking_data['start_datetime'] = booking_data['start_datetime'].replace(tzinfo=None)
    if booking_data.get('end_datetime') and hasattr(booking_data['end_datetime'], 'replace'):
        booking_data['end_datetime'] = booking_data['end_datetime'].replace(tzinfo=None)
    
    db_booking = models.VehicleBooking(
        tenant_id=current_user.tenant_id,
        code=code,
        requested_by=current_user.id,
        **booking_data
    )
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    return db_booking


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    booking_update: BookingUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a booking"""
    result = await db.execute(
        select(models.VehicleBooking).where(
            models.VehicleBooking.id == booking_id,
            models.VehicleBooking.tenant_id == current_user.tenant_id
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = booking_update.model_dump(exclude_unset=True)
    
    # Handle approval
    if update_data.get('status') == BookingStatus.APPROVED and booking.status == 'PENDING':
        update_data['approved_by'] = current_user.id
        update_data['approved_at'] = datetime.utcnow()
    
    # Handle timezone
    for dt_field in ['start_datetime', 'end_datetime', 'actual_start', 'actual_end']:
        if update_data.get(dt_field) and hasattr(update_data[dt_field], 'replace'):
            update_data[dt_field] = update_data[dt_field].replace(tzinfo=None)
    
    for key, value in update_data.items():
        setattr(booking, key, value)
    
    await db.commit()
    await db.refresh(booking)
    return booking


@router.delete("/bookings/{booking_id}")
async def delete_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a booking"""
    result = await db.execute(
        select(models.VehicleBooking).where(
            models.VehicleBooking.id == booking_id,
            models.VehicleBooking.tenant_id == current_user.tenant_id
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.delete(booking)
    await db.commit()
    return {"message": "Booking deleted successfully"}


# ==================== FUEL LOGS ====================

@router.get("/fuel-logs", response_model=List[FuelLogResponse])
async def list_fuel_logs(
    vehicle_id: UUID = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List fuel logs"""
    query = select(models.VehicleFuelLog).where(models.VehicleFuelLog.tenant_id == current_user.tenant_id)
    if vehicle_id:
        query = query.where(models.VehicleFuelLog.vehicle_id == vehicle_id)
    query = query.order_by(models.VehicleFuelLog.date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/fuel-logs", response_model=FuelLogResponse)
async def create_fuel_log(
    fuel_log: FuelLogCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a fuel log entry"""
    # Calculate total cost
    total_cost = fuel_log.liters * fuel_log.price_per_liter
    
    # Get previous fuel log for efficiency calculation
    prev_result = await db.execute(
        select(models.VehicleFuelLog)
        .where(
            models.VehicleFuelLog.vehicle_id == fuel_log.vehicle_id,
            models.VehicleFuelLog.date < fuel_log.date
        )
        .order_by(models.VehicleFuelLog.date.desc())
        .limit(1)
    )
    prev_log = prev_result.scalar_one_or_none()
    
    distance_traveled = None
    fuel_efficiency = None
    if prev_log:
        distance_traveled = fuel_log.odometer - prev_log.odometer
        if fuel_log.liters > 0:
            fuel_efficiency = distance_traveled / fuel_log.liters
    
    # Update vehicle odometer
    vehicle_result = await db.execute(
        select(models.Vehicle).where(models.Vehicle.id == fuel_log.vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if vehicle:
        vehicle.current_odometer = fuel_log.odometer
    
    db_fuel_log = models.VehicleFuelLog(
        tenant_id=current_user.tenant_id,
        recorded_by=current_user.id,
        total_cost=total_cost,
        distance_traveled=distance_traveled,
        fuel_efficiency=fuel_efficiency,
        **fuel_log.model_dump()
    )
    db.add(db_fuel_log)
    await db.commit()
    await db.refresh(db_fuel_log)
    return db_fuel_log


# ==================== MAINTENANCE LOGS ====================

@router.get("/maintenance", response_model=List[MaintenanceLogResponse])
async def list_maintenance_logs(
    vehicle_id: UUID = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List maintenance logs"""
    query = select(models.VehicleMaintenanceLog).where(models.VehicleMaintenanceLog.tenant_id == current_user.tenant_id)
    if vehicle_id:
        query = query.where(models.VehicleMaintenanceLog.vehicle_id == vehicle_id)
    query = query.order_by(models.VehicleMaintenanceLog.date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/maintenance", response_model=MaintenanceLogResponse)
async def create_maintenance_log(
    maint_log: MaintenanceLogCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a maintenance log entry"""
    total_cost = maint_log.parts_cost + maint_log.labor_cost
    
    # Update vehicle odometer if provided
    if maint_log.odometer:
        vehicle_result = await db.execute(
            select(models.Vehicle).where(models.Vehicle.id == maint_log.vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if vehicle:
            vehicle.current_odometer = maint_log.odometer
    
    db_maint = models.VehicleMaintenanceLog(
        tenant_id=current_user.tenant_id,
        recorded_by=current_user.id,
        total_cost=total_cost,
        **maint_log.model_dump()
    )
    db.add(db_maint)
    await db.commit()
    await db.refresh(db_maint)
    return db_maint


# ==================== EXPENSES ====================

@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    vehicle_id: UUID = None,
    category: str = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List vehicle expenses"""
    query = select(models.VehicleExpense).where(models.VehicleExpense.tenant_id == current_user.tenant_id)
    if vehicle_id:
        query = query.where(models.VehicleExpense.vehicle_id == vehicle_id)
    if category:
        query = query.where(models.VehicleExpense.category == category)
    query = query.order_by(models.VehicleExpense.date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(
    expense: ExpenseCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create an expense entry"""
    db_expense = models.VehicleExpense(
        tenant_id=current_user.tenant_id,
        recorded_by=current_user.id,
        **expense.model_dump()
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense


# ==================== REMINDERS ====================

@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(
    vehicle_id: UUID = None,
    due_soon: bool = False,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List reminders"""
    query = select(models.VehicleReminder).where(
        models.VehicleReminder.tenant_id == current_user.tenant_id,
        models.VehicleReminder.is_completed == False
    )
    if vehicle_id:
        query = query.where(models.VehicleReminder.vehicle_id == vehicle_id)
    if due_soon:
        query = query.where(models.VehicleReminder.due_date <= date.today() + timedelta(days=30))
    query = query.order_by(models.VehicleReminder.due_date)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/reminders", response_model=ReminderResponse)
async def create_reminder(
    reminder: ReminderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a reminder"""
    db_reminder = models.VehicleReminder(
        tenant_id=current_user.tenant_id,
        **reminder.model_dump()
    )
    db.add(db_reminder)
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder


@router.put("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    reminder_update: ReminderUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a reminder"""
    result = await db.execute(
        select(models.VehicleReminder).where(
            models.VehicleReminder.id == reminder_id,
            models.VehicleReminder.tenant_id == current_user.tenant_id
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    update_data = reminder_update.model_dump(exclude_unset=True)
    
    # Handle completion
    if update_data.get('is_completed') and not reminder.is_completed:
        update_data['completed_at'] = datetime.utcnow()
        update_data['completed_by'] = current_user.id
    
    for key, value in update_data.items():
        setattr(reminder, key, value)
    
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a reminder"""
    result = await db.execute(
        select(models.VehicleReminder).where(
            models.VehicleReminder.id == reminder_id,
            models.VehicleReminder.tenant_id == current_user.tenant_id
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    await db.delete(reminder)
    await db.commit()
    return {"message": "Reminder deleted successfully"}
