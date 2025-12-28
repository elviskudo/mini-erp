"""
POS Models - Transaction, TransactionLog, Promo for Point of Sale system
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from models.base import TenantMixin


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    QRIS = "QRIS"
    STRIPE = "STRIPE"
    CREDIT = "CREDIT"  # Customer credit balance


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PromoType(str, enum.Enum):
    FIXED = "FIXED"  # Fixed amount discount
    PERCENTAGE = "PERCENTAGE"  # Percentage discount
    FREE_ITEM = "FREE_ITEM"  # Free item promo


class TransactionLogType(str, enum.Enum):
    CREDIT = "CREDIT"  # Add to balance (payment received)
    DEBIT = "DEBIT"  # Subtract from balance (purchase made)


class POSTransaction(Base, TenantMixin):
    """POS Transaction record"""
    __tablename__ = "pos_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer & Cashier
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=True)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Items (stored as JSON array)
    items = Column(JSON, nullable=False, default=list)
    # Format: [{"product_id": "...", "name": "...", "quantity": 1, "unit_price": 10.0, "subtotal": 10.0}]
    
    # Pricing
    subtotal = Column(Float, default=0)
    discount = Column(Float, default=0)
    tax = Column(Float, default=0)
    total = Column(Float, default=0)
    
    # Payment
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.CASH)
    payment_reference = Column(String, nullable=True)  # External payment ID (Stripe, QRIS)
    
    # Promo applied
    promo_id = Column(UUID(as_uuid=True), ForeignKey("pos_promos.id"), nullable=True)
    promo_code = Column(String, nullable=True)
    
    # Status
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.COMPLETED)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", backref="pos_transactions")
    cashier = relationship("User")
    promo = relationship("Promo", backref="transactions")


class TransactionLog(Base, TenantMixin):
    """Customer balance transaction log for credit tracking"""
    __tablename__ = "pos_transaction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=False)
    
    # Related transaction (optional)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("pos_transactions.id"), nullable=True)
    
    # Type and amounts
    log_type = Column(SQLEnum(TransactionLogType), nullable=False)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, default=0)
    balance_after = Column(Float, default=0)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    customer = relationship("Customer", backref="transaction_logs")
    transaction = relationship("POSTransaction", backref="logs")


class Promo(Base, TenantMixin):
    """Promotional offers and discounts"""
    __tablename__ = "pos_promos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Promo info
    code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Type and value
    promo_type = Column(SQLEnum(PromoType), default=PromoType.PERCENTAGE)
    value = Column(Float, default=0)  # Amount or percentage
    
    # Conditions
    min_order = Column(Float, default=0)  # Minimum order amount
    max_discount = Column(Float, nullable=True)  # Maximum discount cap
    
    # Validity
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Usage limits
    usage_limit = Column(Integer, nullable=True)  # Max total uses
    usage_count = Column(Integer, default=0)  # Current usage count
    per_customer_limit = Column(Integer, default=1)  # Max uses per customer
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
