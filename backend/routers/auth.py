from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from typing import Annotated
import database, models, schemas, auth
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from services.email_service import generate_otp, get_otp_expiry, is_otp_valid, send_otp_email

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Additional schemas for OTP
class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

class MessageResponse(BaseModel):
    message: str
    email: str = None
    otp_code: str = None # For dev/testing purposes

@router.post("/register", response_model=MessageResponse)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(database.get_db)):
    # Check existing
    query = select(models.User).where(models.User.email == user.email)
    result = await db.execute(query)
    if result.scalar():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate OTP
    otp_code = generate_otp()
    otp_expires = get_otp_expiry()
    
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        username=user.username,
        role=user.role,
        password_hash=hashed_pw,
        tenant_id=user.tenant_id,
        is_verified=False,
        otp_code=otp_code,
        otp_expires_at=otp_expires
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Send OTP email
    await send_otp_email(user.email, otp_code, user.username)
    
    return {"message": "Registration successful. Please check your email for verification code.", "email": user.email}

@router.post("/send-otp", response_model=MessageResponse)
async def send_otp(request: OTPRequest, db: AsyncSession = Depends(database.get_db)):
    """Resend OTP code to user email"""
    query = select(models.User).where(models.User.email == request.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new OTP
    otp_code = generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = get_otp_expiry()
    await db.commit()
    
    # Send OTP email
    await send_otp_email(request.email, otp_code, user.username)
    
    return {"message": "Verification code sent to your email", "email": request.email, "otp_code": otp_code}

@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(request: OTPVerify, db: AsyncSession = Depends(database.get_db)):
    """Verify OTP code and activate user account"""
    query = select(models.User).where(models.User.email == request.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    if not is_otp_valid(user.otp_expires_at):
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    
    if user.otp_code != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    # Verify user
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    
    return {"message": "Email verified successfully. You can now login.", "email": request.email}

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "username": user.username,  # For frontend display
            "role": user.role.value if user.role else "STAFF",  # Ensure string value
            "tenant_id": str(user.tenant_id) if user.tenant_id else None
        }, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserResponse = Depends(auth.get_current_user)):
    return current_user
