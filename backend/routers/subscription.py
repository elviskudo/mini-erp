from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import database, models, schemas
from utils.stripe_utils import create_checkout_session
from models.models_saas import SubscriptionTier, Tenant
from dependencies import get_current_tenant_id

router = APIRouter(
    prefix="/subscription",
    tags=["SaaS Billing"]
)

@router.post("/checkout")
async def checkout(
    tier: SubscriptionTier, 
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(database.get_db)
):
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    
    # Mock URLs
    success = "http://localhost:3000/settings/billing/success"
    cancel = "http://localhost:3000/settings/billing/cancel"
    
    url = create_checkout_session(tier, tenant_id, success, cancel)
    return {"url": url}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(database.get_db)):
    # In real app: Verify Signature!
    payload = await request.json()
    
    # Simple Mock Logic for 'invoice.payment_succeeded' or checkout.session.completed
    event_type = payload.get("type")
    
    if event_type == "checkout.session.completed":
        data = payload.get("data", {}).get("object", {})
        tenant_id = data.get("client_reference_id")
        # Metadata is safer
        
        if tenant_id:
            tenant = await db.get(models.Tenant, tenant_id)
            if tenant:
                tenant.subscription_status = "active"
                # Update tier if in metadata
                await db.commit()
                
    return {"status": "received"}
