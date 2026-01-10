from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime

import database
import models
from models.base import get_current_tenant

# Default tenant for MVP
DEFAULT_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")

def get_tenant_id() -> uuid.UUID:
    """Get current tenant with fallback to default"""
    tenant = get_current_tenant()
    return tenant if tenant else DEFAULT_TENANT_ID

router = APIRouter(
    prefix="/config",
    tags=["Configuration"]
)


# === REGION CONFIG SCHEMAS ===

class RegionConfigCreate(BaseModel):
    code: str
    name: str
    currency_code: str
    currency_symbol: str
    currency_name: Optional[str] = None
    decimal_places: int = 0
    locale: str
    timezone: str
    gmt_offset: str
    gmt_offset_minutes: int = 0
    date_format: str = "DD/MM/YYYY"
    time_format: str = "HH:mm"
    is_active: bool = True
    display_order: int = 0


class RegionConfigResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    currency_code: str
    currency_symbol: str
    currency_name: Optional[str]
    decimal_places: int
    locale: str
    timezone: str
    gmt_offset: str
    gmt_offset_minutes: int
    date_format: str
    time_format: str
    is_active: bool
    display_order: int

    class Config:
        from_attributes = True


# === REGION ENDPOINTS ===

@router.get("/regions", response_model=List[RegionConfigResponse])
async def list_regions(
    active_only: bool = True,
    db: AsyncSession = Depends(database.get_db)
):
    """List all available regions/countries"""
    query = select(models.models_settings.RegionConfig)
    if active_only:
        query = query.where(models.models_settings.RegionConfig.is_active == True)
    query = query.order_by(models.models_settings.RegionConfig.display_order, models.models_settings.RegionConfig.name)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/regions/{code}", response_model=RegionConfigResponse)
async def get_region(
    code: str,
    db: AsyncSession = Depends(database.get_db)
):
    """Get region config by code"""
    result = await db.execute(
        select(models.models_settings.RegionConfig).where(
            models.models_settings.RegionConfig.code == code
        )
    )
    region = result.scalar_one_or_none()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.post("/regions", response_model=RegionConfigResponse)
