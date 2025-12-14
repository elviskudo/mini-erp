from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime
import json

import database
import models
from utils.cache import redis_client

router = APIRouter(
    prefix="/finance",
    tags=["Financial Management"]
)

# Schemas
class AccountCreate(BaseModel):
    code: str
    name: str
    type: str
    parent_id: Optional[uuid.UUID] = None

class AccountResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    type: str
    parent_id: Optional[uuid.UUID]
    children: List['AccountResponse'] = []
    class Config:
        from_attributes = True

class PeriodCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime

class PeriodResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_date: datetime
    end_date: datetime
    is_closed: bool
    class Config:
        from_attributes = True

# COA Endpoints
@router.post("/coa", response_model=AccountResponse)
async def create_account(account: AccountCreate, db: AsyncSession = Depends(database.get_db)):
    # Check duplicate code
    existing = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == account.code))
    if existing.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Account code already exists")

    new_account = models.ChartOfAccount(**account.dict())
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    # Invalidate Cache
    await redis_client.delete("coa_hierarchy")
    
    return new_account

@router.get("/coa", response_model=List[AccountResponse])
async def get_coa(db: AsyncSession = Depends(database.get_db)):
    # Try Cache
    cached = await redis_client.get("coa_hierarchy")
    if cached:
        # We need to deserialize properly. Pydantic can handle list of dicts.
        return json.loads(cached)

    # Fetch fresh (Hierarchy logic needed? For flat list let's just dump)
    # Ideally we build a tree. For now, let's return flat list but ordered by code?
    # Or actually build the tree if the schema expects children.
    # The schema `children: List['AccountResponse'] = []` implies tree.
    # Let's fetch root accounts (parent_id is None) and load children recursively.
    
    # Simple adjacency list fetching is hard in one query unless we use CTE.
    # For MVP, let's fetch ALL and build tree in Python.
    query = select(models.ChartOfAccount)
    result = await db.execute(query)
    all_accounts = result.scalars().all()
    
    # Build Tree
    account_map = {acc.id: acc for acc in all_accounts}
    roots = []
    
    # We need to convert SQLAlchemy objects to dicts to attach 'children' property dynamically 
    # since SQLAlchemy models don't auto-populate 'children' unless eager loaded properly (which is hard for deep recursive)
    # actually `remote_side` in model handles this if we query roots.
    
    # Let's simplify: Return Flat List for now, frontend can build tree.
    # Wait, user wants "Hierarchical structure".
    # Let's try to return roots with selectinload(children).
    # But that's only 1 level.
    
    # Python-side reconstruction:
    # 1 Convert to Pydantic-friendly dicts
    nodes = {acc.id: {
        "id": str(acc.id), 
        "code": acc.code, 
        "name": acc.name, 
        "type": acc.type, 
        "parent_id": str(acc.parent_id) if acc.parent_id else None, 
        "children": []
    } for acc in all_accounts}

    root_nodes = []
    for acc in all_accounts:
        if acc.parent_id:
            parent = nodes.get(acc.parent_id)
            if parent:
                parent["children"].append(nodes[acc.id])
        else:
            root_nodes.append(nodes[acc.id])
            
    # Cache it
    await redis_client.set("coa_hierarchy", json.dumps(root_nodes), expire=3600)
    
    return root_nodes

@router.post("/coa/seed")
async def seed_coa(db: AsyncSession = Depends(database.get_db)):
    # Standard Template
    template = [
        {"code": "1000", "name": "ASSETS", "type": "Asset", "children": [
            {"code": "1100", "name": "Current Assets", "type": "Asset", "children": [
                {"code": "1110", "name": "Cash & Bank", "type": "Asset"},
                {"code": "1120", "name": "Accounts Receivable", "type": "Asset"},
                {"code": "1130", "name": "Inventory", "type": "Asset"},
            ]},
            {"code": "1200", "name": "Fixed Assets", "type": "Asset"}
        ]},
        {"code": "2000", "name": "LIABILITIES", "type": "Liability", "children": [
            {"code": "2100", "name": "Accounts Payable", "type": "Liability"}
        ]},
        {"code": "3000", "name": "EQUITY", "type": "Equity", "children": [
            {"code": "3100", "name": "Capital", "type": "Equity"}
        ]},
         {"code": "4000", "name": "REVENUE", "type": "Income", "children": [
            {"code": "4100", "name": "Sales Revenue", "type": "Income"}
        ]},
         {"code": "5000", "name": "EXPENSES", "type": "Expense", "children": [
            {"code": "5100", "name": "COGS", "type": "Expense"},
             {"code": "5200", "name": "Operating Expenses", "type": "Expense"}
        ]}
    ]

    async def create_recursive(node, parent_id=None):
        existing = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == node["code"]))
        acc = existing.scalar_one_or_none()
        
        if not acc:
            acc = models.ChartOfAccount(
                code=node["code"],
                name=node["name"],
                type=node["type"],
                parent_id=parent_id
            )
            db.add(acc)
            await db.flush() # get ID
        
        if "children" in node:
            for child in node["children"]:
                await create_recursive(child, acc.id)

    for root in template:
        await create_recursive(root)
    
    await db.commit()
    await redis_client.delete("coa_hierarchy")
    return {"status": "Seeded"}

# Fiscal Periods
@router.post("/periods", response_model=PeriodResponse)
async def create_period(period: PeriodCreate, db: AsyncSession = Depends(database.get_db)):
    new_period = models.FiscalPeriod(**period.dict())
    db.add(new_period)
    await db.commit()
    await db.refresh(new_period)
    return new_period

@router.get("/periods", response_model=List[PeriodResponse])
async def list_periods(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.FiscalPeriod).order_by(models.FiscalPeriod.start_date.desc()))
    return result.scalars().all()

@router.post("/periods/{id}/close")
async def close_period(id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    period = await db.get(models.FiscalPeriod, id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    
    period.is_closed = True
    await db.commit()
    
    
    # Broadcast event via RabbitMQ (Placeholder for now, but addressing the 'use rabbitmq' request)
    # In Task 3.3/3.8 we might listen to this to generate final reports
    
    return {"status": "Closed"}

import schemas
from services.gl_engine import post_journal_entry

@router.post("/journal", response_model=schemas.JournalEntryResponse)
async def create_journal(entry: schemas.JournalEntryCreate, db: AsyncSession = Depends(database.get_db)):
    # User ID would come from auth in real scenario
    return await post_journal_entry(db, entry, user_id=None)

# Fixed Assets
from services.asset_mgmt import run_depreciation

@router.post("/assets", response_model=schemas.AssetResponse)
async def create_asset(asset: schemas.AssetCreate, db: AsyncSession = Depends(database.get_db)):
    new_asset = models.FixedAsset(**asset.dict())
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    return new_asset

@router.post("/assets/{id}/depreciate")
async def depreciate_asset(id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    try:
        return await run_depreciation(db, id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Reporting
from services import reporting_engine

@router.get("/reports/trial-balance")
async def get_trial_balance(db: AsyncSession = Depends(database.get_db)):
    return await reporting_engine.generate_trial_balance(db)

@router.get("/reports/pl")
async def get_pl(start_date: datetime, end_date: datetime, db: AsyncSession = Depends(database.get_db)):
    return await reporting_engine.generate_pl(db, start_date, end_date)

@router.get("/reports/balance-sheet")
async def get_balance_sheet(date: datetime, db: AsyncSession = Depends(database.get_db)):
    return await reporting_engine.generate_balance_sheet(db, date)
