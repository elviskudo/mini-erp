from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import models
import database
from services.matching_engine import perform_3_way_match

router = APIRouter(
    prefix="/ap",
    tags=["Accounts Payable"]
)

@router.post("/invoices", response_model=schemas.InvoiceResponse)
async def create_invoice(payload: schemas.InvoiceCreate, db: AsyncSession = Depends(database.get_db)):
    # Calculate Total
    total = sum(item.quantity * item.unit_price for item in payload.items)
    
    new_inv = models.PurchaseInvoice(
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        po_id=payload.po_id,
        date=payload.date,
        due_date=payload.due_date,
        total_amount=total
    )
    db.add(new_inv)
    await db.flush()
    
    for item in payload.items:
        inv_item = models.PurchaseInvoiceItem(
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

@router.post("/invoices/{id}/match")
async def match_invoice(id: str, db: AsyncSession = Depends(database.get_db)):
    # Run the engine
    try:
        result = await perform_3_way_match(db, id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
