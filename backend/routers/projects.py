"""
Projects API Router - Enhanced with Team, Time Tracking, and Expenses
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import datetime
import uuid

import database
import models
from models.models_projects import (
    Project, ProjectTask, ProjectMember, TimeEntry, ProjectExpense,
    ProjectStatus, TaskStatus
)
from schemas.schemas_projects import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    ProjectTaskCreate, ProjectTaskUpdate, ProjectTaskResponse,
    ProjectMemberCreate, ProjectMemberResponse,
    TimeEntryCreate, TimeEntryResponse,
    ProjectExpenseCreate, ProjectExpenseResponse,
    ProjectGanttResponse, ProjectStatsResponse
)
from auth import get_current_user

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


# ==================== PROJECTS ====================

@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new project"""
    # Strip timezone from dates to avoid naive/aware mismatch
    start_date = project.start_date.replace(tzinfo=None) if project.start_date else None
    end_date = project.end_date.replace(tzinfo=None) if project.end_date else None
    
    db_project = Project(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=project.name,
        code=project.code,
        description=project.description,
        type=project.type,
        status=project.status,
        priority=project.priority,
        manager_id=project.manager_id,
        client_id=project.client_id,
        start_date=start_date,
        end_date=end_date,
        budget=project.budget,
        tags=project.tags or []
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    status: str = None,
    type: str = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all projects with optional filters"""
    query = select(Project).where(Project.tenant_id == current_user.tenant_id)
    
    if status:
        query = query.where(Project.status == status)
    if type:
        query = query.where(Project.type == type)
    
    query = query.order_by(Project.created_at.desc())
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # Add computed fields
    response = []
    for p in projects:
        # Count tasks
        task_result = await db.execute(
            select(func.count(ProjectTask.id)).where(ProjectTask.project_id == p.id)
        )
        task_count = task_result.scalar() or 0
        
        completed_result = await db.execute(
            select(func.count(ProjectTask.id)).where(
                and_(ProjectTask.project_id == p.id, ProjectTask.status == 'DONE')
            )
        )
        completed_tasks = completed_result.scalar() or 0
        
        # Sum hours and expenses
        hours_result = await db.execute(
            select(func.sum(TimeEntry.hours)).where(TimeEntry.project_id == p.id)
        )
        total_hours = hours_result.scalar() or 0.0
        
        expense_result = await db.execute(
            select(func.sum(ProjectExpense.amount)).where(ProjectExpense.project_id == p.id)
        )
        total_expenses = expense_result.scalar() or 0.0
        
        response.append({
            **p.__dict__,
            "task_count": task_count,
            "completed_tasks": completed_tasks,
            "total_hours": total_hours,
            "total_expenses": total_expenses
        })
    
    return response


@router.get("/{id}", response_model=ProjectDetailResponse)
async def get_project(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get project with tasks and members"""
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.tasks), selectinload(Project.members))
        .where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Enrich members with user info
    members_response = []
    for m in project.members:
        user_result = await db.execute(
            select(models.User).where(models.User.id == m.user_id)
        )
        user = user_result.scalar_one_or_none()
        members_response.append({
            **m.__dict__,
            "user_name": user.username if user else None,
            "user_email": user.email if user else None
        })
    
    return {
        **project.__dict__,
        "tasks": project.tasks,
        "members": members_response
    }


@router.put("/{id}", response_model=ProjectResponse)
async def update_project(
    id: str,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a project"""
    result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.model_dump(exclude_unset=True)
    # Strip timezone from datetime fields
    for key in ['start_date', 'end_date', 'actual_end_date']:
        if key in update_data and update_data[key] is not None:
            update_data[key] = update_data[key].replace(tzinfo=None)
    
    for key, value in update_data.items():
        setattr(project, key, value)
    
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{id}")
async def delete_project(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a project"""
    result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}


# ==================== TASKS ====================

