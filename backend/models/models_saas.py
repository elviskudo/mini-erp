from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum
import random
import string
from database import Base


class SubscriptionTier(str, enum.Enum):
    MAKER = "MAKER"           # $49/mo
    GROWTH = "GROWTH"         # $149/mo
    ENTERPRISE = "ENTERPRISE" # $499/mo
    FREE_TRIAL = "FREE_TRIAL"


class MemberRole(str, enum.Enum):
    OWNER = "owner"       # Full access, can delete company
    ADMIN = "admin"       # Full access except delete company
    MEMBER = "member"     # Standard access
    PENDING = "pending"   # Requested to join, waiting approval


def generate_company_code():
    """Generate unique 6-character company code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=True)  # e.g. "acme" for acme.minierp.com
    company_code = Column(String(6), unique=True, index=True, default=generate_company_code)  # For "Find Company" flow
    
    # Subscription
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE_TRIAL)
    subscription_status = Column(String, default="active")  # active, past_due, canceled
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    
    # Localization
    currency = Column(String, default="USD")  # USD, EUR, IDR
    timezone = Column(String, default="UTC")  # UTC, Asia/Jakarta
    
    # Logo & branding
    logo_url = Column(String, nullable=True)
    
    # Setup completion status
    is_setup_complete = Column(Boolean, default=False)  # False until initial config wizard is completed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    members = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")


class TenantMember(Base):
    """
    User-Tenant relationship table with roles.
    Allows a user to belong to multiple tenants with different roles.
    """
    __tablename__ = "tenant_members"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_member'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER, nullable=False)
    
    # Invitation tracking
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow)
    joined_at = Column(DateTime, nullable=True)  # Null until approved
    
    # Relationships
    tenant = relationship("Tenant", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
