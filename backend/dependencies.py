from fastapi import Depends, HTTPException, Header
from typing import Optional
from auth import get_current_user
from schemas import UserResponse

async def get_current_tenant_id(
    current_user: UserResponse = Depends(get_current_user)
) -> str:
    """
    Extracts tenant_id from the authenticated user's token.
    Enforces that a user belongs to a tenant.
    """
    if not current_user.tenant_id:
        # Fallback for SuperAdmin or initial setup, or return None
        # For SaaS strict mode, maybe raise 403.
        return None 
    return str(current_user.tenant_id)

async def verify_tenant_access(
    tenant_id: str = Depends(get_current_tenant_id)
):
    if not tenant_id:
         raise HTTPException(status_code=403, detail="Tenant context required")
    return tenant_id
