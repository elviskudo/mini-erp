import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from database import Base


class ProductType(str, enum.Enum):
    RAW_MATERIAL = "Raw Material"
    WIP = "WIP"
    FINISHED_GOODS = "Finished Goods"


class Category(Base):
    """Product categories for organization and filtering"""
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class WorkCenter(Base):
    __tablename__ = "work_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    cost_per_hour = Column(Float, default=0.0)
    capacity_hours = Column(Float, default=8.0)
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)  # Product description
    type = Column(Enum(ProductType), default=ProductType.RAW_MATERIAL)
    uom = Column(String, default="pcs")  # Unit of Measure
    
    # Category - FK to categories table
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    category = Column(String, nullable=True)  # Keep for backward compatibility
    
    # Product origin
    is_manufactured = Column(Boolean, default=True)  # False = purchased externally
    is_active = Column(Boolean, default=True)  # For POS filtering
    image_url = Column(Text, nullable=True)  # Base64 or URL for product image
    
    # Cost & Pricing
    standard_cost = Column(Float, default=0.0)
    weighted_avg_cost = Column(Float, default=0.0)  # Updated on each receipt
    desired_margin = Column(Float, default=0.30)  # 30% default margin
    suggested_selling_price = Column(Float, default=0.0)  # HPP / (1 - margin)
    
    # Cold chain requirements
    requires_cold_chain = Column(Boolean, default=False)
    max_storage_temp = Column(Float, nullable=True)  # Max allowed temperature

    # Relationship
    category_rel = relationship("Category", foreign_keys=[category_id])


class BillOfMaterial(Base):
    __tablename__ = "bill_of_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    version = Column(String, default="1.0")
    is_active = Column(Boolean, default=True)

    product = relationship("Product", backref="boms")
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")


class BOMItem(Base):
    __tablename__ = "bom_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    bom_id = Column(UUID(as_uuid=True), ForeignKey("bill_of_materials.id"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    waste_percentage = Column(Float, default=0.0)

    bom = relationship("BillOfMaterial", back_populates="items")
    component = relationship("Product", foreign_keys=[component_id])


