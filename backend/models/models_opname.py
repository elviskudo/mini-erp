import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Enum, DateTime, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base


class OpnameStatus(str, enum.Enum):
    DRAFT = "DRAFT"            # Legacy - old records (backward compatibility)
    SCHEDULED = "Scheduled"    # Opname scheduled, not started
    IN_PROGRESS = "In Progress"  # Counting in progress
    COUNTING_DONE = "Counting Done"  # Counting complete, pending review
    REVIEWED = "Reviewed"      # Reviewed, pending approval
    APPROVED = "Approved"      # Approved for adjustment
    POSTED = "Posted"          # Adjustments posted to inventory
    CANCELLED = "Cancelled"    # Opname cancelled


class OpnameFrequency(str, enum.Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"
    ADHOC = "Ad-hoc"


class VarianceReason(str, enum.Enum):
    THEFT = "Theft"
    DAMAGE = "Damage"
    INPUT_ERROR = "Input Error"
    RETURN_NOT_RECORDED = "Return Not Recorded"
    RECEIVING_ERROR = "Receiving Error"
    EXPIRED = "Expired"
    SHRINKAGE = "Shrinkage"
    SYSTEM_ERROR = "System Error"
    UNKNOWN = "Unknown"
    OTHER = "Other"


class OpnameSchedule(Base):
    """Schedule for recurring or one-time opname events"""
    __tablename__ = "opname_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # e.g., "Monthly Full Count", "Weekly Fast-Moving"
    description = Column(Text, nullable=True)
    frequency = Column(Enum(OpnameFrequency), default=OpnameFrequency.MONTHLY)
    
    scheduled_date = Column(DateTime, nullable=False)  # Next scheduled date
    start_time = Column(String(10), nullable=True)  # e.g., "09:00"
    estimated_duration_hours = Column(Integer, default=4)
    
    # Filters for what to count
    count_all_items = Column(Boolean, default=True)
    category_filter = Column(String(255), nullable=True)  # JSON array of category IDs
    location_filter = Column(String(255), nullable=True)  # JSON array of location IDs
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    warehouse = relationship("Warehouse")
    assignments = relationship("OpnameAssignment", back_populates="schedule", cascade="all, delete-orphan")


class OpnameAssignment(Base):
    """Assign team members to opname schedules"""
    __tablename__ = "opname_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("opname_schedules.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    role = Column(String(50), default="Counter")  # Counter, Supervisor, Approver
    assigned_locations = Column(Text, nullable=True)  # JSON array of location codes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    schedule = relationship("OpnameSchedule", back_populates="assignments")
    user = relationship("User")


class StockOpname(Base):
    """Main stock opname header - tracks a single opname event"""
    __tablename__ = "stock_opnames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("opname_schedules.id"), nullable=True)  # Optional link to schedule
    
    opname_number = Column(String(50), nullable=True)  # Auto-generated: OPN-YYYYMMDD-001
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OpnameStatus), default=OpnameStatus.SCHEDULED)
    notes = Column(Text, nullable=True)
    
    # Progress tracking
    total_items = Column(Integer, default=0)
    counted_items = Column(Integer, default=0)
    items_with_variance = Column(Integer, default=0)
    
    # Summary values (calculated after counting)
    total_system_value = Column(Float, default=0)
    total_counted_value = Column(Float, default=0)
    total_variance_value = Column(Float, default=0)
    
    # Workflow tracking
    counting_started_at = Column(DateTime, nullable=True)
    counting_completed_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    details = relationship("StockOpnameDetail", back_populates="opname", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse")
    schedule = relationship("OpnameSchedule")


class StockOpnameDetail(Base):
    """Individual items in an opname - tracks system vs counted qty"""
    __tablename__ = "stock_opname_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    opname_id = Column(UUID(as_uuid=True), ForeignKey("stock_opnames.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    
    # Quantities
    system_qty = Column(Float, nullable=False)
    counted_qty = Column(Float, nullable=True)  # Nullable until counted
    variance = Column(Float, default=0)  # counted - system (calculated)
    
    # Values (for reporting)
    unit_cost = Column(Float, default=0)
    system_value = Column(Float, default=0)  # system_qty * unit_cost
    counted_value = Column(Float, default=0)  # counted_qty * unit_cost
    variance_value = Column(Float, default=0)  # variance * unit_cost
    
    # Variance tracking
    variance_reason = Column(Enum(VarianceReason), nullable=True)
    variance_notes = Column(Text, nullable=True)
    
    # Counting workflow
    counted_at = Column(DateTime, nullable=True)
    counted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Flag for recount
    needs_recount = Column(Boolean, default=False)
    recount_reason = Column(String(255), nullable=True)

    opname = relationship("StockOpname", back_populates="details")
    product = relationship("Product")
    batch = relationship("InventoryBatch")
    location = relationship("Location")
