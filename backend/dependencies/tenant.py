"""
Tenant Dependency Injection - "Iron Wall" Middleware

This module provides FastAPI dependencies for tenant isolation:
1. get_current_tenant - Validates X-Tenant-ID header and user membership
2. require_tenant - Same as above but raises 403 if no tenant

Usage in routers:
    @router.get("/products")
    async def get_products(
        tenant: Tenant = Depends(require_tenant),
        db: AsyncSession = Depends(get_db)
    ):
        # All queries must filter by tenant.id
        result = await db.execute(
            select(Product).where(Product.tenant_id == tenant.id)
        )
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

import database
from auth import get_current_user
from models.user import User
from models.models_saas import Tenant, TenantMember, MemberRole
from models.base import set_current_tenant, clear_current_tenant


async def get_tenant_from_header(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
) -> Tenant | None:
    """
    Get tenant from X-Tenant-ID header and validate user membership.
    Returns None if no tenant header is provided.
    """
    tenant_id_str = request.headers.get("X-Tenant-ID")
    
    if not tenant_id_str:
        # No tenant header - check if user has a default tenant
        if current_user.tenant_id:
            result = await db.execute(
                select(Tenant).where(Tenant.id == current_user.tenant_id)
            )
            tenant = result.scalar_one_or_none()
            if tenant:
                set_current_tenant(tenant.id)
                return tenant
        return None
    
    try:
        tenant_id = uuid.UUID(tenant_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format"
        )
    
    # Validate tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Validate user is member of this tenant
    result = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == current_user.id,
            TenantMember.role.in_([MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER])
        )
    )
    membership = result.scalar_one_or_none()
    
    # Allow if user is member OR if user's default tenant matches
    if not membership and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this tenant"
        )
    
    # Set current tenant context for auto-injection
    set_current_tenant(tenant.id)
    
    return tenant


async def require_tenant(
    tenant: Tenant | None = Depends(get_tenant_from_header)
) -> Tenant:
    """
    Require a valid tenant to proceed.
    Raises 403 if no tenant context is available.
    """
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required"
        )
    return tenant


async def get_optional_tenant(
    request: Request,
    db: AsyncSession = Depends(database.get_db)
) -> Tenant | None:
    """
    Get tenant from header without requiring authentication.
    Used for public endpoints that need tenant context.
    """
    tenant_id_str = request.headers.get("X-Tenant-ID")
    
    if not tenant_id_str:
        return None
    
    try:
        tenant_id = uuid.UUID(tenant_id_str)
    except ValueError:
        return None
    
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    return result.scalar_one_or_none()


# Cleanup context after request
async def clear_tenant_context():
    """Clear tenant context after request processing"""
    clear_current_tenant()
