import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    receive_date = Column(DateTime, default=datetime.utcnow)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    # Ideally we would have lines here linking to PO Lines and Batches, 
    # but for simplicity we rely on the created batches to track what came in.

class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_number = Column(String, nullable=False, index=True)
    quantity_on_hand = Column(Float, default=0.0)
    expiration_date = Column(DateTime, nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    
    # Traceability back to GR
    goods_receipt_id = Column(UUID(as_uuid=True), ForeignKey("goods_receipts.id"), nullable=True)

    product = relationship("Product")
    location = relationship("Location")
    goods_receipt = relationship("GoodsReceipt")
