from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
import models
from datetime import datetime
import schemas
from connections.rabbitmq_utils import get_rabbitmq_connection
import json
import aio_pika

async def post_journal_entry(db: AsyncSession, entry_data: schemas.JournalEntryCreate, user_id=None):
    # 1. Validate Balance
    total_debit = sum(d.debit for d in entry_data.details)
    total_credit = sum(d.credit for d in entry_data.details)
    
    if abs(total_debit - total_credit) > 0.01: # Floating point tolerance
        raise HTTPException(status_code=400, detail="Journal Entry is not balanced")

    # 2. Check Fiscal Period (Simplified)
    # Ideally find period by date and check is_closed
    # For MVP: Just check if *any* closed period covers this date
    # query = select(models.FiscalPeriod).where(
    #     models.FiscalPeriod.start_date <= entry_data.date, 
    #     models.FiscalPeriod.end_date >= entry_data.date,
    #     models.FiscalPeriod.is_closed == True
    # )
    # ... if result: raise HTTPException ...

    # 3. Create Entry
    new_entry = models.JournalEntry(
        date=entry_data.date,
        description=entry_data.description,
        reference_id=entry_data.reference_id,
        reference_type=entry_data.reference_type,
        posted_by=user_id
    )
    db.add(new_entry)
    await db.flush() # Get ID

    # 4. Create Details
    for d in entry_data.details:
        detail = models.JournalDetail(
            journal_entry_id=new_entry.id,
            account_id=d.account_id,
            debit=d.debit,
            credit=d.credit
        )
        db.add(detail)
    
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

    return new_entry
