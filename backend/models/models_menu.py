"""
Menu and Permission models for role-based menu access control
"""

import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Menu(Base):
    """
    Menu items stored in database.
    Supports nested menus via parent_id.
    """
    __tablename__ = "menus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)  # e.g. 'dashboard', 'manufacturing'
    label = Column(String, nullable=False)
    icon = Column(String, nullable=True)  # e.g. 'i-heroicons-home'
    path = Column(String, nullable=True)  # e.g. '/manufacturing' or None for parent menu
    parent_id = Column(UUID(as_uuid=True), ForeignKey("menus.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    children = relationship("Menu", back_populates="parent", remote_side=[id])
    parent = relationship("Menu", back_populates="children", remote_side=[parent_id])
    permissions = relationship("RoleMenuPermission", back_populates="menu", cascade="all, delete-orphan")


class RoleMenuPermission(Base):
    """
    Defines which roles can access which menus per tenant.
    If no permission record exists, default behavior applies.
    """
    __tablename__ = "role_menu_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'admin', 'manager', 'production', etc.
    menu_id = Column(UUID(as_uuid=True), ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    can_access = Column(Boolean, default=True)
    
    # Relationships
    menu = relationship("Menu", back_populates="permissions")
