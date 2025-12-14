from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid
import database
import models
import schemas
from services.mrp_engine import MRPEngine

router = APIRouter(
    prefix="/mrp",
    tags=["MRP Power Core"]
)

@router.post("/run", response_model=schemas.MRPRunResponse)
async def run_mrp_calculation(request: schemas.MRPRunRequest, db: AsyncSession = Depends(database.get_db)):
    engine = MRPEngine(db)
    try:
        mrp_run = await engine.run_mrp(request.product_id, request.quantity)
        
        # Reload to get relationships
        query = select(models.MRPRun)\
            .where(models.MRPRun.id == mrp_run.id)\
            .options(selectinload(models.MRPRun.requirements))
        result = await db.execute(query)
        return result.scalar_one()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs", response_model=List[schemas.MRPRunResponse])
async def get_mrp_runs(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(database.get_db)):
    query = select(models.MRPRun)\
        .options(selectinload(models.MRPRun.requirements))\
        .order_by(models.MRPRun.run_date.desc())\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
