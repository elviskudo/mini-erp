"""
Settings Models - TenantSettings and PaymentGateway
"""
import uuid
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class GatewayType(str, enum.Enum):
    STRIPE = "Stripe"
    MIDTRANS = "Midtrans"
    XENDIT = "Xendit"
    PAYPAL = "PayPal"
    MANUAL = "Manual"


class TenantSettings(Base):
    """Tenant-specific settings including currency and regional preferences"""
    __tablename__ = "tenant_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Company Info
    company_name = Column(String, nullable=True)
    company_logo_url = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    # Currency Settings
    currency_code = Column(String(3), default="IDR")  # ISO 4217 code
    currency_symbol = Column(String(10), default="Rp")
    currency_position = Column(String(10), default="before")  # "before" or "after"
    decimal_separator = Column(String(1), default=",")
    thousand_separator = Column(String(1), default=".")
    decimal_places = Column(String(1), default="0")  # 0, 2, etc.
    
    # Regional Settings
    timezone = Column(String, default="Asia/Jakarta")
    date_format = Column(String, default="DD/MM/YYYY")
    
    # Setup Status
    setup_complete = Column(Boolean, default=False)


class PaymentGateway(Base):
    """Payment gateway configurations per tenant"""
    __tablename__ = "payment_gateways"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False)  # Custom name like "Stripe Production"
    gateway_type = Column(Enum(GatewayType), default=GatewayType.MANUAL)
    
    # API Credentials (should be encrypted in production)
    api_key = Column(Text, nullable=True)
    api_secret = Column(Text, nullable=True)
    webhook_secret = Column(Text, nullable=True)
    
    # Additional options
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False)  # Test mode
    
    notes = Column(Text, nullable=True)


class StorageType(str, enum.Enum):
    LOCAL = "Local"
    CLOUDINARY = "Cloudinary"
    AWS_S3 = "AWS S3"
    GOOGLE_CLOUD = "Google Cloud Storage"
    AZURE_BLOB = "Azure Blob Storage"


class StorageProvider(Base):
    """Cloud storage provider configurations per tenant"""
    __tablename__ = "storage_providers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False)  # Custom name like "Main Cloud Storage"
    storage_type = Column(Enum(StorageType), default=StorageType.LOCAL)
    
    # Common Settings
    bucket_name = Column(String, nullable=True)  # S3 bucket / Cloudinary cloud name
    region = Column(String, nullable=True)  # AWS region, etc.
    base_url = Column(String, nullable=True)  # Custom CDN URL
    
    # API Credentials
    api_key = Column(Text, nullable=True)  # Access key / API key
    api_secret = Column(Text, nullable=True)  # Secret key / API secret
    
    # Cloudinary specific
    cloud_name = Column(String, nullable=True)
    
    # AWS S3 specific
    access_key_id = Column(String, nullable=True)
    secret_access_key = Column(Text, nullable=True)
    
    # Options
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Use as primary storage
    
    notes = Column(Text, nullable=True)

