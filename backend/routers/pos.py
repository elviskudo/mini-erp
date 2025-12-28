"""
POS API Router - Point of Sale endpoints for products, customers, transactions, and promos
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
import uuid as uuid_module
import cloudinary
import cloudinary.uploader

import database
import models
from models.models_pos import POSTransaction, TransactionLog, Promo, PaymentMethod, TransactionStatus, TransactionLogType, PromoType
from models.models_sales import Customer
from models.models_manufacturing import Product
from models.models_settings import TenantSettings
from auth import get_current_user

router = APIRouter(
    prefix="/pos",
    tags=["POS"]
)


# ==================== SCHEMAS ====================

class ProductPOSResponse(BaseModel):
    id: UUID
    code: str
    name: str
    category: Optional[str] = None
    unit_price: float
    image_url: Optional[str] = None
    stock_qty: Optional[float] = 0
    
    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: Optional[str] = None
    ktp_number: Optional[str] = None
    birth_date: Optional[datetime] = None
    credit_limit: Optional[float] = 0


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    ktp_number: Optional[str] = None
    ktp_image_url: Optional[str] = None
    credit_limit: float = 0
    current_balance: float = 0
    
    class Config:
        from_attributes = True


class TransactionItemCreate(BaseModel):
    product_id: UUID
    name: str
    quantity: float
    unit_price: float


class TransactionCreate(BaseModel):
    customer_id: Optional[UUID] = None
    items: List[TransactionItemCreate]
    promo_code: Optional[str] = None
    payment_method: str = "CASH"
    payment_reference: Optional[str] = None


class TransactionResponse(BaseModel):
    id: UUID
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    items: list
    subtotal: float
    discount: float
    tax: float
    total: float
    payment_method: str
    promo_code: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PromoResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    promo_type: str
    value: float
    min_order: float = 0
    max_discount: Optional[float] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True


# ==================== SETTINGS ====================

@router.get("/settings")
async def get_pos_settings(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get tenant settings for POS (currency, etc.)"""
    result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == current_user.tenant_id)
    )
    settings = result.scalar_one_or_none()
    
    # Default values if no settings exist
    if not settings:
        return {
            "currency_code": "IDR",
            "currency_symbol": "Rp",
            "currency_position": "before",
            "decimal_separator": ",",
            "thousand_separator": ".",
            "decimal_places": "0",
            "timezone": "Asia/Jakarta",
            "company_name": current_user.tenant_id
        }
    
    return {
        "currency_code": settings.currency_code or "IDR",
        "currency_symbol": settings.currency_symbol or "Rp",
        "currency_position": settings.currency_position or "before",
        "decimal_separator": settings.decimal_separator or ",",
        "thousand_separator": settings.thousand_separator or ".",
        "decimal_places": settings.decimal_places or "0",
        "timezone": settings.timezone or "Asia/Jakarta",
        "company_name": settings.company_name
    }


# ==================== PRODUCTS ====================

@router.get("/products", response_model=List[ProductPOSResponse])
async def get_pos_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get products that passed QC inspection for POS display"""
    # Get products with passed QC
    query = select(Product).where(
        Product.tenant_id == current_user.tenant_id,
        Product.is_active == True
    )
    
    if category:
        query = query.where(Product.category == category)
    
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return [
        ProductPOSResponse(
            id=p.id,
            code=p.code or "",
            name=p.name,
            category=p.category,
            unit_price=p.suggested_selling_price or 0,
            image_url=getattr(p, 'image_url', None),
            stock_qty=0  # TODO: Get from inventory
        ) for p in products
    ]


@router.get("/categories")
async def get_product_categories(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get distinct product categories"""
    result = await db.execute(
        select(Product.category).where(
            Product.tenant_id == current_user.tenant_id,
            Product.category.isnot(None)
        ).distinct()
    )
    categories = [row[0] for row in result.all() if row[0]]
    return {"categories": categories}


# ==================== CUSTOMERS ====================

