from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum
from database import Base

class SubscriptionTier(str, enum.Enum):
    MAKER = "MAKER"       # $49/mo
    GROWTH = "GROWTH"     # $149/mo
    ENTERPRISE = "ENTERPRISE" # $499/mo
    FREE_TRIAL = "FREE_TRIAL"

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=True) # e.g. "acme" for acme.minierp.com
    
    # Subscription
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE_TRIAL)
    subscription_status = Column(String, default="active") # active, past_due, canceled
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    
    # Localization
    currency = Column(String, default="USD") # USD, EUR, IDR
    timezone = Column(String, default="UTC") # UTC, Asia/Jakarta
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="tenant")
