from fastapi import APIRouter, HTTPException, BackgroundTasks
from connections.rabbitmq_utils import publish_message
from sqlalchemy.orm import Session
from fastapi import Depends
import database
import models
import schemas

router = APIRouter(
    prefix="/iot",
    tags=["IoT"]
)

@router.post("/ingest")
async def ingest_lab_data(payload: schemas.LabDataPayload, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    # 1. Check Asset Calibration Status
    # Assuming device_id maps to FixedAsset.id or FixedAsset.code
    # For MVP, we'll try to find a FixedAsset with code == device_id
    asset = db.query(models.FixedAsset).filter(models.FixedAsset.code == payload.device_id).first()
    
    if asset:
        if asset.calibration_status == models.CalibrationStatus.EXPIRED:
            raise HTTPException(status_code=400, detail="Data Rejected: Device Calibration Expired")
    
    try:
        # Publish to RabbitMQ in background to not block response
        background_tasks.add_task(publish_message, "lab_data_ingress", payload.dict())
        return {"status": "queued", "message": "Data received and queued for processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
