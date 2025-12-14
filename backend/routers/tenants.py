from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
import database
from models.models_saas import Tenant, SubscriptionTier

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"]
)

# Pydantic Schemas
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    domain: Optional[str] = Field(None, min_length=2, max_length=50)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC")

class TenantResponse(BaseModel):
    id: UUID
    name: str
    domain: Optional[str]
    tier: SubscriptionTier
    currency: str
    timezone: str

    class Config:
        from_attributes = True

class TenantListResponse(BaseModel):
    id: UUID
    name: str
    domain: Optional[str]

    class Config:
        from_attributes = True

# Endpoints
@router.get("/", response_model=List[TenantListResponse])
async def list_tenants(db: AsyncSession = Depends(database.get_db)):
    """List all available tenants for registration selection"""
    result = await db.execute(select(Tenant).order_by(Tenant.name))
    tenants = result.scalars().all()
    return tenants

@router.post("/", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, db: AsyncSession = Depends(database.get_db)):
    """Create a new tenant (company/organization)"""
    # Check if domain already exists
    if tenant.domain:
        existing = await db.execute(
            select(Tenant).where(Tenant.domain == tenant.domain)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain already in use")
    
    new_tenant = Tenant(
        name=tenant.name,
        domain=tenant.domain,
        currency=tenant.currency,
        timezone=tenant.timezone,
        tier=SubscriptionTier.FREE_TRIAL
    )
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)
    return new_tenant

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: UUID, db: AsyncSession = Depends(database.get_db)):
    """Get tenant details by ID"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
