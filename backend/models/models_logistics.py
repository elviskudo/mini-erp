"""
Logistics Models - Stock Transfers, Shipments, Returns, Couriers
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Enum, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


# ===================== ENUMS =====================

class TransferStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In Transit"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ShipmentStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    ISSUE = "Issue"
    RETURNED = "Returned"


class ReturnType(str, enum.Enum):
    SALES = "Sales"
    PURCHASE = "Purchase"


class ReturnStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In Transit"
    PROCESSED = "Processed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ItemCondition(str, enum.Enum):
    GOOD = "Good"
    DAMAGED = "Damaged"
    DEFECTIVE = "Defective"


# ===================== COURIER =====================

class Courier(Base):
    """Courier/Shipping provider master data"""
    __tablename__ = "couriers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Contact info
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Service details
    service_types = Column(String(200), nullable=True)  # e.g., "Regular,Express,Same Day"
    default_service = Column(String(50), default="Regular")
    standard_lead_days = Column(Integer, default=3)  # Days for standard delivery
    express_lead_days = Column(Integer, default=1)
    
    # Pricing
    base_cost = Column(Float, default=0)
    cost_per_kg = Column(Float, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shipments = relationship("Shipment", back_populates="courier")


# ===================== STOCK TRANSFER =====================

class StockTransfer(Base):
    """Internal stock movement between warehouses"""
    __tablename__ = "stock_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    transfer_number = Column(String(50), nullable=False, index=True)
    
    from_warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    transfer_date = Column(DateTime, default=datetime.utcnow)
    transfer_type = Column(String(50), default="Standard")  # Standard, Urgent, Rebalancing
    status = Column(Enum(TransferStatus), default=TransferStatus.PENDING)
    
    notes = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    items = relationship("StockTransferItem", back_populates="transfer", cascade="all, delete-orphan")


class StockTransferItem(Base):
    """Line items for stock transfer"""
    __tablename__ = "stock_transfer_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    transfer_id = Column(UUID(as_uuid=True), ForeignKey("stock_transfers.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    
    # Relationships
    transfer = relationship("StockTransfer", back_populates="items")
    product = relationship("Product")


# ===================== SHIPMENT =====================

class Shipment(Base):
    """Outbound shipment tracking"""
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    shipment_number = Column(String(50), nullable=False, index=True)
    
    # Link to delivery order
    delivery_order_id = Column(UUID(as_uuid=True), ForeignKey("delivery_orders.id"), nullable=True)
    
    # Courier info
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id"), nullable=True)
    service_type = Column(String(50), default="Regular")
    tracking_number = Column(String(100), nullable=True)
    
    # Dates
    ship_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    
    # Costs
    shipping_cost = Column(Float, default=0)
    weight_kg = Column(Float, nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    delivery_order = relationship("DeliveryOrder")
    courier = relationship("Courier", back_populates="shipments")


# ===================== RETURNS =====================

class Return(Base):
    """Return management for sales and purchase returns"""
    __tablename__ = "returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    return_number = Column(String(50), nullable=False, index=True)
    
    return_type = Column(Enum(ReturnType), nullable=False)
    
    # For sales returns
    customer_name = Column(String(200), nullable=True)
    so_reference = Column(String(100), nullable=True)  # Sales Order reference
    do_reference = Column(String(100), nullable=True)  # Delivery Order reference
    
    # For purchase returns
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    po_reference = Column(String(100), nullable=True)  # PO reference
    grn_reference = Column(String(100), nullable=True)  # GRN reference
    
    reason = Column(String(100), nullable=False)
    return_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ReturnStatus), default=ReturnStatus.PENDING)
    
    notes = Column(Text, nullable=True)
    
    shipped_at = Column(DateTime, nullable=True)  # For purchase returns
    processed_at = Column(DateTime, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor")
    items = relationship("ReturnItem", back_populates="return_order", cascade="all, delete-orphan")


class ReturnItem(Base):
    """Line items for returns"""
    __tablename__ = "return_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    return_id = Column(UUID(as_uuid=True), ForeignKey("returns.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    condition = Column(Enum(ItemCondition), default=ItemCondition.GOOD)
    
    # Relationships
    return_order = relationship("Return", back_populates="items")
    product = relationship("Product")


# ===================== PICKING =====================

class PickingStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class PickingList(Base):
    """Picking list for warehouse"""
    __tablename__ = "picking_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    pick_number = Column(String(50), nullable=False, index=True)
    
    # Link to SO or DO
    so_number = Column(String(100), nullable=True)
    delivery_order_id = Column(UUID(as_uuid=True), ForeignKey("delivery_orders.id"), nullable=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    
    priority = Column(String(20), default="Normal")  # Normal, High, Urgent
    status = Column(Enum(PickingStatus), default=PickingStatus.PENDING)
    
    picker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    picker = relationship("User")
    warehouse = relationship("Warehouse")
    items = relationship("PickingItem", back_populates="picking_list", cascade="all, delete-orphan")


class PickingItem(Base):
    """Line items for picking"""
    __tablename__ = "picking_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    picking_list_id = Column(UUID(as_uuid=True), ForeignKey("picking_lists.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=True)
    
    location_code = Column(String(50), nullable=True)
    quantity = Column(Float, nullable=False)
    picked_quantity = Column(Float, default=0)
    
    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    product = relationship("Product")
    batch = relationship("InventoryBatch")
