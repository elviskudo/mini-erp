"""
Settings Models - TenantSettings, RegionConfig, and PaymentGateway
"""
import uuid
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class GatewayType(str, enum.Enum):
    STRIPE = "Stripe"
    MIDTRANS = "Midtrans"
    XENDIT = "Xendit"
    PAYPAL = "PayPal"
    MANUAL = "Manual"


class RegionConfig(Base):
    """Master table for region/country configuration"""
    __tablename__ = "region_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Region identification
    code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., "ID", "MY", "SG"
    name = Column(String(100), nullable=False)  # e.g., "Indonesia", "Malaysia"
    
    # Currency settings
    currency_code = Column(String(3), nullable=False)  # ISO 4217: IDR, MYR, SGD, etc.
    currency_symbol = Column(String(10), nullable=False)  # Rp, RM, S$, ฿, ₱, ¥, €, $, £
    currency_name = Column(String(50), nullable=True)  # Indonesian Rupiah, etc.
    decimal_places = Column(Integer, default=0)  # 0 for IDR/JPY, 2 for USD/EUR
    
    # Locale settings
    locale = Column(String(10), nullable=False)  # id-ID, ms-MY, en-SG, etc.
    
    # Timezone settings
    timezone = Column(String(50), nullable=False)  # Asia/Jakarta, Asia/Kuala_Lumpur, etc.
    gmt_offset = Column(String(10), nullable=False)  # GMT+7, GMT+8, GMT+9, etc.
    gmt_offset_minutes = Column(Integer, default=0)  # 420 for GMT+7, 480 for GMT+8, etc.
    
    # Date/Time format preferences
    date_format = Column(String(20), default="DD/MM/YYYY")
    time_format = Column(String(10), default="HH:mm")  # 24-hour format
    
    # Status
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)


class TenantSettings(Base):
    """Tenant-specific settings including currency and regional preferences"""
    __tablename__ = "tenant_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Company Info
    company_name = Column(String, nullable=True)
    company_logo_url = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    # Region Settings (link to master or custom values)
    region_code = Column(String(10), ForeignKey("region_configs.code"), nullable=True)
    region = relationship("RegionConfig")
    
    # Currency Settings (can override region defaults)
    currency_code = Column(String(3), default="IDR")  # ISO 4217 code
    currency_symbol = Column(String(10), default="Rp")
    currency_position = Column(String(10), default="before")  # "before" or "after"
    decimal_separator = Column(String(1), default=",")
    thousand_separator = Column(String(1), default=".")
    decimal_places = Column(String(1), default="0")  # 0, 2, etc.
    
    # Regional Settings
    locale = Column(String(10), default="id-ID")  # Locale code
    timezone = Column(String, default="Asia/Jakarta")
    gmt_offset = Column(String(10), default="GMT+7")  # GMT offset for display
    gmt_offset_minutes = Column(Integer, default=420)  # Offset in minutes for calculations
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

