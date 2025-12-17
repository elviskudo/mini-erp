"""
User Management API - CRUD operations for tenant users
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from passlib.context import CryptContext

import database
from auth import get_current_user
from models.user import User, UserRole

router = APIRouter(prefix="/users", tags=["Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Schemas
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    is_verified: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    role: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None


# Endpoints
@router.get("", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users in current tenant"""
    # Only managers/admins can view all users
    if current_user.role.value not in ['ADMIN', 'MANAGER']:
        raise HTTPException(status_code=403, detail="Not authorized to view users")
    
    tenant_id = current_user.tenant_id
    
    if tenant_id:
        result = await db.execute(
            select(User).where(User.tenant_id == tenant_id).order_by(User.username)
        )
    else:
        result = await db.execute(select(User).order_by(User.username))
    
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role.value if u.role else 'STAFF',
            is_verified=u.is_verified
        )
        for u in users
    ]


@router.post("", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user in current tenant"""
    if current_user.role.value not in ['ADMIN', 'MANAGER']:
        raise HTTPException(status_code=403, detail="Not authorized to create users")
    
    # Check if username/email exists
    existing = await db.execute(
        select(User).where((User.username == user.username) | (User.email == user.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Validate role
    try:
        role_enum = UserRole[user.role]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {user.role}")
    
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=pwd_context.hash(user.password),
        role=role_enum,
        tenant_id=current_user.tenant_id,
        is_verified=True  # Created by manager, no email verification needed
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role.value,
        is_verified=new_user.is_verified
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    if current_user.role.value not in ['ADMIN', 'MANAGER']:
        raise HTTPException(status_code=403, detail="Not authorized to update users")
    
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ensure same tenant
    if db_user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cannot modify user from different tenant")
    
    if user.username:
        db_user.username = user.username
    if user.email:
        db_user.email = user.email
    if user.role:
        try:
            db_user.role = UserRole[user.role]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {user.role}")
    if user.password:
        db_user.password_hash = pwd_context.hash(user.password)
    
    await db.commit()
    await db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role.value,
        is_verified=db_user.is_verified
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user"""
    if current_user.role.value not in ['ADMIN', 'MANAGER']:
        raise HTTPException(status_code=403, detail="Not authorized to delete users")
    
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ensure same tenant
    if db_user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cannot delete user from different tenant")
    
    # Prevent self-deletion
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await db.delete(db_user)
    await db.commit()
    
    return {"message": "User deleted successfully"}
