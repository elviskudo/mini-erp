from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel

import schemas
import models
import database
from services.matching_engine import perform_3_way_match
from models.base import get_current_tenant

# Default tenant for MVP - in production, this should come from auth context
DEFAULT_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")

def get_tenant_id() -> uuid.UUID:
    """Get current tenant with fallback to default"""
    tenant = get_current_tenant()
    return tenant if tenant else DEFAULT_TENANT_ID

router = APIRouter(
    prefix="/ap",
    tags=["Accounts Payable"]
)

# Additional Schemas
class APPaymentCreate(BaseModel):
    vendor_id: str  # Accept as string, validate in endpoint
    invoice_id: Optional[str] = None  # Accept empty string or UUID string
    payment_date: str  # Accept as ISO date string
    payment_method: str
    amount: float
    bank_account_id: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


# === VENDOR BILLS ===

@router.get("/bills")
async def list_vendor_bills(
    status: Optional[str] = None,
    vendor_id: Optional[uuid.UUID] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(database.get_db)
):
    """List all vendor bills with filtering"""
    tenant_id = get_tenant_id()

    query = select(models.PurchaseInvoice).where(
        models.PurchaseInvoice.tenant_id == tenant_id
    ).options(selectinload(models.PurchaseInvoice.vendor))

    if status:
        query = query.where(models.PurchaseInvoice.status == status)
    if vendor_id:
        query = query.where(models.PurchaseInvoice.vendor_id == vendor_id)
    if date_from:
        query = query.where(models.PurchaseInvoice.date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(models.PurchaseInvoice.date <= datetime.fromisoformat(date_to))

    query = query.order_by(models.PurchaseInvoice.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    bills = result.scalars().all()

    return [
        {
            "id": str(b.id),
            "invoice_number": b.invoice_number,
            "vendor_id": str(b.vendor_id) if b.vendor_id else None,
            "vendor_name": b.vendor.name if b.vendor else None,
            "date": b.date.isoformat() if b.date else None,
            "due_date": b.due_date.isoformat() if b.due_date else None,
            "payment_terms": getattr(b, 'payment_terms', None),
            "currency_code": getattr(b, 'currency_code', 'IDR'),
            "subtotal": getattr(b, 'subtotal', 0) or 0,
            "tax_amount": getattr(b, 'tax_amount', 0) or 0,
            "total_amount": b.total_amount or 0,
            "amount_paid": getattr(b, 'amount_paid', 0) or 0,
            "amount_due": getattr(b, 'amount_due', b.total_amount) or 0,
            "status": b.status or "Draft",
            "notes": getattr(b, 'notes', None),
            "created_at": getattr(b, 'created_at', b.date).isoformat() if hasattr(b, 'created_at') and b.created_at else (b.date.isoformat() if b.date else None)
        } for b in bills
    ]


@router.post("/invoices", response_model=schemas.InvoiceResponse)
async def create_invoice(payload: schemas.InvoiceCreate, db: AsyncSession = Depends(database.get_db)):
    """Create a new vendor invoice/bill"""
    tenant_id = get_tenant_id()
    
    # Calculate Total from items, or use provided total_amount
    if payload.items:
        total = sum(item.quantity * item.unit_price for item in payload.items)
    else:
        total = payload.total_amount or 0
    
    # Default date to now if not provided
    invoice_date = payload.date or datetime.utcnow()
    
    new_inv = models.PurchaseInvoice(
        tenant_id=tenant_id,
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        po_id=payload.po_id,
        date=invoice_date,
        due_date=payload.due_date,
        total_amount=total,
        amount_due=total,
        amount_paid=0,
        status="Draft",
        notes=payload.notes
    )
    db.add(new_inv)
    await db.flush()
    
    for item in payload.items:
        inv_item = models.PurchaseInvoiceItem(
            tenant_id=tenant_id,
            invoice_id=new_inv.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price,
            po_item_id=item.po_item_id
        )
        db.add(inv_item)
        
    await db.commit()
    await db.refresh(new_inv)
    return new_inv


# Bill Update Schema
class BillUpdate(BaseModel):
    invoice_number: Optional[str] = None
    vendor_id: Optional[uuid.UUID] = None
    date: Optional[str] = None
    due_date: Optional[str] = None
    total_amount: Optional[float] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


@router.put("/bills/{bill_id}")
async def update_vendor_bill(
    bill_id: uuid.UUID,
    payload: BillUpdate,
    db: AsyncSession = Depends(database.get_db)
):
    """Update existing vendor bill"""
    tenant_id = get_tenant_id()
    result = await db.execute(
        select(models.PurchaseInvoice).where(
            models.PurchaseInvoice.id == bill_id,
            models.PurchaseInvoice.tenant_id == tenant_id
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Update fields if provided
    if payload.invoice_number is not None:
        existing.invoice_number = payload.invoice_number
    if payload.vendor_id is not None:
        existing.vendor_id = payload.vendor_id
    if payload.date is not None:
        existing.date = datetime.fromisoformat(payload.date.replace('Z', '+00:00')) if isinstance(payload.date, str) else payload.date
    if payload.due_date is not None:
        existing.due_date = datetime.fromisoformat(payload.due_date.replace('Z', '+00:00')) if isinstance(payload.due_date, str) else payload.due_date
    if payload.total_amount is not None:
        existing.total_amount = payload.total_amount
        existing.amount_due = payload.total_amount - (existing.amount_paid or 0)
    if payload.subtotal is not None:
        existing.subtotal = payload.subtotal
    if payload.tax_amount is not None:
        existing.tax_amount = payload.tax_amount
    if payload.payment_terms is not None:
        existing.payment_terms = payload.payment_terms
    if payload.notes is not None:
        existing.notes = payload.notes

    await db.commit()
    await db.refresh(existing)
    return {"message": "Bill updated", "id": str(existing.id)}


@router.post("/invoices/{id}/match")
async def match_invoice(id: str, db: AsyncSession = Depends(database.get_db)):
    """Run 3-way match for invoice"""
    try:
        result = await perform_3_way_match(db, id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# === AP PAYMENTS ===

@router.get("/payments")
async def list_ap_payments(
    vendor_id: Optional[uuid.UUID] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(database.get_db)
):
    """List AP payments"""
    tenant_id = get_tenant_id()

    query = select(models.models_ap.APPayment).where(
        models.models_ap.APPayment.tenant_id == tenant_id
    ).options(selectinload(models.models_ap.APPayment.vendor))

    if vendor_id:
        query = query.where(models.models_ap.APPayment.vendor_id == vendor_id)
    if date_from:
        query = query.where(models.models_ap.APPayment.payment_date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(models.models_ap.APPayment.payment_date <= datetime.fromisoformat(date_to))

    query = query.order_by(models.models_ap.APPayment.payment_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    payments = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "payment_number": p.payment_number,
            "vendor_id": str(p.vendor_id),
            "vendor_name": p.vendor.name if p.vendor else None,
            "invoice_id": str(p.invoice_id) if p.invoice_id else None,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "payment_method": p.payment_method.value if hasattr(p.payment_method, 'value') else str(p.payment_method),
            "amount": p.amount,
            "bank_account_id": str(p.bank_account_id) if p.bank_account_id else None,
            "reference_number": p.reference_number,
            "status": p.status or "completed",
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in payments
    ]


@router.post("/payments")
async def create_ap_payment(
    payment: APPaymentCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Create a new AP payment"""
    tenant_id = get_tenant_id()

    # Validate and convert vendor_id
    if not payment.vendor_id:
        raise HTTPException(status_code=400, detail="vendor_id is required")
    try:
        vendor_uuid = uuid.UUID(payment.vendor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vendor_id format")

    # Convert optional invoice_id
    invoice_uuid = None
    if payment.invoice_id and payment.invoice_id.strip():
        try:
            invoice_uuid = uuid.UUID(payment.invoice_id)
        except ValueError:
            pass  # Ignore invalid UUID, treat as no invoice

    # Convert bank_account_id
    bank_uuid = None
    if payment.bank_account_id and payment.bank_account_id.strip():
        try:
            bank_uuid = uuid.UUID(payment.bank_account_id)
        except ValueError:
            pass

    # Convert payment_date string to datetime
    try:
        payment_dt = datetime.fromisoformat(payment.payment_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment_date format")

    payment_number = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    new_payment = models.models_ap.APPayment(
        tenant_id=tenant_id,
        payment_number=payment_number,
        vendor_id=vendor_uuid,
        invoice_id=invoice_uuid,
        payment_date=payment_dt,
        payment_method=payment.payment_method,
        amount=payment.amount,
        amount_in_base_currency=payment.amount,
        bank_account_id=bank_uuid,
        reference_number=payment.reference_number,
        notes=payment.notes,
        status="completed"
    )
    db.add(new_payment)

    # Update invoice if linked
    if invoice_uuid:
        invoice_result = await db.execute(
            select(models.PurchaseInvoice).where(models.PurchaseInvoice.id == invoice_uuid)
        )
        invoice = invoice_result.scalar_one_or_none()
        if invoice:
            invoice.amount_paid = (getattr(invoice, 'amount_paid', 0) or 0) + payment.amount
            invoice.amount_due = (invoice.total_amount or 0) - invoice.amount_paid
            if invoice.amount_due <= 0:
                invoice.status = "Paid"
            elif invoice.amount_paid > 0:
                invoice.status = "Partially Paid"

    await db.commit()
    await db.refresh(new_payment)

    return {
        "id": str(new_payment.id),
        "payment_number": new_payment.payment_number,
        "amount": new_payment.amount,
        "status": new_payment.status
    }


# === AP AGING ===

@router.get("/aging")
async def get_ap_aging(
    as_of_date: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db)
):
    """Get AP aging report"""
    tenant_id = get_tenant_id()

    reference_date = datetime.fromisoformat(as_of_date) if as_of_date else datetime.utcnow()

    # Get unpaid bills
    result = await db.execute(
        select(models.PurchaseInvoice).where(
            models.PurchaseInvoice.tenant_id == tenant_id
        ).options(selectinload(models.PurchaseInvoice.vendor))
    )
    bills = result.scalars().all()

    # Filter bills with outstanding balance
    unpaid_bills = [b for b in bills if (getattr(b, 'amount_due', b.total_amount) or 0) > 0]

    # Calculate aging buckets
    buckets = {"current": 0, "days_1_30": 0, "days_31_60": 0, "days_61_90": 0, "over_90": 0}
    bucket_counts = {"current": 0, "days_1_30": 0, "days_31_60": 0, "days_61_90": 0, "over_90": 0}
    vendor_breakdown = {}

    for bill in unpaid_bills:
        due_date = bill.due_date or bill.date
        if not due_date:
            continue
        days_overdue = (reference_date - due_date).days
        amount = getattr(bill, 'amount_due', bill.total_amount) or 0

        vendor_name = bill.vendor.name if bill.vendor else "Unknown"
        if vendor_name not in vendor_breakdown:
            vendor_breakdown[vendor_name] = {"current": 0, "days_1_30": 0, "days_31_60": 0, "days_61_90": 0, "over_90": 0, "total": 0}

        if days_overdue <= 0:
            buckets["current"] += amount
            bucket_counts["current"] += 1
            vendor_breakdown[vendor_name]["current"] += amount
        elif days_overdue <= 30:
            buckets["days_1_30"] += amount
            bucket_counts["days_1_30"] += 1
            vendor_breakdown[vendor_name]["days_1_30"] += amount
        elif days_overdue <= 60:
            buckets["days_31_60"] += amount
            bucket_counts["days_31_60"] += 1
            vendor_breakdown[vendor_name]["days_31_60"] += amount
        elif days_overdue <= 90:
            buckets["days_61_90"] += amount
            bucket_counts["days_61_90"] += 1
            vendor_breakdown[vendor_name]["days_61_90"] += amount
        else:
            buckets["over_90"] += amount
            bucket_counts["over_90"] += 1
            vendor_breakdown[vendor_name]["over_90"] += amount

        vendor_breakdown[vendor_name]["total"] += amount

    vendors = [{"vendor": k, **v} for k, v in vendor_breakdown.items()]

    return {
        "as_of_date": reference_date.isoformat(),
        "buckets": [
            {"label": "Current", "amount": buckets["current"], "count": bucket_counts["current"]},
            {"label": "1-30 Days", "amount": buckets["days_1_30"], "count": bucket_counts["days_1_30"]},
            {"label": "31-60 Days", "amount": buckets["days_31_60"], "count": bucket_counts["days_31_60"]},
            {"label": "61-90 Days", "amount": buckets["days_61_90"], "count": bucket_counts["days_61_90"]},
            {"label": "> 90 Days", "amount": buckets["over_90"], "count": bucket_counts["over_90"]}
        ],
        "total": sum(buckets.values()),
        "vendors": vendors
    }

