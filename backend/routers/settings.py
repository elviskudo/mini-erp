"""
Settings Router - Manage tenant settings and payment gateways
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import uuid

import database
import models
from models.models_settings import TenantSettings, PaymentGateway, GatewayType, StorageProvider, StorageType
from auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


# ============ Pydantic Schemas ============

class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    industry: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    currency_position: Optional[str] = None
    decimal_separator: Optional[str] = None
    thousand_separator: Optional[str] = None
    decimal_places: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None


class PaymentGatewayCreate(BaseModel):
    name: str
    gateway_type: str = "Manual"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True
    is_sandbox: bool = False
    notes: Optional[str] = None


class PaymentGatewayUpdate(BaseModel):
    name: Optional[str] = None
    gateway_type: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: Optional[bool] = None
    is_sandbox: Optional[bool] = None
    notes: Optional[str] = None


# ============ Settings Endpoints ============

@router.get("")
async def get_settings(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get tenant settings"""
    result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == current_user.tenant_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = TenantSettings(
            tenant_id=current_user.tenant_id,
            currency_code="IDR",
            currency_symbol="Rp",
            currency_position="before",
            decimal_separator=",",
            thousand_separator=".",
            decimal_places="0",
            timezone="Asia/Jakarta",
            date_format="DD/MM/YYYY"
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return {
        "id": str(settings.id),
        "company_name": settings.company_name,
        "company_logo_url": settings.company_logo_url,
        "industry": settings.industry,
        "currency_code": settings.currency_code,
        "currency_symbol": settings.currency_symbol,
        "currency_position": settings.currency_position,
        "decimal_separator": settings.decimal_separator,
        "thousand_separator": settings.thousand_separator,
        "decimal_places": settings.decimal_places,
        "timezone": settings.timezone,
        "date_format": settings.date_format,
        "setup_complete": settings.setup_complete
    }


@router.put("")
async def update_settings(
    data: SettingsUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update tenant settings"""
    result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == current_user.tenant_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = TenantSettings(tenant_id=current_user.tenant_id)
        db.add(settings)
    
    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return {"message": "Settings updated successfully"}


@router.post("/upload-logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Upload company logo and save URL to tenant settings"""
    import os
    from pathlib import Path
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    contents = await file.read()
    
    # Check file size (max 2MB)
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 2MB")
    
    logo_url = None
    
    # Try Cloudinary first if configured
    cloudinary_key = os.getenv("CLOUDINARY_API_KEY")
    if cloudinary_key:
        try:
            from utils.media import upload_media
            result = upload_media(contents, folder="mini_erp_logos")
            if result and result.get("url"):
                logo_url = result["url"]
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
    
    # Fallback to local storage
    if not logo_url:
        try:
            # Save to static folder
            static_dir = Path(__file__).parent.parent / "static" / "logos"
            static_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename using tenant_id
            ext = file.filename.split('.')[-1] if file.filename and '.' in file.filename else 'png'
            filename = f"{current_user.tenant_id}.{ext}"
            filepath = static_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(contents)
            
            # Return relative URL (served by FastAPI static files)
            logo_url = f"/static/logos/{filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save logo: {str(e)}")
    
    if not logo_url:
        raise HTTPException(status_code=500, detail="Failed to upload logo")
    
    # Update tenant settings with logo URL
    db_result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == current_user.tenant_id)
    )
    settings = db_result.scalar_one_or_none()
    
    if not settings:
        settings = TenantSettings(tenant_id=current_user.tenant_id)
        db.add(settings)
    
    settings.company_logo_url = logo_url
    await db.commit()
    
    return {
        "url": logo_url,
        "message": "Logo uploaded successfully"
    }

