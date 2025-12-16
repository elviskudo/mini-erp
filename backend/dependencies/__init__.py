"""
Dependencies Package - FastAPI Dependency Injection

Exports:
- get_tenant_from_header - Get tenant from X-Tenant-ID header (requires auth)
- require_tenant - Require tenant context (raises 400 if missing)
- get_optional_tenant - Get tenant without requiring auth
- get_current_tenant_id - Simple helper returning just the tenant ID string
"""

from fastapi import Depends, Request
from .tenant import (
    get_tenant_from_header,
    require_tenant,
    get_optional_tenant,
    clear_tenant_context
)


async def get_current_tenant_id(request: Request) -> str | None:
    """
    Simple dependency that returns the tenant ID from X-Tenant-ID header.
    Used by legacy routes that just need the tenant_id string.
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    return tenant_id


__all__ = [
    "get_tenant_from_header",
    "require_tenant", 
    "get_optional_tenant",
    "get_current_tenant_id",
    "clear_tenant_context"
]
