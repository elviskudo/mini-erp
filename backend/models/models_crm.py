"""
CRM Models - Leads, Opportunities, Activities, Notes, Sales Orders
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from models.base import TenantMixin
import uuid
from database import Base
from datetime import datetime
import enum


# ==================== ENUMS ====================

class LeadSource(str, enum.Enum):
    WEBSITE = "Website"
    EXPO = "Expo"
    REFERRAL = "Referral"
    COLD_CALL = "Cold Call"
    SOCIAL_MEDIA = "Social Media"
    ADVERTISEMENT = "Advertisement"
    EMAIL_CAMPAIGN = "Email Campaign"
    PARTNER = "Partner"
    OTHER = "Other"


class LeadStatus(str, enum.Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    CONVERTED = "Converted"
    LOST = "Lost"


class OpportunityStage(str, enum.Enum):
    QUALIFICATION = "Qualification"
    NEEDS_ANALYSIS = "Needs Analysis"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class ActivityType(str, enum.Enum):
    CALL = "Call"
    EMAIL = "Email"
    MEETING = "Meeting"
    TASK = "Task"
    FOLLOW_UP = "Follow Up"
    DEMO = "Demo"
    REMINDER = "Reminder"


class ActivityStatus(str, enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class SOStatus:
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    SHIPPED = "Shipped"
    CANCELLED = "Cancelled"


class OrderSource:
    MANUAL = "Manual"
    WEB = "Web"
    API = "API"


# ==================== MODELS ====================

class Lead(Base, TenantMixin):
    """Lead/Prospek - kontak awal sebelum jadi customer"""
    __tablename__ = "crm_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Info
    name = Column(String, nullable=False, index=True)
    company = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Source & Status
    source = Column(SQLEnum(LeadSource), default=LeadSource.OTHER)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    
    # Additional Info
    industry = Column(String, nullable=True)
    company_size = Column(String, nullable=True)  # e.g., "1-10", "10-50", "50-200", "200+"
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Scoring
    score = Column(Integer, default=0)  # Lead score 0-100
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Conversion
    converted_at = Column(DateTime, nullable=True)
    converted_opportunity_id = Column(UUID(as_uuid=True), nullable=True)
    converted_customer_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to])
    activities = relationship("Activity", back_populates="lead", cascade="all, delete-orphan")
    notes_list = relationship("Note", back_populates="lead", cascade="all, delete-orphan")


class Opportunity(Base, TenantMixin):
    """Opportunity - Lead yang sudah qualified dan berpotensi jadi deal"""
    __tablename__ = "crm_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Info
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Stage & Probability
    stage = Column(SQLEnum(OpportunityStage), default=OpportunityStage.QUALIFICATION)
    probability = Column(Integer, default=10)  # 0-100%
    
    # Value
    expected_value = Column(Float, default=0)
    expected_close_date = Column(DateTime, nullable=True)
    
    # Links
    lead_id = Column(UUID(as_uuid=True), ForeignKey("crm_leads.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=True)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Outcome
    closed_at = Column(DateTime, nullable=True)
    actual_value = Column(Float, nullable=True)
    lost_reason = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    lead = relationship("Lead")
    customer = relationship("Customer")
    assignee = relationship("User", foreign_keys=[assigned_to])
    activities = relationship("Activity", back_populates="opportunity", cascade="all, delete-orphan")
    notes_list = relationship("Note", back_populates="opportunity", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="opportunity")


class Quotation(Base, TenantMixin):
    """Quotation/Penawaran untuk Opportunity"""
    __tablename__ = "crm_quotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    quotation_number = Column(String, nullable=False, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm_opportunities.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=True)
    
    # Status
    status = Column(String, default="Draft")  # Draft, Sent, Accepted, Rejected, Expired
    valid_until = Column(DateTime, nullable=True)
    
    # Value
    subtotal = Column(Float, default=0)
    discount = Column(Float, default=0)
    tax = Column(Float, default=0)
    total = Column(Float, default=0)
    
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    opportunity = relationship("Opportunity", back_populates="quotations")
    customer = relationship("Customer")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base, TenantMixin):
    __tablename__ = "crm_quotation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("crm_quotations.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    description = Column(String, nullable=True)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    discount = Column(Float, default=0)
    subtotal = Column(Float, default=0)
    
    quotation = relationship("Quotation", back_populates="items")
    product = relationship("Product")


class Activity(Base, TenantMixin):
    """Activity/Task - Follow-up, meeting, call, etc."""
    __tablename__ = "crm_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    activity_type = Column(SQLEnum(ActivityType), default=ActivityType.TASK)
    status = Column(SQLEnum(ActivityStatus), default=ActivityStatus.PLANNED)
    
    # Schedule
    due_date = Column(DateTime, nullable=True)
    due_time = Column(String, nullable=True)  # HH:MM format
    duration_minutes = Column(Integer, nullable=True)
    
    # Priority
    priority = Column(String, default="Normal")  # Low, Normal, High, Urgent
    
    # Links
    lead_id = Column(UUID(as_uuid=True), ForeignKey("crm_leads.id"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm_opportunities.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=True)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Completion
    completed_at = Column(DateTime, nullable=True)
    outcome = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    opportunity = relationship("Opportunity", back_populates="activities")
    customer = relationship("Customer")
    assignee = relationship("User", foreign_keys=[assigned_to])


class Note(Base, TenantMixin):
    """Note/Communication Log"""
    __tablename__ = "crm_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    content = Column(Text, nullable=False)
    
    # Links
    lead_id = Column(UUID(as_uuid=True), ForeignKey("crm_leads.id"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm_opportunities.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"), nullable=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("crm_activities.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="notes_list")
    opportunity = relationship("Opportunity", back_populates="notes_list")
    customer = relationship("Customer")
    creator = relationship("User", foreign_keys=[created_by])


# ==================== EXISTING MODELS ====================

class SalesOrder(Base, TenantMixin):
    __tablename__ = "sales_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("sales_customers.id"))
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm_opportunities.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default=SOStatus.DRAFT)
    source = Column(String, default=OrderSource.MANUAL)
    total_amount = Column(Float, default=0.0)
    
    # Relationships
    customer = relationship("Customer")
    items = relationship("SOItem", back_populates="order", cascade="all, delete-orphan")


class SOItem(Base, TenantMixin):
    __tablename__ = "so_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product")