@router.post("/customer", response_model=CustomerResponse)
async def create_customer(
    name: str = Form(...),
    email: Optional[str] = Form(None),  # Email is now optional
    phone: str = Form(...),
    address: Optional[str] = Form(None),
    ktp_number: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None),
    credit_limit: float = Form(0),
    ktp_image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create new customer with optional KTP image upload to Cloudinary"""
    
    # Upload KTP image to Cloudinary if provided
    ktp_image_url = None
    if ktp_image:
        try:
            contents = await ktp_image.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder=f"mini-erp/{current_user.tenant_id}/ktp",
                resource_type="image"
            )
            ktp_image_url = upload_result.get("secure_url")
        except Exception as e:
            # Log error but don't fail the request
            print(f"Cloudinary upload error: {e}")
    
    # Parse birth_date if provided
    parsed_birth_date = None
    if birth_date:
        try:
            parsed_birth_date = datetime.fromisoformat(birth_date.replace("Z", "+00:00"))
        except:
            pass
    
    customer = Customer(
        id=uuid_module.uuid4(),
        tenant_id=current_user.tenant_id,
        name=name,
        email=email,
        phone=phone,
        address=address,
        ktp_number=ktp_number,
        ktp_image_url=ktp_image_url,
        birth_date=parsed_birth_date,
        credit_limit=credit_limit,
        current_balance=credit_limit  # Start with full balance
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    
    return customer


@router.get("/customer/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get customer by ID with balance info"""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.get("/customers/search")
async def search_customers(
    q: str,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Search customers by name, email, phone, or KTP number"""
    result = await db.execute(
        select(Customer).where(
            Customer.tenant_id == current_user.tenant_id,
            func.lower(Customer.name).contains(q.lower()) |
            func.lower(Customer.email).contains(q.lower()) |
            Customer.phone.contains(q) |
            Customer.ktp_number.contains(q)
        ).limit(10)
    )
    customers = result.scalars().all()
    return [CustomerResponse.model_validate(c) for c in customers]


@router.post("/customer/{customer_id}/topup")
async def topup_customer_credit(
    customer_id: UUID,
    amount: float = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add credit to customer balance (top-up)"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Add to current balance
    old_balance = customer.current_balance or 0
    customer.current_balance = old_balance + amount
    
    await db.commit()
    await db.refresh(customer)
    
    return {
        "message": "Top-up successful",
        "customer_id": str(customer_id),
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": customer.current_balance,
        "notes": notes
    }


@router.put("/customer/{customer_id}")
async def update_customer(
    customer_id: UUID,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    credit_limit: Optional[float] = Form(None),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update customer details"""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if name: customer.name = name
    if email: customer.email = email
    if phone: customer.phone = phone
    if address: customer.address = address
    if credit_limit is not None: customer.credit_limit = credit_limit
    
    await db.commit()
    await db.refresh(customer)
    
    return CustomerResponse.model_validate(customer)


# ==================== TRANSACTIONS ====================

@router.post("/transaction", response_model=TransactionResponse)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new POS transaction"""
    
    # Calculate subtotal
    subtotal = sum(item.quantity * item.unit_price for item in payload.items)
    discount = 0
    promo_id = None
    
    # Apply promo if provided
    if payload.promo_code:
        promo_result = await db.execute(
            select(Promo).where(
                Promo.tenant_id == current_user.tenant_id,
                Promo.code == payload.promo_code,
                Promo.is_active == True
            )
        )
        promo = promo_result.scalar_one_or_none()
        
        if promo:
            if subtotal >= promo.min_order:
                if promo.promo_type == PromoType.FIXED:
                    discount = promo.value
                elif promo.promo_type == PromoType.PERCENTAGE:
                    discount = subtotal * (promo.value / 100)
                    if promo.max_discount:
                        discount = min(discount, promo.max_discount)
                
                promo_id = promo.id
                promo.usage_count += 1
    
    # Calculate tax (10%)
    tax = (subtotal - discount) * 0.1
    total = subtotal - discount + tax
    
    # Parse payment method
    try:
        payment_method = PaymentMethod[payload.payment_method.upper()]
    except KeyError:
        payment_method = PaymentMethod.CASH
    
    # Get customer for balance check if paying with credit
    customer = None
    if payload.customer_id:
        cust_result = await db.execute(
            select(Customer).where(Customer.id == payload.customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        
        if payment_method == PaymentMethod.CREDIT:
            if not customer:
                raise HTTPException(status_code=400, detail="Customer required for credit payment")
            if customer.current_balance < total:
                raise HTTPException(status_code=400, detail="Insufficient credit balance")
    
    # Create transaction
    items_json = [
        {
            "product_id": str(item.product_id),
            "name": item.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.quantity * item.unit_price
        }
        for item in payload.items
    ]
    
    transaction = POSTransaction(
        id=uuid_module.uuid4(),
        tenant_id=current_user.tenant_id,
        customer_id=payload.customer_id,
        cashier_id=current_user.id,
        items=items_json,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        total=total,
        payment_method=payment_method,
        payment_reference=payload.payment_reference,
        promo_id=promo_id,
        promo_code=payload.promo_code,
        status=TransactionStatus.COMPLETED
    )
    db.add(transaction)
    
    # Update customer balance if paying with credit
    if payment_method == PaymentMethod.CREDIT and customer:
        balance_before = customer.current_balance
        customer.current_balance -= total
        
        # Log the transaction
        log = TransactionLog(
            id=uuid_module.uuid4(),
            tenant_id=current_user.tenant_id,
            customer_id=customer.id,
            transaction_id=transaction.id,
            log_type=TransactionLogType.DEBIT,
            amount=total,
            balance_before=balance_before,
            balance_after=customer.current_balance,
            description=f"POS Purchase - {len(payload.items)} items",
            created_by=current_user.id
        )
        db.add(log)
    
    # If payment received (CASH, QRIS, STRIPE), add to customer credit
    elif customer and payment_method in [PaymentMethod.CASH, PaymentMethod.QRIS, PaymentMethod.STRIPE]:
        balance_before = customer.current_balance
        customer.current_balance += total
        
        log = TransactionLog(
            id=uuid_module.uuid4(),
            tenant_id=current_user.tenant_id,
            customer_id=customer.id,
            transaction_id=transaction.id,
            log_type=TransactionLogType.CREDIT,
            amount=total,
            balance_before=balance_before,
            balance_after=customer.current_balance,
            description=f"Payment received via {payment_method.value}",
            created_by=current_user.id
        )
        db.add(log)
    
    await db.commit()
    await db.refresh(transaction)
    
    return TransactionResponse(
        id=transaction.id,
        customer_id=transaction.customer_id,
        customer_name=customer.name if customer else None,
        items=transaction.items,
        subtotal=transaction.subtotal,
        discount=transaction.discount,
        tax=transaction.tax,
        total=transaction.total,
        payment_method=transaction.payment_method.value,
        promo_code=transaction.promo_code,
        status=transaction.status.value,
        created_at=transaction.created_at
    )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get recent transactions"""
    result = await db.execute(
        select(POSTransaction).where(
            POSTransaction.tenant_id == current_user.tenant_id
        ).order_by(POSTransaction.created_at.desc()).limit(limit)
    )
    transactions = result.scalars().all()
    
    return [
        TransactionResponse(
            id=t.id,
            customer_id=t.customer_id,
            items=t.items,
            subtotal=t.subtotal,
            discount=t.discount,
            tax=t.tax,
            total=t.total,
            payment_method=t.payment_method.value,
            promo_code=t.promo_code,
            status=t.status.value,
            created_at=t.created_at
        ) for t in transactions
    ]


# ==================== PROMOS ====================

@router.get("/promos", response_model=List[PromoResponse])
async def get_active_promos(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get active promos for POS"""
    now = datetime.utcnow()
    result = await db.execute(
        select(Promo).where(
            Promo.tenant_id == current_user.tenant_id,
            Promo.is_active == True,
            (Promo.start_date.is_(None) | (Promo.start_date <= now)),
            (Promo.end_date.is_(None) | (Promo.end_date >= now)),
            (Promo.usage_limit.is_(None) | (Promo.usage_count < Promo.usage_limit))
        )
    )
    promos = result.scalars().all()
    
    return [
        PromoResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            promo_type=p.promo_type.value,
            value=p.value,
            min_order=p.min_order,
            max_discount=p.max_discount,
            is_active=p.is_active
        ) for p in promos
    ]


@router.post("/promos/validate")
async def validate_promo(
    code: str,
    order_amount: float,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Validate a promo code and calculate discount"""
    now = datetime.utcnow()
    result = await db.execute(
        select(Promo).where(
            Promo.tenant_id == current_user.tenant_id,
            Promo.code == code,
            Promo.is_active == True
        )
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        return {"valid": False, "error": "Promo code not found"}
    
    if promo.start_date and promo.start_date > now:
        return {"valid": False, "error": "Promo not yet active"}
    
    if promo.end_date and promo.end_date < now:
        return {"valid": False, "error": "Promo has expired"}
    
    if promo.usage_limit and promo.usage_count >= promo.usage_limit:
        return {"valid": False, "error": "Promo usage limit reached"}
    
    if order_amount < promo.min_order:
        return {"valid": False, "error": f"Minimum order amount is {promo.min_order}"}
    
    # Calculate discount
    discount = 0
    if promo.promo_type == PromoType.FIXED:
        discount = promo.value
    elif promo.promo_type == PromoType.PERCENTAGE:
        discount = order_amount * (promo.value / 100)
        if promo.max_discount:
            discount = min(discount, promo.max_discount)
    
    return {
        "valid": True,
        "promo": {
            "code": promo.code,
            "name": promo.name,
            "type": promo.promo_type.value,
            "value": promo.value,
            "discount": round(discount, 2)
        }
    }
