from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
import models
from datetime import datetime
import schemas
from connections.rabbitmq_utils import get_rabbitmq_connection
import json
import aio_pika
import uuid

# Default tenant ID for MVP (should come from auth in production)
DEFAULT_TENANT_ID = uuid.UUID("6c812e6d-da95-49e8-8510-cc36b196bdb6")

async def post_journal_entry(db: AsyncSession, entry_data: schemas.JournalEntryCreate, user_id=None):
    # Get details using helper method
    details = entry_data.get_details()
    
    if not details:
        raise HTTPException(status_code=400, detail="Journal entry must have at least one detail line")
    
    # 1. Validate Balance
    total_debit = sum(d.debit or 0 for d in details)
    total_credit = sum(d.credit or 0 for d in details)
    
    if abs(total_debit - total_credit) > 0.01: # Floating point tolerance
        raise HTTPException(status_code=400, detail="Journal Entry is not balanced")

    # 2. Check Fiscal Period (Simplified) - Skipped for MVP

    # 3. Create Entry
    entry_date = entry_data.date or datetime.utcnow()
    new_entry = models.JournalEntry(
        tenant_id=DEFAULT_TENANT_ID,
        date=entry_date,
        description=entry_data.description,
        reference_id=entry_data.get_reference_id(),
        reference_type=entry_data.reference_type,
        posted_by=user_id
    )
    db.add(new_entry)
    await db.flush() # Get ID

    # 4. Create Details
    # Store details for response
    created_details = []
    for d in details:
        detail_id = uuid.uuid4()  # Generate ID upfront
        detail = models.JournalDetail(
            id=detail_id,
            tenant_id=DEFAULT_TENANT_ID,
            journal_entry_id=new_entry.id,
            account_id=d.account_id,
            debit=d.debit or 0,
            credit=d.credit or 0
        )
        db.add(detail)
        created_details.append({
            "id": detail_id,
            "account_id": d.account_id,
            "debit": d.debit or 0,
            "credit": d.credit or 0
        })
    
    await db.commit()
    await db.refresh(new_entry)

    # 5. Broadcast Event via RabbitMQ
    try:
        connection = await get_rabbitmq_connection()
        channel = await connection.channel()
        
        # Declare exchange if not exists
        exchange = await channel.declare_exchange("erp_events", type="topic")
        
        message = {
            "event": "new_journal_entry",
            "data": {
                "id": str(new_entry.id),
                "description": new_entry.description,
                "amount": total_debit
            }
        }
        
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key="finance.journal.created"
        )
    except Exception as e:
        print(f"Failed to publish event: {e}") 
        # Non-blocking failure

    # Return dict to avoid MissingGreenlet error
    return {
        "id": new_entry.id,
        "date": new_entry.date,
        "description": new_entry.description,
        "reference_id": new_entry.reference_id,
        "details": created_details
    }