async def create_region(
    region: RegionConfigCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Create new region config (admin only)"""
    new_region = models.models_settings.RegionConfig(**region.dict())
    db.add(new_region)
    await db.commit()
    await db.refresh(new_region)
    return new_region


@router.put("/regions/{code}", response_model=RegionConfigResponse)
async def update_region(
    code: str,
    region: RegionConfigCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Update region config"""
    result = await db.execute(
        select(models.models_settings.RegionConfig).where(
            models.models_settings.RegionConfig.code == code
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    
    for key, value in region.dict().items():
        setattr(existing, key, value)
    
    await db.commit()
    await db.refresh(existing)
    return existing


# === SEED REGIONS ===

@router.post("/regions/seed")
async def seed_regions(db: AsyncSession = Depends(database.get_db)):
    """Seed default region configurations"""
    
    regions_data = [
        {
            "code": "ID", "name": "Indonesia",
            "currency_code": "IDR", "currency_symbol": "Rp", "currency_name": "Indonesian Rupiah",
            "decimal_places": 0, "locale": "id-ID",
            "timezone": "Asia/Jakarta", "gmt_offset": "GMT+7", "gmt_offset_minutes": 420,
            "date_format": "DD/MM/YYYY", "time_format": "HH:mm",
            "display_order": 1
        },
        {
            "code": "MY", "name": "Malaysia",
            "currency_code": "MYR", "currency_symbol": "RM", "currency_name": "Malaysian Ringgit",
            "decimal_places": 2, "locale": "ms-MY",
            "timezone": "Asia/Kuala_Lumpur", "gmt_offset": "GMT+8", "gmt_offset_minutes": 480,
            "date_format": "DD/MM/YYYY", "time_format": "HH:mm",
            "display_order": 2
        },
        {
            "code": "SG", "name": "Singapore",
            "currency_code": "SGD", "currency_symbol": "S$", "currency_name": "Singapore Dollar",
            "decimal_places": 2, "locale": "en-SG",
            "timezone": "Asia/Singapore", "gmt_offset": "GMT+8", "gmt_offset_minutes": 480,
            "date_format": "DD/MM/YYYY", "time_format": "HH:mm",
            "display_order": 3
        },
        {
            "code": "TH", "name": "Thailand",
            "currency_code": "THB", "currency_symbol": "฿", "currency_name": "Thai Baht",
            "decimal_places": 2, "locale": "th-TH",
            "timezone": "Asia/Bangkok", "gmt_offset": "GMT+7", "gmt_offset_minutes": 420,
            "date_format": "DD/MM/YYYY", "time_format": "HH:mm",
            "display_order": 4
        },
        {
            "code": "PH", "name": "Philippines",
            "currency_code": "PHP", "currency_symbol": "₱", "currency_name": "Philippine Peso",
            "decimal_places": 2, "locale": "en-PH",
            "timezone": "Asia/Manila", "gmt_offset": "GMT+8", "gmt_offset_minutes": 480,
            "date_format": "MM/DD/YYYY", "time_format": "hh:mm A",
            "display_order": 5
        },
        {
            "code": "JP", "name": "Japan",
            "currency_code": "JPY", "currency_symbol": "¥", "currency_name": "Japanese Yen",
            "decimal_places": 0, "locale": "ja-JP",
            "timezone": "Asia/Tokyo", "gmt_offset": "GMT+9", "gmt_offset_minutes": 540,
            "date_format": "YYYY/MM/DD", "time_format": "HH:mm",
            "display_order": 6
        },
        {
            "code": "DE", "name": "Germany (Europe)",
            "currency_code": "EUR", "currency_symbol": "€", "currency_name": "Euro",
            "decimal_places": 2, "locale": "de-DE",
            "timezone": "Europe/Berlin", "gmt_offset": "GMT+1", "gmt_offset_minutes": 60,
            "date_format": "DD.MM.YYYY", "time_format": "HH:mm",
            "display_order": 7
        },
        {
            "code": "GB", "name": "United Kingdom",
            "currency_code": "GBP", "currency_symbol": "£", "currency_name": "British Pound",
            "decimal_places": 2, "locale": "en-GB",
            "timezone": "Europe/London", "gmt_offset": "GMT+0", "gmt_offset_minutes": 0,
            "date_format": "DD/MM/YYYY", "time_format": "HH:mm",
            "display_order": 8
        },
        {
            "code": "US", "name": "United States",
            "currency_code": "USD", "currency_symbol": "$", "currency_name": "US Dollar",
            "decimal_places": 2, "locale": "en-US",
            "timezone": "America/New_York", "gmt_offset": "GMT-5", "gmt_offset_minutes": -300,
            "date_format": "MM/DD/YYYY", "time_format": "hh:mm A",
            "display_order": 9
        },
        {
            "code": "AU", "name": "Australia",
            "currency_code": "AUD", "currency_symbol": "A$", "currency_name": "Australian Dollar",
            "decimal_places": 2, "locale": "en-AU",
            "timezone": "Australia/Sydney", "gmt_offset": "GMT+11", "gmt_offset_minutes": 660,
            "date_format": "DD/MM/YYYY", "time_format": "HH:mm",
            "display_order": 10
        }
    ]
    
    created = 0
    for region_data in regions_data:
        # Check if exists
        existing = await db.execute(
            select(models.models_settings.RegionConfig).where(
                models.models_settings.RegionConfig.code == region_data["code"]
            )
        )
        if not existing.scalar_one_or_none():
            new_region = models.models_settings.RegionConfig(**region_data)
            db.add(new_region)
            created += 1
    
    await db.commit()
    return {"message": f"Seeded {created} regions", "total": len(regions_data)}


# === TENANT SETTINGS ===

class TenantSettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    region_code: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    gmt_offset: Optional[str] = None
    gmt_offset_minutes: Optional[int] = None
    date_format: Optional[str] = None


@router.get("/tenant-settings")
async def get_tenant_settings(db: AsyncSession = Depends(database.get_db)):
    """Get current tenant settings"""
    tenant_id = get_tenant_id()
    
    result = await db.execute(
        select(models.models_settings.TenantSettings).where(
            models.models_settings.TenantSettings.tenant_id == tenant_id
        ).options(selectinload(models.models_settings.TenantSettings.region))
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = models.models_settings.TenantSettings(
            tenant_id=tenant_id,
            region_code="ID",
            currency_code="IDR",
            currency_symbol="Rp",
            locale="id-ID",
            timezone="Asia/Jakarta",
            gmt_offset="GMT+7",
            gmt_offset_minutes=420
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return {
        "id": str(settings.id),
        "company_name": settings.company_name,
        "company_logo_url": settings.company_logo_url,
        "region_code": settings.region_code,
        "currency_code": settings.currency_code,
        "currency_symbol": settings.currency_symbol,
        "locale": settings.locale,
        "timezone": settings.timezone,
        "gmt_offset": settings.gmt_offset,
        "gmt_offset_minutes": settings.gmt_offset_minutes,
        "date_format": settings.date_format,
        "setup_complete": settings.setup_complete
    }


@router.put("/tenant-settings")
async def update_tenant_settings(
    update: TenantSettingsUpdate,
    db: AsyncSession = Depends(database.get_db)
):
    """Update tenant settings"""
    tenant_id = get_tenant_id()
    
    result = await db.execute(
        select(models.models_settings.TenantSettings).where(
            models.models_settings.TenantSettings.tenant_id == tenant_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = models.models_settings.TenantSettings(tenant_id=tenant_id)
        db.add(settings)
    
    # If region_code is set, copy defaults from region
    if update.region_code:
        region_result = await db.execute(
            select(models.models_settings.RegionConfig).where(
                models.models_settings.RegionConfig.code == update.region_code
            )
        )
        region = region_result.scalar_one_or_none()
        if region:
            settings.region_code = region.code
            settings.currency_code = region.currency_code
            settings.currency_symbol = region.currency_symbol
            settings.locale = region.locale
            settings.timezone = region.timezone
            settings.gmt_offset = region.gmt_offset
            settings.gmt_offset_minutes = region.gmt_offset_minutes
            settings.date_format = region.date_format
    
    # Apply any explicit overrides
    for key, value in update.dict(exclude_unset=True).items():
        if key != 'region_code' and value is not None:
            setattr(settings, key, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return {"message": "Settings updated", "settings": {
        "region_code": settings.region_code,
        "currency_code": settings.currency_code,
        "timezone": settings.timezone,
        "gmt_offset": settings.gmt_offset
    }}
