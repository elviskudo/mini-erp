from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

import models # We'll need to export models_qms in __init__
from database import get_db
from models.models_qms import DocStatus, SOPDocument
from connections.mongodb import get_mongo_db

router = APIRouter(
    prefix="/compliance",
    tags=["compliance"]
)

# --- Audit Logs (MongoDB) ---
@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50, 
    action: Optional[str] = None, 
    username: Optional[str] = None
):
    mongo_db = await get_mongo_db()
    collection = mongo_db["audit_logs"]
    
    query = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if username:
        query["username"] = {"$regex": username, "$options": "i"}
        
    cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    # Convert ObjectId to str
    for log in logs:
        log["id"] = str(log.pop("_id"))
        
    return logs

# --- SOP Documents ---
@router.get("/sops")
def list_sops(db: Session = Depends(get_db)):
    return db.query(SOPDocument).order_by(SOPDocument.created_at.desc()).all()

@router.post("/sops")
def create_sop(
    title: str, 
    content: str = None, 
    file_url: str = None, 
    db: Session = Depends(get_db)
):
    # Simplified Pydantic logic via args for speed, normally use schema
    doc = SOPDocument(
        title=title,
        content=content,
        file_url=file_url,
        status=DocStatus.DRAFT,
        version=1,
        created_by="Admin" # Shim
    )
    db.add(doc)
    db.commit()
    return doc

@router.patch("/sops/{id}/approve")
def approve_sop(id: str, db: Session = Depends(get_db)):
    doc = db.query(SOPDocument).filter(SOPDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="SOP not found")
    
    doc.status = DocStatus.APPROVED
    doc.effective_date = datetime.utcnow()
    doc.approved_by = "Admin"
    
    db.commit()
    return doc