@router.get("/currency-options")
async def get_currency_options():
    """Get available currency options"""
    return {
        "currencies": [
            {"code": "IDR", "symbol": "Rp", "name": "Indonesian Rupiah"},
            {"code": "USD", "symbol": "$", "name": "US Dollar"},
            {"code": "EUR", "symbol": "€", "name": "Euro"},
            {"code": "GBP", "symbol": "£", "name": "British Pound"},
            {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar"},
            {"code": "MYR", "symbol": "RM", "name": "Malaysian Ringgit"},
            {"code": "JPY", "symbol": "¥", "name": "Japanese Yen"},
            {"code": "CNY", "symbol": "¥", "name": "Chinese Yuan"},
            {"code": "AUD", "symbol": "A$", "name": "Australian Dollar"},
            {"code": "THB", "symbol": "฿", "name": "Thai Baht"}
        ],
        "positions": [
            {"value": "before", "label": "Before amount (e.g. Rp 10.000)"},
            {"value": "after", "label": "After amount (e.g. 10.000 Rp)"}
        ],
        "decimal_separators": [",", "."],
        "thousand_separators": [".", ",", " "],
        "decimal_places": ["0", "2", "3"]
    }


# ============ Payment Gateway Endpoints ============

@router.get("/payment-gateways")
async def list_payment_gateways(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all payment gateways for tenant"""
    result = await db.execute(
        select(PaymentGateway).where(PaymentGateway.tenant_id == current_user.tenant_id)
    )
    gateways = result.scalars().all()
    
    return [
        {
            "id": str(g.id),
            "name": g.name,
            "gateway_type": g.gateway_type.value if g.gateway_type else "Manual",
            "api_key": "****" + g.api_key[-4:] if g.api_key and len(g.api_key) > 4 else "****",
            "api_secret": "****" if g.api_secret else None,
            "webhook_secret": "****" if g.webhook_secret else None,
            "is_active": g.is_active,
            "is_sandbox": g.is_sandbox,
            "notes": g.notes
        }
        for g in gateways
    ]


@router.get("/payment-gateways/{gateway_id}")
async def get_payment_gateway(
    gateway_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific payment gateway (with full credentials for editing)"""
    result = await db.execute(
        select(PaymentGateway).where(
            PaymentGateway.id == uuid.UUID(gateway_id),
            PaymentGateway.tenant_id == current_user.tenant_id
        )
    )
    gateway = result.scalar_one_or_none()
    
    if not gateway:
        raise HTTPException(status_code=404, detail="Payment gateway not found")
    
    return {
        "id": str(gateway.id),
        "name": gateway.name,
        "gateway_type": gateway.gateway_type.value if gateway.gateway_type else "Manual",
        "api_key": gateway.api_key,
        "api_secret": gateway.api_secret,
        "webhook_secret": gateway.webhook_secret,
        "is_active": gateway.is_active,
        "is_sandbox": gateway.is_sandbox,
        "notes": gateway.notes
    }


@router.post("/payment-gateways")
async def create_payment_gateway(
    data: PaymentGatewayCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new payment gateway"""
    try:
        gateway_type = GatewayType(data.gateway_type)
    except ValueError:
        gateway_type = GatewayType.MANUAL
    
    gateway = PaymentGateway(
        tenant_id=current_user.tenant_id,
        name=data.name,
        gateway_type=gateway_type,
        api_key=data.api_key,
        api_secret=data.api_secret,
        webhook_secret=data.webhook_secret,
        is_active=data.is_active,
        is_sandbox=data.is_sandbox,
        notes=data.notes
    )
    
    db.add(gateway)
    await db.commit()
    await db.refresh(gateway)
    
    return {
        "id": str(gateway.id),
        "name": gateway.name,
        "message": "Payment gateway created successfully"
    }


@router.put("/payment-gateways/{gateway_id}")
async def update_payment_gateway(
    gateway_id: str,
    data: PaymentGatewayUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a payment gateway"""
    result = await db.execute(
        select(PaymentGateway).where(
            PaymentGateway.id == uuid.UUID(gateway_id),
            PaymentGateway.tenant_id == current_user.tenant_id
        )
    )
    gateway = result.scalar_one_or_none()
    
    if not gateway:
        raise HTTPException(status_code=404, detail="Payment gateway not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "gateway_type" and value:
            try:
                value = GatewayType(value)
            except ValueError:
                value = GatewayType.MANUAL
        if value is not None:
            setattr(gateway, field, value)
    
    await db.commit()
    
    return {"message": "Payment gateway updated successfully"}


@router.delete("/payment-gateways/{gateway_id}")
async def delete_payment_gateway(
    gateway_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a payment gateway"""
    result = await db.execute(
        select(PaymentGateway).where(
            PaymentGateway.id == uuid.UUID(gateway_id),
            PaymentGateway.tenant_id == current_user.tenant_id
        )
    )
    gateway = result.scalar_one_or_none()
    
    if not gateway:
        raise HTTPException(status_code=404, detail="Payment gateway not found")
    
    await db.delete(gateway)
    await db.commit()
    
    return {"message": "Payment gateway deleted successfully"}


@router.get("/gateway-types")
async def get_gateway_types():
    """Get available payment gateway types"""
    return [
        {"value": "Stripe", "label": "Stripe", "description": "International payments"},
        {"value": "Midtrans", "label": "Midtrans", "description": "Indonesian payment gateway"},
        {"value": "Xendit", "label": "Xendit", "description": "Southeast Asia payments"},
        {"value": "PayPal", "label": "PayPal", "description": "Global payments"},
        {"value": "Manual", "label": "Manual", "description": "Manual bank transfer"}
    ]


# ============ Storage Provider Schemas ============

class StorageProviderCreate(BaseModel):
    name: str
    storage_type: str = "Local"
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    cloud_name: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    notes: Optional[str] = None


class StorageProviderUpdate(BaseModel):
    name: Optional[str] = None
    storage_type: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    cloud_name: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    notes: Optional[str] = None


# ============ Storage Provider Endpoints ============

@router.get("/storage-providers")
async def list_storage_providers(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all storage providers for tenant"""
    result = await db.execute(
        select(StorageProvider).where(StorageProvider.tenant_id == current_user.tenant_id)
    )
    providers = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "storage_type": p.storage_type.value if p.storage_type else "Local",
            "bucket_name": p.bucket_name,
            "region": p.region,
            "base_url": p.base_url,
            "api_key": "****" + p.api_key[-4:] if p.api_key and len(p.api_key) > 4 else ("****" if p.api_key else None),
            "cloud_name": p.cloud_name,
            "is_active": p.is_active,
            "is_default": p.is_default,
            "notes": p.notes
        }
        for p in providers
    ]


@router.get("/storage-providers/{provider_id}")
async def get_storage_provider(
    provider_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific storage provider (with full credentials for editing)"""
    result = await db.execute(
        select(StorageProvider).where(
            StorageProvider.id == uuid.UUID(provider_id),
            StorageProvider.tenant_id == current_user.tenant_id
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    
    return {
        "id": str(provider.id),
        "name": provider.name,
        "storage_type": provider.storage_type.value if provider.storage_type else "Local",
        "bucket_name": provider.bucket_name,
        "region": provider.region,
        "base_url": provider.base_url,
        "api_key": provider.api_key,
        "api_secret": provider.api_secret,
        "cloud_name": provider.cloud_name,
        "access_key_id": provider.access_key_id,
        "secret_access_key": provider.secret_access_key,
        "is_active": provider.is_active,
        "is_default": provider.is_default,
        "notes": provider.notes
    }


@router.post("/storage-providers")
async def create_storage_provider(
    data: StorageProviderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new storage provider"""
    try:
        storage_type = StorageType(data.storage_type)
    except ValueError:
        storage_type = StorageType.LOCAL
    
    # If setting as default, unset other defaults
    if data.is_default:
        await db.execute(
            select(StorageProvider).where(
                StorageProvider.tenant_id == current_user.tenant_id,
                StorageProvider.is_default == True
            )
        )
        result = await db.execute(
            select(StorageProvider).where(
                StorageProvider.tenant_id == current_user.tenant_id,
                StorageProvider.is_default == True
            )
        )
        for p in result.scalars().all():
            p.is_default = False
    
    provider = StorageProvider(
        tenant_id=current_user.tenant_id,
        name=data.name,
        storage_type=storage_type,
        bucket_name=data.bucket_name,
        region=data.region,
        base_url=data.base_url,
        api_key=data.api_key,
        api_secret=data.api_secret,
        cloud_name=data.cloud_name,
        access_key_id=data.access_key_id,
        secret_access_key=data.secret_access_key,
        is_active=data.is_active,
        is_default=data.is_default,
        notes=data.notes
    )
    
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    
    return {
        "id": str(provider.id),
        "name": provider.name,
        "message": "Storage provider created successfully"
    }


@router.put("/storage-providers/{provider_id}")
async def update_storage_provider(
    provider_id: str,
    data: StorageProviderUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a storage provider"""
    result = await db.execute(
        select(StorageProvider).where(
            StorageProvider.id == uuid.UUID(provider_id),
            StorageProvider.tenant_id == current_user.tenant_id
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        result2 = await db.execute(
            select(StorageProvider).where(
                StorageProvider.tenant_id == current_user.tenant_id,
                StorageProvider.is_default == True,
                StorageProvider.id != uuid.UUID(provider_id)
            )
        )
        for p in result2.scalars().all():
            p.is_default = False
    
    for field, value in update_data.items():
        if field == "storage_type" and value:
            try:
                value = StorageType(value)
            except ValueError:
                value = StorageType.LOCAL
        if value is not None:
            setattr(provider, field, value)
    
    await db.commit()
    
    return {"message": "Storage provider updated successfully"}


@router.delete("/storage-providers/{provider_id}")
async def delete_storage_provider(
    provider_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a storage provider"""
    result = await db.execute(
        select(StorageProvider).where(
            StorageProvider.id == uuid.UUID(provider_id),
            StorageProvider.tenant_id == current_user.tenant_id
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    
    await db.delete(provider)
    await db.commit()
    
    return {"message": "Storage provider deleted successfully"}


@router.get("/storage-types")
async def get_storage_types():
    """Get available storage provider types"""
    return [
        {"value": "Local", "label": "Local Storage", "description": "Store files locally on server"},
        {"value": "Cloudinary", "label": "Cloudinary", "description": "Cloud-based image and video management"},
        {"value": "AWS S3", "label": "AWS S3", "description": "Amazon Simple Storage Service"},
        {"value": "Google Cloud Storage", "label": "Google Cloud Storage", "description": "Google Cloud object storage"},
        {"value": "Azure Blob Storage", "label": "Azure Blob", "description": "Microsoft Azure Blob Storage"}
    ]


@router.get("/storage-env")
async def get_storage_from_env():
    """Get storage configuration from environment variables"""
    import os
    
    providers = []
    
    # Check Cloudinary
    cloudinary_key = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    if cloudinary_key and cloudinary_name:
        providers.append({
            "storage_type": "Cloudinary",
            "name": "Cloudinary (from env)",
            "cloud_name": cloudinary_name,
            "api_key": cloudinary_key,
            "api_secret": os.getenv("CLOUDINARY_API_SECRET", ""),
            "is_active": True,
            "is_default": True,
            "from_env": True
        })
    
    # Check AWS S3
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_bucket = os.getenv("AWS_S3_BUCKET")
    if aws_key and aws_bucket:
        providers.append({
            "storage_type": "AWS S3",
            "name": "AWS S3 (from env)",
            "bucket_name": aws_bucket,
            "region": os.getenv("AWS_S3_REGION", "us-east-1"),
            "access_key_id": aws_key,
            "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "is_active": True,
            "from_env": True
        })
    
    return providers


@router.post("/storage-sync-env")
async def sync_storage_from_env(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Sync storage providers from environment variables to database"""
    import os
    
    created = []
    
    # Check Cloudinary
    cloudinary_key = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    if cloudinary_key and cloudinary_name:
        # Check if already exists
        result = await db.execute(
            select(StorageProvider).where(
                StorageProvider.tenant_id == current_user.tenant_id,
                StorageProvider.storage_type == StorageType.CLOUDINARY
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            provider = StorageProvider(
                tenant_id=current_user.tenant_id,
                name="Cloudinary",
                storage_type=StorageType.CLOUDINARY,
                cloud_name=cloudinary_name,
                api_key=cloudinary_key,
                api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
                is_active=True,
                is_default=True,
                notes="Auto-configured from environment variables"
            )
            db.add(provider)
            created.append("Cloudinary")
    
    if created:
        await db.commit()
    
    return {"synced": created, "message": f"Synced {len(created)} storage providers from environment"}


# ============ Warehouse Settings ============

@router.get("/warehouse")
async def get_warehouse_settings(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get default warehouse settings for tenant"""
    from models.models_inventory import Warehouse
    
    # Get first warehouse for tenant
    result = await db.execute(
        select(Warehouse).where(Warehouse.tenant_id == current_user.tenant_id).limit(1)
    )
    warehouse = result.scalar_one_or_none()
    
    if warehouse:
        return {
            "id": str(warehouse.id),
            "name": warehouse.name,
            "code": warehouse.code,
            "address": warehouse.address
        }
    
    return None


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None


@router.put("/warehouse")
async def update_warehouse_settings(
    data: WarehouseUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update default warehouse settings"""
    from models.models_inventory import Warehouse
    
    # Get first warehouse for tenant
    result = await db.execute(
        select(Warehouse).where(Warehouse.tenant_id == current_user.tenant_id).limit(1)
    )
    warehouse = result.scalar_one_or_none()
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="No warehouse found")
    
    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(warehouse, field, value)
    
    await db.commit()
    
    return {"message": "Warehouse updated successfully"}


# ============ Approval Rules Endpoints ============

class ApprovalRuleCreate(BaseModel):
    requester_role: str
    approver_role: str
    description: Optional[str] = None

@router.get("/approval-rules")
async def list_approval_rules(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all approval rules for the tenant"""
    from models.models_approval import ApprovalRule
    
    query = select(ApprovalRule).where(ApprovalRule.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [{
        "id": str(r.id),
        "requester_role": r.requester_role,
        "approver_role": r.approver_role,
        "description": r.description,
        "created_at": r.created_at.isoformat() if r.created_at else None
    } for r in rules]

@router.post("/approval-rules")
async def create_approval_rule(
    data: ApprovalRuleCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new approval rule"""
    from models.models_approval import ApprovalRule
    
    rule = ApprovalRule(
        tenant_id=current_user.tenant_id,
        requester_role=data.requester_role,
        approver_role=data.approver_role,
        description=data.description
    )
    db.add(rule)
    await db.commit()
    
    return {"id": str(rule.id), "message": "Approval rule created"}

@router.delete("/approval-rules/{rule_id}")
async def delete_approval_rule(
    rule_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an approval rule"""
    from models.models_approval import ApprovalRule
    import uuid
    
    rule = await db.get(ApprovalRule, uuid.UUID(rule_id))
    if not rule or rule.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    
    return {"message": "Approval rule deleted"}

@router.get("/roles")
async def list_roles():
    """Get available user roles"""
    return [
        {"value": "ADMIN", "label": "Admin"},
        {"value": "MANAGER", "label": "Manager"},
        {"value": "STAFF", "label": "Staff"},
        {"value": "FINANCE", "label": "Finance"},
        {"value": "PROCUREMENT", "label": "Procurement"},
        {"value": "WAREHOUSE", "label": "Warehouse"},
        {"value": "PRODUCTION", "label": "Production"},
        {"value": "HR", "label": "HR"},
        {"value": "LAB_TECH", "label": "Lab Tech"}
    ]
