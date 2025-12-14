"""
TenantMixin - Base class for multi-tenant models

All functional tables (Products, Orders, GL_Entries, etc.) 
should inherit from TenantMixin to automatically have tenant_id column.
"""

import uuid
from sqlalchemy import Column, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID
from contextvars import ContextVar

# Context variable to hold current tenant_id
current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar('current_tenant_id', default=None)


class TenantMixin:
    """
    Mixin that adds tenant_id column to models.
    
    Usage:
        class Product(TenantMixin, Base):
            __tablename__ = "products"
            ...
    """
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id"), 
        nullable=False,
        index=True
    )


def set_current_tenant(tenant_id: uuid.UUID):
    """Set the current tenant context for auto-injection"""
    current_tenant_id.set(tenant_id)


def get_current_tenant() -> uuid.UUID | None:
    """Get the current tenant context"""
    return current_tenant_id.get()


def clear_current_tenant():
    """Clear the current tenant context"""
    current_tenant_id.set(None)


def auto_set_tenant_id(mapper, connection, target):
    """
    SQLAlchemy event listener to auto-set tenant_id on insert.
    Called before insert on any model with TenantMixin.
    """
    if hasattr(target, 'tenant_id') and target.tenant_id is None:
        tenant_id = get_current_tenant()
        if tenant_id:
            target.tenant_id = tenant_id


def setup_tenant_listeners(model_class):
    """
    Setup event listener for a model class to auto-inject tenant_id.
    Call this for each model that uses TenantMixin.
    """
    event.listen(model_class, 'before_insert', auto_set_tenant_id)
