from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.models_projects import ProjectType, ProjectStatus

# --- Task Schemas ---
class ProjectTaskBase(BaseModel):
    name: str
    wbs_code: Optional[str] = None
    parent_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: Optional[float] = 0.0
    assigned_to: Optional[str] = None
    dependencies: Optional[List[str]] = []

class ProjectTaskCreate(ProjectTaskBase):
    pass

class ProjectTaskUpdate(ProjectTaskBase):
    name: Optional[str] = None

class ProjectTaskResponse(ProjectTaskBase):
    id: str
    project_id: str
    children: Optional[List['ProjectTaskResponse']] = []

    class Config:
        from_attributes = True

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    code: str
    type: ProjectType
    status: Optional[ProjectStatus] = ProjectStatus.PLANNING
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = 0.0

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    # tasks: List[ProjectTaskResponse] = [] # Optional to include tasks in list view

    class Config:
        from_attributes = True

# For Gantt View, we might need a specialized flat response or hierarchical
class ProjectGanttResponse(BaseModel):
    project: ProjectResponse
    tasks: List[ProjectTaskResponse]
