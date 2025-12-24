"""
Approval Models - Multi-level approval workflow
"""
import uuid
import enum
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class EntityType(str, enum.Enum):
    PURCHASE_ORDER = "PurchaseOrder"
    PURCHASE_REQUEST = "PurchaseRequest"
    PAYMENT = "Payment"
    EXPENSE = "Expense"


class ApprovalLevel(Base):
    """Defines approval levels based on amount thresholds"""
    __tablename__ = "approval_levels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    level = Column(Integer, nullable=False)  # 1, 2, 3, 4
    name = Column(String, nullable=False)  # "Supervisor", "Manager", etc.
    min_amount = Column(Float, default=0.0)  # Minimum amount for this level
    max_amount = Column(Float, nullable=True)  # Maximum amount (null = unlimited)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)  # Required role
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class ApprovalHistory(Base):
    """Tracks approval decisions for entities"""
    __tablename__ = "approval_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    entity_type = Column(Enum(EntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    level = Column(Integer, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    approver = relationship("User", foreign_keys=[approved_by])


class ApprovalRule(Base):
    """Define which roles can approve requests from which roles"""
    __tablename__ = "approval_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Role that needs approval (e.g., STAFF, FINANCE)
    requester_role = Column(String, nullable=False)
    
    # Role that can approve (e.g., MANAGER, FINANCE)
    approver_role = Column(String, nullable=False)
    
    # Description for the rule
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
