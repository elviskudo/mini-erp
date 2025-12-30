"""
Maintenance Module Models
Handles asset management, work orders, maintenance schedules, and cost tracking
"""
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


# ==================== ASSETS ====================

class Asset(Base):
    """Asset/Equipment to be maintained"""
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String, nullable=False, index=True)  # EQP-001
    name = Column(String, nullable=False)
    category = Column(String)  # Equipment, Vehicle, Building, etc.
    location = Column(String)
    status = Column(String, default='OPERATIONAL')  # OPERATIONAL, UNDER_MAINTENANCE, BROKEN, RETIRED
    
    # Purchase info
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, default=0.0)
    serial_number = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    
    notes = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_orders = relationship("MaintenanceWorkOrder", back_populates="asset", cascade="all, delete-orphan")
    schedules = relationship("MaintenanceSchedule", back_populates="asset", cascade="all, delete-orphan")


# ==================== MAINTENANCE TYPES ====================

class MaintenanceType(Base):
    """Types of maintenance: Preventive, Corrective, etc."""
    __tablename__ = "maintenance_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String, nullable=False)  # PM, CM
    name = Column(String, nullable=False)  # Preventive Maintenance, Corrective Maintenance
    description = Column(Text, nullable=True)
    is_scheduled = Column(Boolean, default=False)  # PM is scheduled, CM is not
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== WORK ORDERS ====================

class MaintenanceWorkOrder(Base):
    """Work Order for maintenance tasks"""
    __tablename__ = "maintenance_work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String, nullable=False, index=True)  # WO-2024-001
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    type_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_types.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    status = Column(String, default='DRAFT')  # DRAFT, SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    
    # Timeline
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="work_orders")
    tasks = relationship("MaintenanceWorkOrderTask", back_populates="work_order", cascade="all, delete-orphan")
    parts = relationship("MaintenanceWorkOrderPart", back_populates="work_order", cascade="all, delete-orphan")
    costs = relationship("MaintenanceWorkOrderCost", back_populates="work_order", cascade="all, delete-orphan")


class MaintenanceWorkOrderTask(Base):
    """Tasks within a work order"""
    __tablename__ = "maintenance_work_order_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)
    
    description = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    work_order = relationship("MaintenanceWorkOrder", back_populates="tasks")


class MaintenanceWorkOrderPart(Base):
    """Spare parts used in work order"""
    __tablename__ = "maintenance_work_order_parts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)
    
    part_name = Column(String, nullable=False)
    part_number = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    unit_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Relationships
    work_order = relationship("MaintenanceWorkOrder", back_populates="parts")


class MaintenanceWorkOrderCost(Base):
    """Cost entries for work order"""
    __tablename__ = "maintenance_work_order_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)
    
    category = Column(String, default='OTHER')  # LABOR, PARTS, EXTERNAL, OTHER
    description = Column(String, nullable=False)
    amount = Column(Float, default=0.0)
    date = Column(Date, default=datetime.utcnow)
    
    # Relationships
    work_order = relationship("MaintenanceWorkOrder", back_populates="costs")


# ==================== MAINTENANCE SCHEDULES ====================

class MaintenanceSchedule(Base):
    """Preventive maintenance schedules"""
    __tablename__ = "maintenance_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    type_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_types.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(String, default='MONTHLY')  # DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
    interval_days = Column(Integer, default=30)
    
    last_performed = Column(Date, nullable=True)
    next_due = Column(Date, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="schedules")
