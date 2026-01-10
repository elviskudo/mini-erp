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
    description: Optional[str] = None
    is_active: Optional[bool] = True

# Simple response without children for create/update operations
class AccountSimpleResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    type: str
    parent_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    class Config:
        from_attributes = True

class AccountResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    type: str
    parent_id: Optional[uuid.UUID]
    description: Optional[str] = None
    is_active: Optional[bool] = True
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
# Default tenant ID for MVP (should come from auth in production)
DEFAULT_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")

@router.post("/coa", response_model=AccountSimpleResponse)
async def create_account(account: AccountCreate, db: AsyncSession = Depends(database.get_db)):
    # Check duplicate code
    existing = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == account.code))
    if existing.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Account code already exists")

    account_data = account.dict()
    account_data['tenant_id'] = DEFAULT_TENANT_ID
    new_account = models.ChartOfAccount(**account_data)
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    # Invalidate Cache
    await redis_client.delete("coa_hierarchy")
    
    # Return dict to avoid lazy loading issues
    return {
        "id": new_account.id,
        "code": new_account.code,
        "name": new_account.name,
        "type": new_account.type,
        "parent_id": new_account.parent_id,
        "description": new_account.description,
        "is_active": new_account.is_active
    }

@router.put("/coa/{account_id}", response_model=AccountSimpleResponse)
async def update_account(account_id: uuid.UUID, account: AccountCreate, db: AsyncSession = Depends(database.get_db)):
    existing = await db.get(models.ChartOfAccount, account_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check duplicate code (if changed)
    if account.code != existing.code:
        dup = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == account.code))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Account code already exists")
    
    for key, value in account.dict().items():
        setattr(existing, key, value)
    
    await db.commit()
    await db.refresh(existing)
    
    # Invalidate Cache
    await redis_client.delete("coa_hierarchy")
    
    # Return dict to avoid lazy loading issues
    return {
        "id": existing.id,
        "code": existing.code,
        "name": existing.name,
        "type": existing.type,
        "parent_id": existing.parent_id,
        "description": existing.description,
        "is_active": existing.is_active
    }

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

# General Ledger Query
from sqlalchemy.orm import selectinload

@router.get("/gl")
async def get_general_ledger(
    account_id: uuid.UUID,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(database.get_db)
):
    """Get journal entries for a specific account with running balance"""
    # Verify account exists
    account = await db.get(models.ChartOfAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Build query for journal details with eager loading of entry
    query = select(models.JournalDetail).options(
        selectinload(models.JournalDetail.entry)
    ).join(models.JournalEntry).where(
        models.JournalDetail.account_id == account_id
    ).order_by(models.JournalEntry.date)
    
    if date_from:
        query = query.where(models.JournalEntry.date >= date_from)
    if date_to:
        query = query.where(models.JournalEntry.date <= date_to)
    
    result = await db.execute(query)
    details = result.scalars().all()
    
    # Calculate running balance
    # For assets/expenses: debit increases balance, credit decreases
    # For liabilities/equity/revenue: credit increases balance, debit decreases
    entries = []
    running_balance = 0.0
    opening_balance = 0.0  # TODO: Calculate from prior periods
    
    for detail in details:
        debit = getattr(detail, 'debit', 0) or 0
        credit = getattr(detail, 'credit', 0) or 0
        
        # Determine balance effect based on account type
        if account.type in ['Asset', 'Expense']:
            running_balance += debit - credit
        else:
            running_balance += credit - debit
        
        entries.append({
            "date": detail.entry.date.isoformat() if detail.entry else None,
            "journal_number": f"JE-{str(detail.journal_entry_id)[:8]}",
            "description": detail.entry.description if detail.entry else "",
            "debit": debit,
            "credit": credit,
            "balance": running_balance
        })
    
    return {
        "account_id": str(account_id),
        "account_code": account.code,
        "account_name": account.name,
        "opening_balance": opening_balance,
        "entries": entries
    }

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

@router.post("/journal")
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


# ========== BANKING ACCOUNTS ==========
from pydantic import BaseModel as PydanticBase
from models.models_banking import BankAccount, BankAccountType

# Default tenant for MVP
DEFAULT_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")


class BankAccountCreate(PydanticBase):
    code: str
    name: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    account_type: Optional[str] = "Checking"
    currency_code: str = "IDR"
    opening_balance: float = 0.0
    gl_account_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class BankAccountUpdate(PydanticBase):
    code: Optional[str] = None
    name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    account_type: Optional[str] = None
    currency_code: Optional[str] = None
    opening_balance: Optional[float] = None
    current_balance: Optional[float] = None
    gl_account_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/banking/accounts")
async def list_bank_accounts(db: AsyncSession = Depends(database.get_db)):
    """List all bank accounts"""
    result = await db.execute(
        select(BankAccount).where(BankAccount.tenant_id == DEFAULT_TENANT_ID)
        .order_by(BankAccount.code)
    )
    accounts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "bank_name": a.bank_name,
            "account_number": a.account_number,
            "account_holder": a.account_holder,
            "account_type": a.account_type.value if hasattr(a.account_type, 'value') else str(a.account_type) if a.account_type else "Checking",
            "currency_code": a.currency_code or "IDR",
            "opening_balance": a.opening_balance or 0,
            "current_balance": a.current_balance or 0,
            "gl_account_id": str(a.gl_account_id) if a.gl_account_id else None,
            "is_active": a.is_active if hasattr(a, 'is_active') else True,
            "notes": a.notes
        } for a in accounts
    ]


