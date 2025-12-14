from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import schemas
import models
import database
from services.gl_engine import post_journal_entry
from schemas.schemas_finance import JournalEntryCreate, JournalDetailCreate
from consumers.finance_consumer import get_account_id_by_code, ACCOUNT_MAP

router = APIRouter(
    prefix="/ar",
    tags=["Accounts Receivable"]
)

@router.post("/customers", response_model=schemas.CustomerResponse)
async def create_customer(payload: schemas.CustomerCreate, db: AsyncSession = Depends(database.get_db)):
    new_cust = models.Customer(**payload.dict())
    db.add(new_cust)
    await db.commit()
    await db.refresh(new_cust)
    return new_cust

@router.get("/customers", response_model=list[schemas.CustomerResponse])
async def list_customers(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Customer))
    return result.scalars().all()

@router.post("/invoices", response_model=schemas.SalesInvoiceResponse)
async def create_sales_invoice(payload: schemas.SalesInvoiceCreate, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch Customer & Check Credit Limit
    customer = await db.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    total_amount = sum(item.quantity * item.unit_price for item in payload.items)
    
    if customer.current_balance + total_amount > customer.credit_limit:
        raise HTTPException(
            status_code=400, 
            detail=f"Credit Limit Exceeded! Limit: {customer.credit_limit}, Balance: {customer.current_balance}, Attempted: {total_amount}"
        )

    # 2. Create Invoice
    new_inv = models.SalesInvoice(
        invoice_number=payload.invoice_number,
        customer_id=payload.customer_id,
        so_id=payload.so_id,
        date=payload.date,
        total_amount=total_amount,
        status=models.SalesInvoiceStatus.POSTED # Auto-post for now
    )
    db.add(new_inv)
    await db.flush()

    for item in payload.items:
        db.add(models.SalesInvoiceItem(
            invoice_id=new_inv.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price
        ))

    # 3. Update Balance
    customer.current_balance += total_amount
    
    # 4. GL Posting (Dr AR / Cr Sales)
    # We need AR Account and sales account.
    # Let's map AR to "1120" (Asset) and Sales to "4100" (Income)
    ar_acc_id = await get_account_id_by_code(db, "1120")
    sales_acc_id = await get_account_id_by_code(db, "4100")
    
    if ar_acc_id and sales_acc_id:
        entry = JournalEntryCreate(
            description=f"Sales Invoice {payload.invoice_number}",
            reference_id=str(new_inv.invoice_number),
            reference_type="Sales Invoice",
            details=[
                JournalDetailCreate(account_id=ar_acc_id, debit=total_amount, credit=0),
                JournalDetailCreate(account_id=sales_acc_id, debit=0, credit=total_amount)
            ]
        )
        await post_journal_entry(db, entry)

    await db.commit()
    await db.refresh(new_inv)
    return new_inv
