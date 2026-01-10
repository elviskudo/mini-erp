"""
Fleet Management Module Models
Handles vehicle registration, bookings, fuel tracking, maintenance, expenses, and reminders
"""
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, Date, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


# ==================== ENUMS ====================

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"
    BROKEN = "BROKEN"
    RETIRED = "RETIRED"


class VehicleCategory(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    LOGISTICS = "LOGISTICS"
    RENTAL = "RENTAL"
    EXECUTIVE = "EXECUTIVE"
    OTHER = "OTHER"


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_USE = "IN_USE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class BookingPurpose(str, enum.Enum):
    BUSINESS_TRIP = "BUSINESS_TRIP"
    DELIVERY = "DELIVERY"
    CLIENT_VISIT = "CLIENT_VISIT"
    SITE_INSPECTION = "SITE_INSPECTION"
    PICKUP = "PICKUP"
    EVENT = "EVENT"
    TRAINING = "TRAINING"
    OTHER = "OTHER"


class BookingOriginType(str, enum.Enum):
    WAREHOUSE = "WAREHOUSE"
    STORAGE_ZONE = "STORAGE_ZONE"
    MANUAL = "MANUAL"


class ExpenseCategory(str, enum.Enum):
    FUEL = "FUEL"
    TOLL = "TOLL"
    PARKING = "PARKING"
    SERVICE = "SERVICE"
    TAX = "TAX"
    INSURANCE = "INSURANCE"
    KIR = "KIR"
    OTHER = "OTHER"


class ReminderType(str, enum.Enum):
    TAX = "TAX"
    SERVICE = "SERVICE"
    INSURANCE = "INSURANCE"
    KIR = "KIR"
    STNK = "STNK"
    OTHER = "OTHER"


# ==================== DEPARTMENTS ====================

class FleetDepartment(Base):
    """Department management for fleet"""
    __tablename__ = "fleet_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== DRIVERS ====================

class FleetDriver(Base):
    """Driver management for fleet"""
    __tablename__ = "fleet_drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, nullable=False)  # DR-0001
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Card ID
    card_id_url = Column(String, nullable=True)  # Uploaded ID card image
    card_id_number = Column(String, nullable=True)  # ID card number (KTP/SIM)
    # Employment status
    employment_status = Column(String, nullable=True)  # PERMANENT, CONTRACT, FREELANCE
    # License info
    license_number = Column(String, nullable=True)  # SIM number
    license_type = Column(String, nullable=True)  # A, B1, B2, C
    license_expiry = Column(Date, nullable=True)
    address = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    qr_code = Column(Text, nullable=True)  # QR code data/URL
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== VENDORS ====================

class FleetVendor(Base):
    """Vendor/Workshop management for fleet maintenance"""
    __tablename__ = "fleet_vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, nullable=False)  # VND-0001
    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    service_types = Column(String, nullable=True)  # Comma-separated: Oil,Tire,Engine
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== VEHICLES ====================


class Vehicle(Base):
    """Vehicle registration"""
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Basic info
    code = Column(String, nullable=False, index=True)  # Auto-generated or manual
    plate_number = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    color = Column(String, nullable=True)
    
    # Specifications
    vehicle_type = Column(String, nullable=True)  # Car, Truck, Motorcycle, etc.
    category = Column(Enum(VehicleCategory), default=VehicleCategory.OPERATIONAL)
    capacity = Column(String, nullable=True)  # "5 passengers" or "2 tons"
    fuel_type = Column(String, default="Gasoline")  # Gasoline, Diesel, Electric
    
    # Registration
    chassis_number = Column(String, nullable=True)
    engine_number = Column(String, nullable=True)
    stnk_number = Column(String, nullable=True)
    bpkb_number = Column(String, nullable=True)
    
    # Status
    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    current_odometer = Column(Float, default=0)  # km
    
    # Purchase info
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, default=0)
    
    # Documents (URLs)
    stnk_url = Column(String, nullable=True)
    bpkb_url = Column(String, nullable=True)
    insurance_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("VehicleBooking", back_populates="vehicle", cascade="all, delete-orphan")
    fuel_logs = relationship("VehicleFuelLog", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_logs = relationship("VehicleMaintenanceLog", back_populates="vehicle", cascade="all, delete-orphan")
    expenses = relationship("VehicleExpense", back_populates="vehicle", cascade="all, delete-orphan")
    reminders = relationship("VehicleReminder", back_populates="vehicle", cascade="all, delete-orphan")


# ==================== BOOKINGS ====================

class VehicleBooking(Base):
    """Vehicle usage scheduling"""
    __tablename__ = "vehicle_bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    
    # Booking details
    code = Column(String, nullable=False, index=True)  # BK-2024-0001
    purpose = Column(Enum(BookingPurpose), default=BookingPurpose.BUSINESS_TRIP)
    
    # Origin location
    origin_type = Column(Enum(BookingOriginType), default=BookingOriginType.MANUAL)
    origin_warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    origin_zone_id = Column(UUID(as_uuid=True), ForeignKey("storage_zones.id"), nullable=True)
    origin_address = Column(String, nullable=True)  # For manual input
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    
    # Destination location (required)
    destination = Column(String, nullable=False)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    
    # Time
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    # Odometer
    start_odometer = Column(Float, nullable=True)
    end_odometer = Column(Float, nullable=True)
    
    # Assignment
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("fleet_drivers.id"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("fleet_departments.id"), nullable=True)
    project_id = Column(String, nullable=True)  # Link to project if applicable
    
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    reject_reason = Column(Text, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="bookings")
    department = relationship("FleetDepartment")
    driver = relationship("FleetDriver")



# ==================== FUEL LOGS ====================

class VehicleFuelLog(Base):
    """Fuel consumption tracking"""
    __tablename__ = "vehicle_fuel_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("fleet_drivers.id"), nullable=True)
    
    date = Column(Date, nullable=False)
    odometer = Column(Float, nullable=False)  # Current km reading
    
    # Fuel details
    fuel_type = Column(String, default="Gasoline")
    liters = Column(Float, nullable=False)
    price_per_liter = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Location
    gas_station = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Efficiency calculation
    distance_traveled = Column(Float, nullable=True)  # km since last fill
    fuel_efficiency = Column(Float, nullable=True)  # km/liter
    
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    receipt_url = Column(String, nullable=False)  # Invoice upload required
    invoice_number = Column(String, nullable=True)  # Extracted from OCR
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="fuel_logs")
    driver = relationship("FleetDriver")



