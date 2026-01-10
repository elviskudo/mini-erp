"""
Sales Router - Customer management endpoints
Routes for /sales/customers
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
import uuid
from pydantic import BaseModel

import models
import database

# Default tenant for MVP
DEFAULT_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


# ===== SCHEMAS =====

class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: float = 0


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Optional[float] = None


# ===== CUSTOMERS =====

@router.get("/customers")
async def list_customers(
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(database.get_db)
):
    """List all customers"""
    query = select(models.Customer).where(
        models.Customer.tenant_id == DEFAULT_TENANT_ID
    )
    
    if search:
        query = query.where(models.Customer.name.ilike(f"%{search}%"))
    
    query = query.order_by(models.Customer.name).offset(skip).limit(limit)
    result = await db.execute(query)
    customers = result.scalars().all()
    
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "credit_limit": c.credit_limit or 0,
            "current_balance": c.current_balance or 0
        } for c in customers
    ]


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    """Get a single customer by ID"""
    result = await db.execute(
        select(models.Customer).where(
            models.Customer.id == customer_id,
            models.Customer.tenant_id == DEFAULT_TENANT_ID
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "id": str(customer.id),
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "credit_limit": customer.credit_limit or 0,
        "current_balance": customer.current_balance or 0
    }


@router.post("/customers")
async def create_customer(payload: CustomerCreate, db: AsyncSession = Depends(database.get_db)):
    """Create a new customer"""
    new_customer = models.Customer(
        tenant_id=DEFAULT_TENANT_ID,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        credit_limit=payload.credit_limit,
        current_balance=0
    )
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    
    return {
        "id": str(new_customer.id),
        "name": new_customer.name,
        "message": "Customer created successfully"
    }


@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(database.get_db)
):
    """Update an existing customer"""
    result = await db.execute(
        select(models.Customer).where(
            models.Customer.id == customer_id,
            models.Customer.tenant_id == DEFAULT_TENANT_ID
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields if provided
    if payload.name is not None:
        existing.name = payload.name
    if payload.email is not None:
        existing.email = payload.email
    if payload.phone is not None:
        existing.phone = payload.phone
    if payload.address is not None:
        existing.address = payload.address
    if payload.credit_limit is not None:
        existing.credit_limit = payload.credit_limit
    
    await db.commit()
    await db.refresh(existing)
    
    return {"message": "Customer updated", "id": str(existing.id)}


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    """Delete a customer"""
    result = await db.execute(
        select(models.Customer).where(
            models.Customer.id == customer_id,
            models.Customer.tenant_id == DEFAULT_TENANT_ID
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    await db.delete(existing)
    await db.commit()
    
    return {"message": "Customer deleted", "id": str(customer_id)}

