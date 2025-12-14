import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
from database import Base


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    OPERATOR = "Operator"
    LAB_TECH = "Lab_Tech"
    MANAGER = "Manager"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    
    # Email verification
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Default tenant (for backward compatibility)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    tenant = relationship("Tenant", back_populates="users")
    
    # Multi-tenant memberships
    memberships = relationship("TenantMember", back_populates="user", 
                               foreign_keys="TenantMember.user_id",
                               cascade="all, delete-orphan")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