# ==================== MAINTENANCE LOGS ====================

class VehicleMaintenanceLog(Base):
    """Service and repair records"""
    __tablename__ = "vehicle_maintenance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("fleet_vendors.id"), nullable=False)
    
    date = Column(Date, nullable=False)
    odometer = Column(Float, nullable=False)  # Required
    
    # Service details
    service_type = Column(String, nullable=False)  # Routine, Repair, Inspection, etc.
    description = Column(Text, nullable=False)
    
    # Location
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Parts and labor
    parts_cost = Column(Float, default=0, nullable=False)
    labor_cost = Column(Float, default=0, nullable=False)
    total_cost = Column(Float, default=0, nullable=False)
    
    # Next service - required
    next_service_date = Column(Date, nullable=False)
    next_service_odometer = Column(Float, nullable=True)
    
    performed_by = Column(String, nullable=True)  # Mechanic name
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    invoice_number = Column(String, nullable=True)
    receipt_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_logs")
    vendor = relationship("FleetVendor")



# ==================== EXPENSES ====================

class VehicleExpense(Base):
    """Operational costs"""
    __tablename__ = "vehicle_expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    
    date = Column(Date, nullable=False)
    category = Column(Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    
    # Link to booking if applicable
    booking_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_bookings.id"), nullable=True)
    
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    receipt_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="expenses")


# ==================== REMINDERS ====================

class VehicleReminder(Base):
    """Document expiry and service reminders"""
    __tablename__ = "vehicle_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    
    reminder_type = Column(Enum(ReminderType), nullable=False)
    title = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Notification settings
    remind_days_before = Column(Integer, default=30)  # Notify 30 days before
    is_notified = Column(Boolean, default=False)
    
    # Additional fields
    description = Column(Text, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    reference_number = Column(String, nullable=True)  # STNK number, SIM number, etc.
    document_url = Column(String, nullable=True)  # Uploaded document image
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="reminders")


# ==================== DOCUMENT TYPE ENUM ====================

class DocumentType(str, enum.Enum):
    MAINTENANCE_INVOICE = "MAINTENANCE_INVOICE"
    EXPENSE_RECEIPT = "EXPENSE_RECEIPT"
    FUEL_RECEIPT = "FUEL_RECEIPT"
    STNK = "STNK"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    KIR = "KIR"
    INSURANCE = "INSURANCE"
    OTHER = "OTHER"


# ==================== FLEET INVOICES/DOCUMENTS ====================

class FleetInvoice(Base):
    """Shared table for extracted invoice and document data"""
    __tablename__ = "fleet_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Document classification
    document_type = Column(Enum(DocumentType), nullable=False)
    source_table = Column(String, nullable=True)  # e.g. vehicle_maintenance_logs, vehicle_expenses
    source_id = Column(UUID(as_uuid=True), nullable=True)  # FK to source record
    
    # File info
    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    
    # Extracted invoice data
    invoice_number = Column(String, nullable=True)
    vendor_name = Column(String, nullable=True)
    invoice_date = Column(Date, nullable=True)
    subtotal = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    currency = Column(String, default="IDR")
    
    # For STNK/License extraction
    document_number = Column(String, nullable=True)  # STNK number, license number
    expiry_date = Column(Date, nullable=True)
    holder_name = Column(String, nullable=True)
    
    # Line items (stored as JSON array)
    line_items = Column(Text, nullable=True)  # JSON array of items
    
    # Extraction metadata
    raw_extracted_text = Column(Text, nullable=True)
    extraction_confidence = Column(Float, nullable=True)  # 0-1
    is_valid_document = Column(Boolean, default=True)
    validation_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
