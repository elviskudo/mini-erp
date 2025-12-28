"""
Projects Module Models - Enhanced with Team, Time Tracking, and Expenses
"""
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, JSON, Boolean, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
import uuid
from . import Base


class ProjectType(str, enum.Enum):
    R_AND_D = "R_AND_D"
    CUSTOMER_ORDER = "CUSTOMER_ORDER"
    INTERNAL_IMPROVEMENT = "INTERNAL_IMPROVEMENT"
    MAINTENANCE = "MAINTENANCE"
    CONSULTING = "CONSULTING"


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProjectPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MemberRole(str, enum.Enum):
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TEAM_LEAD = "TEAM_LEAD"
    DEVELOPER = "DEVELOPER"
    DESIGNER = "DESIGNER"
    QA = "QA"
    ANALYST = "ANALYST"
    MEMBER = "MEMBER"


class ExpenseCategory(str, enum.Enum):
    MATERIAL = "MATERIAL"
    LABOR = "LABOR"
    EQUIPMENT = "EQUIPMENT"
    TRAVEL = "TRAVEL"
    SOFTWARE = "SOFTWARE"
    OTHER = "OTHER"


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String, nullable=False)
    code = Column(String, index=True)  # e.g., PRJ-2024-001
    description = Column(Text, nullable=True)
    type = Column(Enum(ProjectType), default=ProjectType.INTERNAL_IMPROVEMENT)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    priority = Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM)
    
    # People
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    client_id = Column(UUID(as_uuid=True), nullable=True)  # Soft reference to customer
    
    # Timeline
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Budget
    budget = Column(Float, default=0.0)
    
    # Metadata
    tags = Column(JSON, default=list)  # ["urgent", "client-facing"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Task Info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    wbs_code = Column(String)  # 1.1, 1.1.1
    
    # Status & Priority (stored as VARCHAR in DB)
    status = Column(String, default='TODO')  # TODO, IN_PROGRESS, REVIEW, DONE, BLOCKED
    priority = Column(String, default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    
    # Self-referential for hierarchy
    parent_id = Column(String, ForeignKey("project_tasks.id"), nullable=True)
    
    # Timeline
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Progress & Time
    progress = Column(Float, default=0.0)  # 0 to 100
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)  # Calculated from time entries
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Dependencies stored as JSON array of task IDs ["task_id_1", "task_id_2"]
    dependencies = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    parent = relationship("ProjectTask", remote_side=[id], backref="children")
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")


class ProjectMember(Base):
    """Team members assigned to a project"""
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER)
    hourly_rate = Column(Float, default=0.0)  # For cost calculation
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User")


class TimeEntry(Base):
    """Time tracking entries for project work"""
    __tablename__ = "time_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    task_id = Column(String, ForeignKey("project_tasks.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    
    # For billing
    billable = Column(Boolean, default=True)
    billed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="time_entries")
    task = relationship("ProjectTask", back_populates="time_entries")
    user = relationship("User")


class ProjectExpense(Base):
    """Expense tracking for projects"""
    __tablename__ = "project_expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    description = Column(String, nullable=False)
    category = Column(Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    
    receipt_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Who submitted
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="expenses")


class TaskAssignee(Base):
    """Many-to-many relationship between tasks and users (assignees)"""
    __tablename__ = "task_assignees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("ProjectTask", backref="assignees")
    user = relationship("User")


class TaskComment(Base):
    """Comments on project tasks with reactions and replies"""
    __tablename__ = "task_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Reply support
    parent_id = Column(UUID(as_uuid=True), ForeignKey("task_comments.id"), nullable=True)
    
    content = Column(Text, nullable=False)
    
    # Reactions stored as JSON: {"like": [user_ids], "love": [user_ids], "dislike": [user_ids], "amazing": [user_ids]}
    reactions = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task = relationship("ProjectTask", backref="comments")
    user = relationship("User")


class TaskAttachment(Base):
    """File attachments for tasks (stored in Cloudinary)"""
    __tablename__ = "task_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)  # Cloudinary URL
    file_type = Column(String)  # image, document, etc.
    file_size = Column(Integer)  # bytes
    public_id = Column(String)  # Cloudinary public_id for deletion
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("ProjectTask", backref="attachments")
    user = relationship("User")
