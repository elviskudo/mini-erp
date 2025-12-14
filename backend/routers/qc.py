from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
import models
from models import models_qc
import database
import schemas

router = APIRouter(
    prefix="/qc",
    tags=["Quality Control"]
)

# Specs Dictionary (Mock for Phase 1 - In real life, this comes from Product spec table)
# Product Code -> Parameter -> (Min, Max)
SpecsDB = {
    "ph": (6.0, 8.0),
    "viscosity": (100.0, 500.0),
    "weight": (10.0, 50.0) # From IoT simulator
}

@router.post("/inspect", response_model=schemas.InspectionResponse)
async def submit_inspection(inspection: schemas.InspectionCreate, db: AsyncSession = Depends(database.get_db)):
    # Create Order
    new_order = models_qc.InspectionOrder(
        product_id=inspection.product_id,
        batch_number=inspection.batch_number,
        inspector_id=inspection.inspector_id,
        status=models.InspectionStatus.COMPLETED
    )
    db.add(new_order)
    await db.flush()

    overall_verdict = models.Verdict.PASS

    for res in inspection.results:
        # Check specs
        spec_min, spec_max = None, None
        passed = True
        
        # Simple lookup logic (lowercase match)
        param_key = res.parameter.lower()
        if param_key in SpecsDB:
            spec_min, spec_max = SpecsDB[param_key]
            if res.value < spec_min or res.value > spec_max:
                passed = False
                overall_verdict = models.Verdict.FAIL
        
        # If no spec found, assume pass or handle otherwise. Here we assume PASS if no spec.
        
        result_record = models.InspectionResult(
            inspection_order_id=new_order.id,
            parameter_name=res.parameter,
            value_measured=res.value,
            spec_min=spec_min,
            spec_max=spec_max,
            passed=passed
        )
        db.add(result_record)
    
    new_order.verdict = overall_verdict
    
    await db.commit()
    await db.refresh(inspection)
    
    return inspection

@router.get("/inspections", response_model=List[schemas.InspectionResponse])
async def list_inspections(db: AsyncSession = Depends(database.get_db)):
    query = select(models.InspectionOrder).options(selectinload(models.InspectionOrder.product))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/coa/{inspection_id}")
async def get_coa(inspection_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    query = select(models.InspectionOrder)\
        .where(models.InspectionOrder.id == inspection_id)\
        .options(selectinload(models.InspectionOrder.results), selectinload(models.InspectionOrder.product))
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    return {
        "certificate_id": str(order.id),
        "product_name": order.product.name,
        "batch": order.batch_number,
        "date": order.created_at,
        "verdict": order.verdict,
        "results": [
            {
                "parameter": r.parameter_name,
                "value": r.value_measured,
                "spec": f"{r.spec_min} - {r.spec_max}" if r.spec_min else "N/A",
                "status": "PASS" if r.passed else "FAIL"
            } for r in order.results
        ]
    }
