"""
SaaS Router - Multi-tenant onboarding endpoints

Endpoints:
- POST /saas/register-tenant - Register new company
- POST /saas/register-owner - Register owner for a tenant
- GET /saas/find-company/{code} - Find company by code
- POST /saas/request-join - Request to join a company
- GET /saas/pending-members - List pending join requests
- POST /saas/approve-member - Approve/reject member request
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from passlib.context import CryptContext
import uuid

import database
import models
from models.models_saas import Tenant, TenantMember, MemberRole, SubscriptionTier
from models.user import User, UserRole
from services.email_service import generate_otp, get_otp_expiry, send_otp_email


router = APIRouter(prefix="/saas", tags=["SaaS Onboarding"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============== Schemas ==============

class RegisterTenantRequest(BaseModel):
    name: str
    domain: Optional[str] = None
    currency: Optional[str] = "USD"
    timezone: Optional[str] = "UTC"


class RegisterTenantResponse(BaseModel):
    id: str
    name: str
    company_code: str
    domain: Optional[str]

    class Config:
        from_attributes = True


class RegisterOwnerRequest(BaseModel):
    tenant_id: str
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class RegisterOwnerResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    message: str


class FindCompanyResponse(BaseModel):
    id: str
    name: str
    company_code: str
    domain: Optional[str]


class RequestJoinRequest(BaseModel):
    company_code: str
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class PendingMemberResponse(BaseModel):
    id: str
    user_id: str
    username: str
    email: str
    invited_at: datetime
    role: str


class ApproveMemberRequest(BaseModel):
    member_id: str
    approve: bool


# ============== Endpoints ==============

@router.post("/register-tenant", response_model=RegisterTenantResponse)
async def register_tenant(
    request: RegisterTenantRequest,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Step 1: Register a new company/tenant.
    Returns the tenant info including unique company_code for employees to join.
    """
    # Check if domain already exists
    if request.domain:
        result = await db.execute(
            select(Tenant).where(Tenant.domain == request.domain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already registered"
            )
    
    # Create tenant
    tenant = Tenant(
        name=request.name,
        domain=request.domain,
        currency=request.currency or "USD",
        timezone=request.timezone or "UTC",
        tier=SubscriptionTier.FREE_TRIAL
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    return RegisterTenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        company_code=tenant.company_code,
        domain=tenant.domain
    )


@router.post("/register-owner", response_model=RegisterOwnerResponse)
async def register_owner(
    request: RegisterOwnerRequest,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Step 2: Register the owner/admin for a tenant.
    Creates user and links as OWNER in tenant_members.
    """
    # Validate tenant exists
    tenant_uuid = uuid.UUID(request.tenant_id)
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_uuid)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check if tenant already has an owner
    result = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_uuid,
            TenantMember.role == MemberRole.OWNER
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant already has an owner"
        )
    
    # Check if username/email already exists
    result = await db.execute(
        select(User).where(
            (User.username == request.username) | (User.email == request.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create user with OTP
    otp_code = generate_otp()
    otp_expires = get_otp_expiry()
    
    user = User(
        username=request.username,
        email=request.email,
        password_hash=pwd_context.hash(request.password),
        role=UserRole.ADMIN,
        tenant_id=tenant_uuid,
        is_verified=False,
        otp_code=otp_code,
        otp_expires_at=otp_expires
    )
    db.add(user)
    await db.flush()  # Get user.id
    
    # Create tenant member (OWNER)
    member = TenantMember(
        tenant_id=tenant_uuid,
        user_id=user.id,
        role=MemberRole.OWNER,
        joined_at=datetime.utcnow()
    )
    db.add(member)
    
    await db.commit()
    
    # Send OTP email
    await send_otp_email(request.email, otp_code, request.username)
    
    return RegisterOwnerResponse(
        user_id=str(user.id),
        tenant_id=str(tenant_uuid),
        email=request.email,
        message="Owner registered. Please verify your email."
    )


@router.get("/find-company/{code}", response_model=FindCompanyResponse)
async def find_company(
    code: str,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Step 3 (Employee flow): Find company by unique code.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.company_code == code.upper())
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return FindCompanyResponse(
        id=str(tenant.id),
        name=tenant.name,
        company_code=tenant.company_code,
        domain=tenant.domain
    )


@router.post("/request-join", response_model=RegisterOwnerResponse)
async def request_join(
    request: RequestJoinRequest,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Step 3 (Employee flow): Request to join a company.
    Creates user with PENDING status, owner must approve.
    """
    # Find tenant
    result = await db.execute(
        select(Tenant).where(Tenant.company_code == request.company_code.upper())
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if username/email already exists
    result = await db.execute(
        select(User).where(
            (User.username == request.username) | (User.email == request.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create user with OTP
    otp_code = generate_otp()
    otp_expires = get_otp_expiry()
    
    user = User(
        username=request.username,
        email=request.email,
        password_hash=pwd_context.hash(request.password),
        role=UserRole.OPERATOR,
        tenant_id=tenant.id,
        is_verified=False,
        otp_code=otp_code,
        otp_expires_at=otp_expires
    )
    db.add(user)
    await db.flush()
    
    # Create tenant member (PENDING)
    member = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=MemberRole.PENDING
    )
    db.add(member)
    
    await db.commit()
    
    # Send OTP email
    await send_otp_email(request.email, otp_code, request.username)
    
    return RegisterOwnerResponse(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=request.email,
        message="Join request submitted. Verify email and wait for owner approval."
    )


@router.get("/pending-members", response_model=List[PendingMemberResponse])
async def get_pending_members(
    tenant_id: str,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Get list of pending member requests for a tenant.
    Owner/Admin only (should add auth check).
    """
    tenant_uuid = uuid.UUID(tenant_id)
    
    result = await db.execute(
        select(TenantMember, User)
        .join(User, TenantMember.user_id == User.id)
        .where(
            TenantMember.tenant_id == tenant_uuid,
            TenantMember.role == MemberRole.PENDING
        )
    )
    
    members = []
    for member, user in result.all():
        members.append(PendingMemberResponse(
            id=str(member.id),
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            invited_at=member.invited_at,
            role=member.role.value
        ))
    
    return members


@router.post("/approve-member")
async def approve_member(
    request: ApproveMemberRequest,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Approve or reject a pending member request.
    Owner/Admin only (should add auth check).
    """
    member_uuid = uuid.UUID(request.member_id)
    
    result = await db.execute(
        select(TenantMember).where(
            TenantMember.id == member_uuid,
            TenantMember.role == MemberRole.PENDING
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending member not found"
        )
    
    if request.approve:
        member.role = MemberRole.MEMBER
        member.joined_at = datetime.utcnow()
        await db.commit()
        return {"message": "Member approved", "status": "approved"}
    else:
        await db.delete(member)
        await db.commit()
        return {"message": "Member request rejected", "status": "rejected"}
