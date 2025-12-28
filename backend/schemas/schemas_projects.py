"""
Projects Module Schemas - Enhanced with Team, Time Tracking, and Expenses
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from models.models_projects import (
    ProjectType, ProjectStatus, ProjectPriority,
    TaskStatus, TaskPriority, MemberRole, ExpenseCategory
)


# ==================== TASK SCHEMAS ====================

class ProjectTaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    wbs_code: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = 'TODO'
    priority: Optional[str] = 'MEDIUM'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: Optional[float] = 0.0
    estimated_hours: Optional[float] = 0.0
    assigned_to: Optional[UUID] = None
    dependencies: Optional[List[str]] = []


class ProjectTaskCreate(ProjectTaskBase):
    pass


class ProjectTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    wbs_code: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: Optional[float] = None
    estimated_hours: Optional[float] = None
    assigned_to: Optional[UUID] = None
    dependencies: Optional[List[str]] = None


class ProjectTaskResponse(ProjectTaskBase):
    id: str
    project_id: str
    actual_hours: float = 0.0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== MEMBER SCHEMAS ====================

class ProjectMemberBase(BaseModel):
    user_id: UUID
    role: Optional[MemberRole] = MemberRole.MEMBER
    hourly_rate: Optional[float] = 0.0


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberResponse(ProjectMemberBase):
    id: UUID
    project_id: str
    joined_at: datetime
    is_active: bool
    # Include user info
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== TIME ENTRY SCHEMAS ====================

class TimeEntryBase(BaseModel):
    task_id: Optional[str] = None
    date: date
    hours: float
    description: Optional[str] = None
    billable: Optional[bool] = True


class TimeEntryCreate(TimeEntryBase):
    pass


class TimeEntryResponse(TimeEntryBase):
    id: UUID
    project_id: str
    user_id: UUID
    billed: bool = False
    created_at: datetime
    # Include user info
    user_name: Optional[str] = None
    task_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== EXPENSE SCHEMAS ====================

class ProjectExpenseBase(BaseModel):
    description: str
    category: Optional[ExpenseCategory] = ExpenseCategory.OTHER
    amount: float
    date: date
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ProjectExpenseCreate(ProjectExpenseBase):
    pass


class ProjectExpenseResponse(ProjectExpenseBase):
    id: UUID
    project_id: str
    submitted_by: Optional[UUID] = None
    approved: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PROJECT SCHEMAS ====================

class ProjectBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    type: Optional[ProjectType] = ProjectType.INTERNAL_IMPROVEMENT
    status: Optional[ProjectStatus] = ProjectStatus.DRAFT
    priority: Optional[ProjectPriority] = ProjectPriority.MEDIUM
    manager_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = 0.0
    tags: Optional[List[str]] = []


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    manager_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    budget: Optional[float] = None
    tags: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    # Computed fields
    task_count: Optional[int] = 0
    completed_tasks: Optional[int] = 0
    total_hours: Optional[float] = 0.0
    total_expenses: Optional[float] = 0.0

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    tasks: List[ProjectTaskResponse] = []
    members: List[ProjectMemberResponse] = []


# ==================== GANTT & STATS SCHEMAS ====================

class ProjectGanttResponse(BaseModel):
    project: ProjectResponse
    tasks: List[ProjectTaskResponse]


class ProjectStatsResponse(BaseModel):
    project_id: str
    task_count: int
    completed_tasks: int
    progress_percentage: float
    total_estimated_hours: float
    total_actual_hours: float
    total_budget: float
    total_expenses: float
    budget_remaining: float
    team_size: int
    hours_by_member: List[dict] = []
    expenses_by_category: List[dict] = []
