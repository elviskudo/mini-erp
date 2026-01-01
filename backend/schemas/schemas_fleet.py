"""
Fleet Management Schemas
Pydantic schemas for vehicles, bookings, fuel logs, maintenance, expenses, and reminders
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from enum import Enum


# ==================== ENUMS ====================

class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"
    BROKEN = "BROKEN"
    RETIRED = "RETIRED"


class VehicleCategory(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    LOGISTICS = "LOGISTICS"
    RENTAL = "RENTAL"
    EXECUTIVE = "EXECUTIVE"
    OTHER = "OTHER"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_USE = "IN_USE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class BookingPurpose(str, Enum):
    BUSINESS_TRIP = "BUSINESS_TRIP"
    DELIVERY = "DELIVERY"
    CLIENT_VISIT = "CLIENT_VISIT"
    SITE_INSPECTION = "SITE_INSPECTION"
    PICKUP = "PICKUP"
    EVENT = "EVENT"
    TRAINING = "TRAINING"
    OTHER = "OTHER"


class BookingOriginType(str, Enum):
    WAREHOUSE = "WAREHOUSE"
    STORAGE_ZONE = "STORAGE_ZONE"
    MANUAL = "MANUAL"


class ExpenseCategory(str, Enum):
    FUEL = "FUEL"
    TOLL = "TOLL"
    PARKING = "PARKING"
    SERVICE = "SERVICE"
    TAX = "TAX"
    INSURANCE = "INSURANCE"
    KIR = "KIR"
    OTHER = "OTHER"


class ReminderType(str, Enum):
    TAX = "TAX"
    SERVICE = "SERVICE"
    INSURANCE = "INSURANCE"
    KIR = "KIR"
    STNK = "STNK"
    OTHER = "OTHER"


# ==================== DEPARTMENT SCHEMAS ====================

class DepartmentBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== DRIVER SCHEMAS ====================

class DriverBase(BaseModel):
    name: str
    phone: str  # Required
    email: Optional[str] = None
    card_id_url: Optional[str] = None  # Uploaded ID card image
    card_id_number: str  # Required - ID card number (KTP)
    employment_status: str  # Required - PERMANENT, CONTRACT, FREELANCE
    license_number: str  # Required - SIM number
    license_type: str  # Required - A, B1, B2, C
    license_expiry: Optional[date] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class DriverCreate(DriverBase):
    code: Optional[str] = None


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    card_id_url: Optional[str] = None
    card_id_number: Optional[str] = None
    employment_status: Optional[str] = None
    license_number: Optional[str] = None
    license_type: Optional[str] = None
    license_expiry: Optional[date] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DriverResponse(BaseModel):
    """Response schema with Optional fields to handle existing NULL database values"""
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    card_id_url: Optional[str] = None
    card_id_number: Optional[str] = None
    employment_status: Optional[str] = None
    license_number: Optional[str] = None
    license_type: Optional[str] = None
    license_expiry: Optional[date] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    qr_code: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True



# ==================== VENDOR SCHEMAS ====================

class VendorBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    service_types: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class VendorCreate(VendorBase):
    code: Optional[str] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    service_types: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class VendorResponse(VendorBase):
    id: UUID
    tenant_id: UUID
    code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ==================== VEHICLE SCHEMAS ====================

class VehicleBase(BaseModel):
    plate_number: str
    brand: str
    model: str
    year: Optional[int] = None
    color: Optional[str] = None
    vehicle_type: Optional[str] = None
    category: VehicleCategory = VehicleCategory.OPERATIONAL
    capacity: Optional[str] = None
    fuel_type: str = "Gasoline"
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    stnk_number: Optional[str] = None
    bpkb_number: Optional[str] = None
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_odometer: float = 0
    purchase_date: Optional[date] = None
    purchase_cost: float = 0
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    code: Optional[str] = None


class VehicleUpdate(BaseModel):
    plate_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    vehicle_type: Optional[str] = None
    category: Optional[VehicleCategory] = None
    capacity: Optional[str] = None
    fuel_type: Optional[str] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    stnk_number: Optional[str] = None
    bpkb_number: Optional[str] = None
    status: Optional[VehicleStatus] = None
    current_odometer: Optional[float] = None
    notes: Optional[str] = None


class VehicleResponse(VehicleBase):
    id: UUID
    tenant_id: UUID
    code: str
    stnk_url: Optional[str] = None
    bpkb_url: Optional[str] = None
    insurance_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== BOOKING SCHEMAS ====================

class BookingBase(BaseModel):
    purpose: BookingPurpose = BookingPurpose.BUSINESS_TRIP
    # Origin
    origin_type: BookingOriginType = BookingOriginType.MANUAL
    origin_warehouse_id: Optional[UUID] = None
    origin_zone_id: Optional[UUID] = None
    origin_address: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    # Destination (required)
    destination: str
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    # Schedule
    start_datetime: datetime
    end_datetime: datetime
    # Assignment
    department_id: Optional[UUID] = None
    project_id: Optional[str] = None
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    vehicle_id: UUID
    driver_id: Optional[UUID] = None


class BookingUpdate(BaseModel):
    purpose: Optional[BookingPurpose] = None
    origin_type: Optional[BookingOriginType] = None
    origin_warehouse_id: Optional[UUID] = None
    origin_zone_id: Optional[UUID] = None
    origin_address: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination: Optional[str] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    status: Optional[BookingStatus] = None
    start_odometer: Optional[float] = None
    end_odometer: Optional[float] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    department_id: Optional[UUID] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    code: str
    purpose: BookingPurpose
    # Origin
    origin_type: BookingOriginType
    origin_warehouse_id: Optional[UUID] = None
    origin_zone_id: Optional[UUID] = None
    origin_address: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    # Destination
    destination: str
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    # Schedule
    start_datetime: datetime
    end_datetime: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    # Odometer
    start_odometer: Optional[float] = None
    end_odometer: Optional[float] = None
    # Assignment
    status: BookingStatus
    requested_by: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    project_id: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True



# ==================== FUEL LOG SCHEMAS ====================

class FuelLogBase(BaseModel):
    date: date
    odometer: float
    fuel_type: str = "Gasoline"
    liters: float
    price_per_liter: float
    gas_station: str  # Required
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None


class FuelLogCreate(FuelLogBase):
    vehicle_id: UUID
    driver_id: Optional[UUID] = None
    receipt_url: str  # Required


class FuelLogUpdate(BaseModel):
    date: Optional[date] = None
    odometer: Optional[float] = None
    fuel_type: Optional[str] = None
    liters: Optional[float] = None
    price_per_liter: Optional[float] = None
    gas_station: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    driver_id: Optional[UUID] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class FuelLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    driver_id: Optional[UUID] = None
    date: date
    odometer: float
    fuel_type: str
    liters: float
    price_per_liter: float
    total_cost: float
    gas_station: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    distance_traveled: Optional[float] = None
    fuel_efficiency: Optional[float] = None
    recorded_by: Optional[UUID] = None
    receipt_url: str
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MAINTENANCE LOG SCHEMAS ====================

class MaintenanceLogBase(BaseModel):
    date: date
    odometer: float  # Required
    service_type: str
    description: str
    parts_cost: float = 0
    labor_cost: float = 0
    next_service_date: date  # Required
    next_service_odometer: Optional[float] = None
    performed_by: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class MaintenanceLogCreate(MaintenanceLogBase):
    vehicle_id: UUID
    vendor_id: UUID  # Required
    receipt_url: Optional[str] = None


class MaintenanceLogUpdate(BaseModel):
    date: Optional[date] = None
    odometer: Optional[float] = None
    service_type: Optional[str] = None
    description: Optional[str] = None
    vendor_id: Optional[UUID] = None
    parts_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    next_service_date: Optional[date] = None
    next_service_odometer: Optional[float] = None
    performed_by: Optional[str] = None
    invoice_number: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class MaintenanceLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    vendor_id: UUID
    date: date
    odometer: float
    service_type: str
    description: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    parts_cost: float
    labor_cost: float
    total_cost: float
    next_service_date: date
    next_service_odometer: Optional[float] = None
    performed_by: Optional[str] = None
    invoice_number: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== EXPENSE SCHEMAS ====================

class ExpenseBase(BaseModel):
    date: date
    category: ExpenseCategory = ExpenseCategory.OTHER
    description: str
    amount: float
    booking_id: Optional[UUID] = None
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    vehicle_id: UUID


class ExpenseResponse(ExpenseBase):
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    recorded_by: Optional[UUID] = None
    receipt_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== REMINDER SCHEMAS ====================

class ReminderBase(BaseModel):
    reminder_type: ReminderType
    title: str
    due_date: date
    remind_days_before: int = 30
    notes: Optional[str] = None


class ReminderCreate(ReminderBase):
    vehicle_id: UUID


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[date] = None
    remind_days_before: Optional[int] = None
    is_completed: Optional[bool] = None
    notes: Optional[str] = None


class ReminderResponse(ReminderBase):
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    is_notified: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    completed_by: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== STATS SCHEMAS ====================

class FleetStats(BaseModel):
    total_vehicles: int
    available_vehicles: int
    in_use_vehicles: int
    maintenance_vehicles: int
    broken_vehicles: int
    active_bookings: int
    pending_reminders: int
    total_fuel_cost_month: float
    total_maintenance_cost_month: float
    total_expense_month: float