@router.post("/{id}/tasks", response_model=ProjectTaskResponse)
async def create_task(
    id: str,
    task: ProjectTaskCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a task in a project"""
    # Verify project exists
    result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_task = ProjectTask(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        project_id=id,
        name=task.name,
        description=task.description,
        wbs_code=task.wbs_code,
        parent_id=task.parent_id,
        status=task.status,
        priority=task.priority,
        start_date=task.start_date,
        end_date=task.end_date,
        progress=task.progress,
        estimated_hours=task.estimated_hours,
        assigned_to=task.assigned_to,
        dependencies=task.dependencies or []
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.get("/{id}/tasks", response_model=List[ProjectTaskResponse])
async def list_tasks(
    id: str,
    status: str = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all tasks in a project"""
    query = select(ProjectTask).where(
        and_(ProjectTask.project_id == id, ProjectTask.tenant_id == current_user.tenant_id)
    )
    
    if status:
        query = query.where(ProjectTask.status == status)
    
    result = await db.execute(query.order_by(ProjectTask.wbs_code))
    return result.scalars().all()


@router.put("/tasks/{task_id}", response_model=ProjectTaskResponse)
async def update_task(
    task_id: str,
    task_update: ProjectTaskUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a task"""
    result = await db.execute(
        select(ProjectTask).where(
            and_(ProjectTask.id == task_id, ProjectTask.tenant_id == current_user.tenant_id)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    # Strip timezone from datetime fields
    for key in ['start_date', 'end_date']:
        if key in update_data and update_data[key] is not None:
            update_data[key] = update_data[key].replace(tzinfo=None)
    
    for key, value in update_data.items():
        setattr(task, key, value)
    
    # Mark completed if status is DONE
    if task_update.status == 'DONE' and not task.completed_at:
        task.completed_at = datetime.utcnow()
        task.progress = 100.0
    
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a task"""
    result = await db.execute(
        select(ProjectTask).where(
            and_(ProjectTask.id == task_id, ProjectTask.tenant_id == current_user.tenant_id)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}


# ==================== TASK ASSIGNEES ====================

@router.get("/tasks/{task_id}/assignees")
async def get_task_assignees(
    task_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all assignees for a task"""
    from models.models_projects import TaskAssignee
    result = await db.execute(
        select(TaskAssignee).where(
            and_(TaskAssignee.task_id == task_id, TaskAssignee.tenant_id == current_user.tenant_id)
        )
    )
    assignees = result.scalars().all()
    
    # Get user info for each assignee
    response = []
    for a in assignees:
        user_result = await db.execute(select(models.User).where(models.User.id == a.user_id))
        user = user_result.scalar_one_or_none()
        response.append({
            "id": str(a.id),
            "task_id": a.task_id,
            "user_id": str(a.user_id),
            "user_name": user.username if user else "Unknown",
            "assigned_at": a.assigned_at
        })
    return response


@router.post("/tasks/{task_id}/assignees")
async def add_task_assignee(
    task_id: str,
    data: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add an assignee to a task"""
    from models.models_projects import TaskAssignee
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    # Check if already assigned
    existing = await db.execute(
        select(TaskAssignee).where(
            and_(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already assigned")
    
    assignee = TaskAssignee(
        tenant_id=current_user.tenant_id,
        task_id=task_id,
        user_id=user_id
    )
    db.add(assignee)
    await db.commit()
    return {"message": "Assignee added"}


@router.delete("/tasks/{task_id}/assignees/{user_id}")
async def remove_task_assignee(
    task_id: str,
    user_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove an assignee from a task"""
    from models.models_projects import TaskAssignee
    result = await db.execute(
        select(TaskAssignee).where(
            and_(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id, TaskAssignee.tenant_id == current_user.tenant_id)
        )
    )
    assignee = result.scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    await db.delete(assignee)
    await db.commit()
    return {"message": "Assignee removed"}


# ==================== TASK COMMENTS ====================

@router.get("/tasks/{task_id}/comments")
async def get_task_comments(
    task_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all comments for a task"""
    from models.models_projects import TaskComment
    result = await db.execute(
        select(TaskComment).where(
            and_(TaskComment.task_id == task_id, TaskComment.tenant_id == current_user.tenant_id)
        ).order_by(TaskComment.created_at.desc())
    )
    comments = result.scalars().all()
    
    response = []
    for c in comments:
        user_result = await db.execute(select(models.User).where(models.User.id == c.user_id))
        user = user_result.scalar_one_or_none()
        response.append({
            "id": str(c.id),
            "task_id": c.task_id,
            "user_id": str(c.user_id),
            "user_name": user.username if user else "Unknown",
            "content": c.content,
            "created_at": c.created_at
        })
    return response


@router.post("/tasks/{task_id}/comments")
async def add_task_comment(
    task_id: str,
    data: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add a comment to a task"""
    from models.models_projects import TaskComment
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content required")
    
    comment = TaskComment(
        tenant_id=current_user.tenant_id,
        task_id=task_id,
        user_id=current_user.id,
        content=content
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return {
        "id": str(comment.id),
        "task_id": comment.task_id,
        "user_id": str(comment.user_id),
        "user_name": current_user.username,
        "content": comment.content,
        "created_at": comment.created_at,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "reactions": comment.reactions or {}
    }


@router.delete("/tasks/{task_id}/comments/{comment_id}")
async def delete_task_comment(
    task_id: str,
    comment_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a comment (only manager or comment owner)"""
    from models.models_projects import TaskComment
    result = await db.execute(
        select(TaskComment).where(
            and_(TaskComment.id == comment_id, TaskComment.tenant_id == current_user.tenant_id)
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only owner or manager can delete
    is_manager = current_user.role in ['admin', 'manager']
    if str(comment.user_id) != str(current_user.id) and not is_manager:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    await db.delete(comment)
    await db.commit()
    return {"message": "Comment deleted"}


@router.post("/tasks/{task_id}/comments/{comment_id}/react")
async def toggle_comment_reaction(
    task_id: str,
    comment_id: str,
    data: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Toggle a reaction on a comment (like, love, dislike, amazing)"""
    from models.models_projects import TaskComment
    reaction_type = data.get("reaction")  # like, love, dislike, amazing
    if reaction_type not in ["like", "love", "dislike", "amazing"]:
        raise HTTPException(status_code=400, detail="Invalid reaction type")
    
    result = await db.execute(
        select(TaskComment).where(
            and_(TaskComment.id == comment_id, TaskComment.tenant_id == current_user.tenant_id)
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    reactions = comment.reactions or {}
    user_id_str = str(current_user.id)
    
    # Toggle reaction
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    
    if user_id_str in reactions[reaction_type]:
        reactions[reaction_type].remove(user_id_str)
    else:
        reactions[reaction_type].append(user_id_str)
    
    comment.reactions = reactions
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(comment, "reactions")
    await db.commit()
    
    return {"reactions": reactions}


@router.post("/tasks/{task_id}/comments/{comment_id}/reply")
async def reply_to_comment(
    task_id: str,
    comment_id: str,
    data: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Reply to a comment"""
    from models.models_projects import TaskComment
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content required")
    
    reply = TaskComment(
        tenant_id=current_user.tenant_id,
        task_id=task_id,
        user_id=current_user.id,
        parent_id=comment_id,
        content=content,
        reactions={}
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    
    return {
        "id": str(reply.id),
        "task_id": reply.task_id,
        "user_id": str(reply.user_id),
        "user_name": current_user.username,
        "content": reply.content,
        "parent_id": str(reply.parent_id),
        "created_at": reply.created_at,
        "reactions": {}
    }


# ==================== TASK ATTACHMENTS ====================

@router.get("/tasks/{task_id}/attachments")
async def get_task_attachments(
    task_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all attachments for a task"""
    from models.models_projects import TaskAttachment
    result = await db.execute(
        select(TaskAttachment).where(
            and_(TaskAttachment.task_id == task_id, TaskAttachment.tenant_id == current_user.tenant_id)
        ).order_by(TaskAttachment.created_at.desc())
    )
    attachments = result.scalars().all()
    
    response = []
    for a in attachments:
        user_result = await db.execute(select(models.User).where(models.User.id == a.user_id))
        user = user_result.scalar_one_or_none()
        response.append({
            "id": str(a.id),
            "task_id": a.task_id,
            "user_id": str(a.user_id),
            "user_name": user.username if user else "Unknown",
            "file_name": a.file_name,
            "file_url": a.file_url,
            "file_type": a.file_type,
            "file_size": a.file_size,
            "created_at": a.created_at
        })
    return response


@router.post("/tasks/{task_id}/attachments")
async def add_task_attachment(
    task_id: str,
    data: dict,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add an attachment to a task (file already uploaded to Cloudinary)"""
    from models.models_projects import TaskAttachment
    
    file_name = data.get("file_name")
    file_url = data.get("file_url")
    if not file_name or not file_url:
        raise HTTPException(status_code=400, detail="file_name and file_url required")
    
    attachment = TaskAttachment(
        tenant_id=current_user.tenant_id,
        task_id=task_id,
        user_id=current_user.id,
        file_name=file_name,
        file_url=file_url,
        file_type=data.get("file_type"),
        file_size=data.get("file_size"),
        public_id=data.get("public_id")
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    
    return {
        "id": str(attachment.id),
        "task_id": attachment.task_id,
        "file_name": attachment.file_name,
        "file_url": attachment.file_url,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "created_at": attachment.created_at
    }


@router.delete("/tasks/{task_id}/attachments/{attachment_id}")
async def delete_task_attachment(
    task_id: str,
    attachment_id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an attachment"""
    from models.models_projects import TaskAttachment
    result = await db.execute(
        select(TaskAttachment).where(
            and_(TaskAttachment.id == attachment_id, TaskAttachment.tenant_id == current_user.tenant_id)
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    await db.delete(attachment)
    await db.commit()
    return {"message": "Attachment deleted"}


# ==================== MEMBERS ====================

@router.get("/{id}/members", response_model=List[ProjectMemberResponse])
async def list_members(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all members of a project"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == id, ProjectMember.tenant_id == current_user.tenant_id)
        )
    )
    members = result.scalars().all()
    
    # Enrich with user info
    response = []
    for m in members:
        user_result = await db.execute(
            select(models.User).where(models.User.id == m.user_id)
        )
        user = user_result.scalar_one_or_none()
        response.append({
            **m.__dict__,
            "user_name": user.username if user else None,
            "user_email": user.email if user else None
        })
    
    return response


@router.post("/{id}/members", response_model=ProjectMemberResponse)
async def add_member(
    id: str,
    member: ProjectMemberCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add a member to a project"""
    # Check project exists
    project_result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if already a member
    existing = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == id, ProjectMember.user_id == member.user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")
    
    db_member = ProjectMember(
        tenant_id=current_user.tenant_id,
        project_id=id,
        user_id=member.user_id,
        role=member.role,
        hourly_rate=member.hourly_rate
    )
    db.add(db_member)
    await db.commit()
    await db.refresh(db_member)
    
    # Get user info
    user_result = await db.execute(
        select(models.User).where(models.User.id == member.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    return {
        **db_member.__dict__,
        "user_name": user.username if user else None,
        "user_email": user.email if user else None
    }


@router.delete("/{id}/members/{user_id}")
async def remove_member(
    id: str,
    user_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove a member from a project"""
    result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == id,
                ProjectMember.user_id == user_id,
                ProjectMember.tenant_id == current_user.tenant_id
            )
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    await db.delete(member)
    await db.commit()
    return {"message": "Member removed"}


# ==================== TIME ENTRIES ====================

@router.get("/{id}/time-entries", response_model=List[TimeEntryResponse])
async def list_time_entries(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all time entries for a project"""
    result = await db.execute(
        select(TimeEntry).where(
            and_(TimeEntry.project_id == id, TimeEntry.tenant_id == current_user.tenant_id)
        ).order_by(TimeEntry.date.desc())
    )
    entries = result.scalars().all()
    
    # Enrich with user and task info
    response = []
    for e in entries:
        user_result = await db.execute(
            select(models.User).where(models.User.id == e.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        task_name = None
        if e.task_id:
            task_result = await db.execute(
                select(ProjectTask).where(ProjectTask.id == e.task_id)
            )
            task = task_result.scalar_one_or_none()
            task_name = task.name if task else None
        
        response.append({
            **e.__dict__,
            "user_name": user.username if user else None,
            "task_name": task_name
        })
    
    return response


@router.post("/{id}/time-entries", response_model=TimeEntryResponse)
async def create_time_entry(
    id: str,
    entry: TimeEntryCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Log time for a project"""
    # Check project exists
    project_result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_entry = TimeEntry(
        tenant_id=current_user.tenant_id,
        project_id=id,
        task_id=entry.task_id,
        user_id=current_user.id,
        date=entry.date,
        hours=entry.hours,
        description=entry.description,
        billable=entry.billable
    )
    db.add(db_entry)
    
    # Update task actual_hours if task specified
    if entry.task_id:
        task_result = await db.execute(
            select(ProjectTask).where(ProjectTask.id == entry.task_id)
        )
        task = task_result.scalar_one_or_none()
        if task:
            task.actual_hours = (task.actual_hours or 0) + entry.hours
    
    await db.commit()
    await db.refresh(db_entry)
    
    return {
        **db_entry.__dict__,
        "user_name": current_user.username,
        "task_name": None
    }


# ==================== EXPENSES ====================

@router.get("/{id}/expenses", response_model=List[ProjectExpenseResponse])
async def list_expenses(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all expenses for a project"""
    result = await db.execute(
        select(ProjectExpense).where(
            and_(ProjectExpense.project_id == id, ProjectExpense.tenant_id == current_user.tenant_id)
        ).order_by(ProjectExpense.date.desc())
    )
    return result.scalars().all()


@router.post("/{id}/expenses", response_model=ProjectExpenseResponse)
async def create_expense(
    id: str,
    expense: ProjectExpenseCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add an expense to a project"""
    # Check project exists
    project_result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_expense = ProjectExpense(
        tenant_id=current_user.tenant_id,
        project_id=id,
        description=expense.description,
        category=expense.category,
        amount=expense.amount,
        date=expense.date,
        receipt_url=expense.receipt_url,
        notes=expense.notes,
        submitted_by=current_user.id
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense


# ==================== STATS & GANTT ====================

@router.get("/{id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get project statistics and analytics"""
    # Verify project
    project_result = await db.execute(
        select(Project).where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Task counts
    task_result = await db.execute(
        select(func.count(ProjectTask.id)).where(ProjectTask.project_id == id)
    )
    task_count = task_result.scalar() or 0
    
    completed_result = await db.execute(
        select(func.count(ProjectTask.id)).where(
            and_(ProjectTask.project_id == id, ProjectTask.status == 'DONE')
        )
    )
    completed_tasks = completed_result.scalar() or 0
    
    # Hours
    estimated_result = await db.execute(
        select(func.sum(ProjectTask.estimated_hours)).where(ProjectTask.project_id == id)
    )
    total_estimated = estimated_result.scalar() or 0.0
    
    actual_result = await db.execute(
        select(func.sum(TimeEntry.hours)).where(TimeEntry.project_id == id)
    )
    total_actual = actual_result.scalar() or 0.0
    
    # Expenses
    expense_result = await db.execute(
        select(func.sum(ProjectExpense.amount)).where(ProjectExpense.project_id == id)
    )
    total_expenses = expense_result.scalar() or 0.0
    
    # Team size
    member_result = await db.execute(
        select(func.count(ProjectMember.id)).where(
            and_(ProjectMember.project_id == id, ProjectMember.is_active == True)
        )
    )
    team_size = member_result.scalar() or 0
    
    # Hours by member
    hours_by_member_result = await db.execute(
        select(TimeEntry.user_id, func.sum(TimeEntry.hours).label("total_hours"))
        .where(TimeEntry.project_id == id)
        .group_by(TimeEntry.user_id)
    )
    hours_by_member = []
    for row in hours_by_member_result:
        user_result = await db.execute(
            select(models.User).where(models.User.id == row.user_id)
        )
        user = user_result.scalar_one_or_none()
        hours_by_member.append({
            "user_id": str(row.user_id),
            "user_name": user.username if user else "Unknown",
            "hours": row.total_hours
        })
    
    # Expenses by category
    expenses_by_cat_result = await db.execute(
        select(ProjectExpense.category, func.sum(ProjectExpense.amount).label("total"))
        .where(ProjectExpense.project_id == id)
        .group_by(ProjectExpense.category)
    )
    expenses_by_category = [
        {"category": row.category.value if row.category else "OTHER", "amount": row.total}
        for row in expenses_by_cat_result
    ]
    
    progress = (completed_tasks / task_count * 100) if task_count > 0 else 0
    
    return {
        "project_id": id,
        "task_count": task_count,
        "completed_tasks": completed_tasks,
        "progress_percentage": round(progress, 1),
        "total_estimated_hours": total_estimated,
        "total_actual_hours": total_actual,
        "total_budget": project.budget or 0,
        "total_expenses": total_expenses,
        "budget_remaining": (project.budget or 0) - total_expenses,
        "team_size": team_size,
        "hours_by_member": hours_by_member,
        "expenses_by_category": expenses_by_category
    }


@router.get("/{id}/gantt", response_model=ProjectGanttResponse)
async def get_project_gantt(
    id: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get project data formatted for Gantt chart"""
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.tasks))
        .where(and_(Project.id == id, Project.tenant_id == current_user.tenant_id))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project": project,
        "tasks": project.tasks
    }
