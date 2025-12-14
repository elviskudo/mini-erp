from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

import models, schemas
from database import get_db
from models.models_finance import CalibrationStatus, FixedAsset
from models.models_maintenance import MaintenanceType, MaintenanceStatus

router = APIRouter(
    prefix="/maintenance",
    tags=["maintenance"]
)

@router.post("/orders", response_model=schemas.MaintenanceOrderResponse)
def create_order(order: schemas.MaintenanceOrderCreate, db: Session = Depends(get_db)):
    db_order = models.MaintenanceOrder(
        id=str(uuid.uuid4()),
        asset_id=order.asset_id,
        type=order.type,
        scheduled_date=order.scheduled_date,
        description=order.description,
        technician=order.technician,
        status=MaintenanceStatus.OPEN
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/orders", response_model=List[schemas.MaintenanceOrderResponse])
def list_orders(db: Session = Depends(get_db)):
    return db.query(models.MaintenanceOrder).all()

@router.post("/orders/{id}/complete", response_model=schemas.MaintenanceOrderResponse)
def complete_order(id: str, request: schemas.CompleteOrderRequest, db: Session = Depends(get_db)):
    order = db.query(models.MaintenanceOrder).filter(models.MaintenanceOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status == MaintenanceStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Order already completed")
        
    order.status = MaintenanceStatus.COMPLETED
    order.completion_date = datetime.utcnow()
    order.notes = request.notes
    
    # Validation / Calibration Logic
    if order.type == MaintenanceType.CALIBRATION:
        asset = db.query(FixedAsset).filter(FixedAsset.id == order.asset_id).first()
        if asset:
            asset.calibration_status = CalibrationStatus.VALID
            asset.last_calibration_date = datetime.utcnow()
            if request.next_calibration_date:
                asset.next_calibration_date = request.next_calibration_date
    
    db.commit()
    db.refresh(order)
    return order