class ProductionOrderStatus(str, enum.Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    order_no = Column(String, nullable=False, index=True)
    status = Column(Enum(ProductionOrderStatus), default=ProductionOrderStatus.DRAFT)
    
    # Quantity tracking
    target_qty = Column(Float, nullable=False, default=0.0)  # Daily target
    quantity = Column(Float, nullable=False)  # Planned quantity
    completed_qty = Column(Float, default=0.0)  # Actual completed
    progress = Column(Integer, default=0)  # Percentage 0-100
    
    # Scheduling
    scheduled_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Labor tracking
    labor_hours = Column(Float, default=0.0)
    hourly_rate = Column(Float, default=0.0)
    
    # Cost breakdown (HPP)
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    total_hpp = Column(Float, default=0.0)  # Total cost of goods manufactured
    hpp_per_unit = Column(Float, default=0.0)
    
    notes = Column(String, nullable=True)
    
    # Relationships
    products = relationship("ProductionOrderProduct", back_populates="production_order", cascade="all, delete-orphan")
    work_centers = relationship("ProductionOrderWorkCenter", back_populates="production_order", cascade="all, delete-orphan")



class ProductionOrderProduct(Base):
    __tablename__ = "production_order_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    production_order = relationship("ProductionOrder", back_populates="products")
    product = relationship("Product")


class ProductionOrderWorkCenter(Base):
    __tablename__ = "production_order_work_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    work_center_id = Column(UUID(as_uuid=True), ForeignKey("work_centers.id"), nullable=False)
    
    production_order = relationship("ProductionOrder", back_populates="work_centers")
    work_center = relationship("WorkCenter")


# ============ ROUTING ============

class Routing(Base):
    """Production routing - defines steps to produce a product"""
    __tablename__ = "routings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g. "Standard Assembly Process"
    version = Column(String, default="1.0")
    is_active = Column(Boolean, default=True)
    total_time_hours = Column(Float, default=0.0)  # Calculated from steps
    
    product = relationship("Product", backref="routings")
    steps = relationship("RoutingStep", back_populates="routing", order_by="RoutingStep.sequence", cascade="all, delete-orphan")


class RoutingStep(Base):
    """Individual step in a routing"""
    __tablename__ = "routing_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    routing_id = Column(UUID(as_uuid=True), ForeignKey("routings.id"), nullable=False)
    work_center_id = Column(UUID(as_uuid=True), ForeignKey("work_centers.id"), nullable=False)
    
    sequence = Column(Integer, nullable=False)  # Step order: 10, 20, 30...
    operation_name = Column(String, nullable=False)  # e.g. "Cutting", "Assembly", "Finishing"
    description = Column(Text, nullable=True)
    setup_time_mins = Column(Float, default=0.0)  # Setup/preparation time
    run_time_mins = Column(Float, default=0.0)  # Time per unit
    
    routing = relationship("Routing", back_populates="steps")
    work_center = relationship("WorkCenter")


# ============ WORK ORDER ============

class WorkOrderStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"


class WorkOrder(Base):
    """Work order for a specific production step"""
    __tablename__ = "work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    routing_step_id = Column(UUID(as_uuid=True), ForeignKey("routing_steps.id"), nullable=True)
    work_center_id = Column(UUID(as_uuid=True), ForeignKey("work_centers.id"), nullable=False)
    
    work_order_no = Column(String, nullable=False, index=True)  # WO-YYYYMMDD-001
    sequence = Column(Integer, default=10)
    operation_name = Column(String, nullable=False)
    status = Column(String, default="Pending")  # Pending, In Progress, Completed
    
    # Quantities
    planned_qty = Column(Float, default=0.0)
    completed_qty = Column(Float, default=0.0)
    scrap_qty = Column(Float, default=0.0)
    
    # Time tracking
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    # Labor
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    labor_hours = Column(Float, default=0.0)
    
    notes = Column(Text, nullable=True)
    
    production_order = relationship("ProductionOrder", backref="work_orders")
    work_center = relationship("WorkCenter")
    assignee = relationship("User")


# ============ QUALITY CHECK ============

class QCStatus(str, enum.Enum):
    PENDING = "Pending"
    PASSED = "Passed"
    FAILED = "Failed"
    PARTIAL = "Partial Pass"


class QualityCheck(Base):
    """Quality check for production output"""
    __tablename__ = "quality_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=True)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    qc_number = Column(String, nullable=False, index=True)  # QC-YYYYMMDD-001
    check_date = Column(DateTime, nullable=False)
    status = Column(String, default="Pending")  # Pending, Passed, Failed, Partial Pass
    
    # Quantities
    inspected_qty = Column(Float, default=0.0)
    passed_qty = Column(Float, default=0.0)
    failed_qty = Column(Float, default=0.0)
    
    # Inspector
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Results
    notes = Column(Text, nullable=True)
    defect_types = Column(Text, nullable=True)  # JSON array of defect codes
    
    production_order = relationship("ProductionOrder", backref="quality_checks")
    product = relationship("Product")
    inspector = relationship("User")


class QCCheckpoint(Base):
    """Individual checkpoint in a quality inspection"""
    __tablename__ = "qc_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    quality_check_id = Column(UUID(as_uuid=True), ForeignKey("quality_checks.id"), nullable=False)
    
    checkpoint_name = Column(String, nullable=False)  # e.g. "Visual Inspection", "Weight Check"
    specification = Column(String, nullable=True)  # Expected value/range
    actual_value = Column(String, nullable=True)  # Measured value
    passed = Column(Boolean, nullable=True)  # null=not checked, true=pass, false=fail
    notes = Column(Text, nullable=True)
    
    quality_check = relationship("QualityCheck", backref="checkpoints")