@router.get("/banking/accounts/{account_id}")
async def get_bank_account(account_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    """Get a single bank account by ID"""
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.tenant_id == DEFAULT_TENANT_ID
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    return {
        "id": str(account.id),
        "code": account.code,
        "name": account.name,
        "bank_name": account.bank_name,
        "account_number": account.account_number,
        "account_holder": account.account_holder,
        "account_type": account.account_type.value if hasattr(account.account_type, 'value') else str(account.account_type) if account.account_type else "Checking",
        "currency_code": account.currency_code or "IDR",
        "opening_balance": account.opening_balance or 0,
        "current_balance": account.current_balance or 0,
        "gl_account_id": str(account.gl_account_id) if account.gl_account_id else None,
        "is_active": account.is_active if hasattr(account, 'is_active') else True,
        "notes": account.notes
    }


@router.post("/banking/accounts")
async def create_bank_account(payload: BankAccountCreate, db: AsyncSession = Depends(database.get_db)):
    """Create a new bank account"""
    new_account = BankAccount(
        tenant_id=DEFAULT_TENANT_ID,
        code=payload.code,
        name=payload.name,
        bank_name=payload.bank_name,
        account_number=payload.account_number,
        account_holder=payload.account_holder,
        account_type=payload.account_type,
        currency_code=payload.currency_code,
        opening_balance=payload.opening_balance,
        current_balance=payload.opening_balance,  # Start with opening balance
        gl_account_id=payload.gl_account_id,
        notes=payload.notes,
        is_active=True
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    return {
        "id": str(new_account.id),
        "code": new_account.code,
        "name": new_account.name,
        "message": "Bank account created successfully"
    }


@router.put("/banking/accounts/{account_id}")
async def update_bank_account(
    account_id: uuid.UUID,
    payload: BankAccountUpdate,
    db: AsyncSession = Depends(database.get_db)
):
    """Update an existing bank account"""
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.tenant_id == DEFAULT_TENANT_ID
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # Update fields if provided
    if payload.code is not None:
        existing.code = payload.code
    if payload.name is not None:
        existing.name = payload.name
    if payload.bank_name is not None:
        existing.bank_name = payload.bank_name
    if payload.account_number is not None:
        existing.account_number = payload.account_number
    if payload.account_holder is not None:
        existing.account_holder = payload.account_holder
    if payload.account_type is not None:
        existing.account_type = payload.account_type
    if payload.currency_code is not None:
        existing.currency_code = payload.currency_code
    if payload.opening_balance is not None:
        existing.opening_balance = payload.opening_balance
    if payload.current_balance is not None:
        existing.current_balance = payload.current_balance
    if payload.gl_account_id is not None:
        existing.gl_account_id = payload.gl_account_id
    if payload.is_active is not None:
        existing.is_active = payload.is_active
    if payload.notes is not None:
        existing.notes = payload.notes
    
    await db.commit()
    await db.refresh(existing)
    
    return {"message": "Bank account updated", "id": str(existing.id)}


@router.delete("/banking/accounts/{account_id}")
async def delete_bank_account(account_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    """Delete (deactivate) a bank account"""
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.tenant_id == DEFAULT_TENANT_ID
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # Soft delete - just deactivate
    existing.is_active = False
    await db.commit()
    
    return {"message": "Bank account deactivated", "id": str(account_id)}
