from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Union
from uuid import UUID
from enum import Enum
from datetime import datetime
import re

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    PRODUCTION = "PRODUCTION"
    WAREHOUSE = "WAREHOUSE"
    STAFF = "STAFF"
    PROCUREMENT = "PROCUREMENT"
    FINANCE = "FINANCE"
    HR = "HR"
    LAB_TECH = "LAB_TECH"

class UserBase(BaseModel):
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description="Username must be 3-50 characters"
    )
    email: EmailStr = Field(..., description="Valid email address required")
    role: UserRole = UserRole.STAFF

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=6, 
        max_length=72,  # bcrypt limit
        description="Password must be 6-72 characters"
    )
    tenant_id: Optional[UUID] = Field(None, description="Tenant/Organization ID")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 72:
            raise ValueError('Password cannot exceed 72 characters (bcrypt limit)')
        return v

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(
        ..., 
        min_length=1, 
        max_length=72,
        description="Password"
    )

class UserResponse(UserBase):
    id: UUID
    tenant_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None
    role: Union[str, None] = None
    tenant_id: Union[str, None] = None
