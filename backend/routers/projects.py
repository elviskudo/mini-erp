from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid

import models, schemas
from database import get_db

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)

# --- Projects ---

@router.post("", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(
        id=str(uuid.uuid4()),
        name=project.name,
        code=project.code,
        type=project.type,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        budget=project.budget
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@router.get("/{id}", response_model=schemas.ProjectResponse)
def get_project(id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# --- Tasks ---

@router.post("/{id}/tasks", response_model=schemas.ProjectTaskResponse)
def create_task(id: str, task: schemas.ProjectTaskCreate, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_task = models.ProjectTask(
        id=str(uuid.uuid4()),
        project_id=id,
        name=task.name,
        wbs_code=task.wbs_code,
        parent_id=task.parent_id,
        start_date=task.start_date,
        end_date=task.end_date,
        progress=task.progress,
        assigned_to=task.assigned_to,
        dependencies=task.dependencies
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/{id}/gantt", response_model=schemas.ProjectGanttResponse)
def get_project_gantt(id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    tasks = db.query(models.ProjectTask).filter(models.ProjectTask.project_id == id).all()
    
    return {
        "project": project,
        "tasks": tasks
    }

@router.patch("/tasks/{task_id}", response_model=schemas.ProjectTaskResponse)
def update_task(task_id: str, task_update: schemas.ProjectTaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(models.ProjectTask).filter(models.ProjectTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/{id}/costs")
def get_project_costs(id: str, db: Session = Depends(get_db)):
    """
    Calculate total actual cost for a project based on material issuance.
    Logic: Sum(InventoryLedger.quantity_change * Product.cost) 
    Note: InventoryLedger quantity_change is negative for OUT_ISSUE, so we negate it.
    """
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Aggregate Material Costs
    # We join StockMovement -> Product to get cost.
    # We filter by project_id and movement_type = OUT_ISSUE
    
    # Note: StockMovement uses 'quantity_change' which is negative for issue.
    # Product cost assumption: we use current standard cost from Product table for simplicity.
    # In advanced ERP, we should use FIFO/Avg Cost from the specific batch, but that complexity is skipped for MVP.
    
    total_material_cost = 0.0
    
    movements = db.query(models.StockMovement)\
        .filter(models.StockMovement.project_id == id)\
        .filter(models.StockMovement.movement_type == models.MovementType.OUT_ISSUE)\
        .all()
        
    for mv in movements:
        product = db.query(models.Product).filter(models.Product.id == mv.product_id).first()
        if product:
             # quantity_change is negative, so -(-5) * 10 = 50
            cost = abs(mv.quantity_change) * (product.standard_cost or 0)
            total_material_cost += cost
            
    return {
        "project_id": id,
        "material_cost": total_material_cost,
        "labor_cost": 0.0, # Placeholder
        "total_actual_cost": total_material_cost,
        "budget": project.budget,
        "variance": (project.budget or 0) - total_material_cost
    }
