import asyncio
import json
import aio_pika
from connections.rabbitmq_utils import get_rabbitmq_connection
from database import SessionLocal
from services.gl_engine import post_journal_entry
from schemas.schemas_finance import JournalEntryCreate, JournalDetailCreate
import models
from sqlalchemy.future import select

# Mock Account Mapping for MVP
# In real app, this comes from a Settings table
ACCOUNT_MAP = {
    "INVENTORY": "1130", # Inventory Asset
    "GRN_CLEARING": "2100", # AP Liability (Simulated)
    "COGS": "5100", # Cost of Goods Sold
    "SALES": "4100" # Revenue
}

async def get_account_id_by_code(db, code):
    result = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == code))
    acc = result.scalar_one_or_none()
    return acc.id if acc else None

async def process_inventory_event(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        event_type = data.get("event")
        payload = data.get("data")
        
        print(f"[Finance Consumer] Received: {event_type} - {payload['type']}")

        if event_type == "inventory.movement":
            move_type = payload["type"]
            quantity = float(payload["quantity"])
            ref_id = payload["ref_id"]
            
            # Simple Costing: Assume standard cost of $10 per unit for MVP
            # In Phase 3.7 we will look up actual cost
            UNIT_COST = 10.0 
            total_value = abs(quantity) * UNIT_COST
            
            async with SessionLocal() as db:
                inventory_acc_id = await get_account_id_by_code(db, ACCOUNT_MAP["INVENTORY"])
                contra_acc_id = None
                
                debit_acc = None
                credit_acc = None

                description = ""

                if move_type == "IN_RECEIPT":
                    # Dr Inventory, Cr AP/GRN Clearing
                    contra_acc_id = await get_account_id_by_code(db, ACCOUNT_MAP["GRN_CLEARING"])
                    debit_acc = inventory_acc_id
                    credit_acc = contra_acc_id
                    description = f"Auto-Post: Goods Receipt {ref_id}"
                
                elif move_type == "OUT_DELIVERY":
                    # Dr COGS, Cr Inventory
                    contra_acc_id = await get_account_id_by_code(db, ACCOUNT_MAP["COGS"])
                    debit_acc = contra_acc_id
                    credit_acc = inventory_acc_id
                    description = f"Auto-Post: Delivery {ref_id}"
                
                if debit_acc and credit_acc:
                    entry = JournalEntryCreate(
                        description=description,
                        reference_id=ref_id,
                        reference_type="Inventory",
                        details=[
                            JournalDetailCreate(account_id=debit_acc, debit=total_value, credit=0),
                            JournalDetailCreate(account_id=credit_acc, debit=0, credit=total_value)
                        ]
                    )
                    await post_journal_entry(db, entry)
                    print(f"[Finance Consumer] Posted Journal: {description} (${total_value})")

async def start_finance_consumer():
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    exchange = await channel.declare_exchange("erp_events", type="topic")
    queue = await channel.declare_queue("finance_posting_queue", durable=True)
    
    await queue.bind(exchange, routing_key="inventory.movement.#")
    
    await queue.consume(process_inventory_event)
    print("[Finance Consumer] Started listening...")
    await asyncio.Future() # Run forever
