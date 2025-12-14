from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from . import Base

class ProjectType(str, enum.Enum):
    R_AND_D = "R_AND_D"
    CUSTOMER_ORDER = "CUSTOMER_ORDER"
    INTERNAL_IMPROVEMENT = "INTERNAL_IMPROVEMENT"

class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True) # e.g., PRJ-2024-001
    type = Column(Enum(ProjectType), default=ProjectType.INTERNAL_IMPROVEMENT)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    budget = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")

class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    name = Column(String, nullable=False)
    wbs_code = Column(String) # 1.1, 1.1.1
    
    # Self-referential for hierarchy
    parent_id = Column(String, ForeignKey("project_tasks.id"), nullable=True)
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    progress = Column(Float, default=0.0) # 0 to 100
    
    assigned_to = Column(String, nullable=True)  # Soft reference to Employee ID
    
    # Dependencies stored as JSON array of task IDs ["task_id_1", "task_id_2"]
    dependencies = Column(JSON, default=list)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    parent = relationship("ProjectTask", remote_side=[id], backref="children")
    # assignee relationship removed due to type mismatch (String vs UUID)
