from sqlalchemy.ext.asyncio import AsyncSession
import models
import uuid
from datetime import datetime
from connections.rabbitmq_utils import get_rabbitmq_connection
import json
import aio_pika

async def record_movement(
    db: AsyncSession,
    product_id: uuid.UUID,
    location_id: uuid.UUID,
    quantity_change: float,
    movement_type: models.MovementType,
    batch_id: uuid.UUID = None,
    reference_id: str = None,
    project_id: str = None,
    notes: str = None
):
    movement = models.StockMovement(
        product_id=product_id,
        location_id=location_id,
        batch_id=batch_id,
        quantity_change=quantity_change,
        movement_type=movement_type,
        reference_id=reference_id,
        project_id=project_id,
        notes=notes
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    
    # Broadcast Event
    try:
        connection = await get_rabbitmq_connection()
        channel = await connection.channel()
        exchange = await channel.declare_exchange("erp_events", type="topic")
        
        message = {
            "event": "inventory.movement",
            "data": {
                "product_id": str(product_id),
                "location_id": str(location_id),
                "quantity": quantity_change,
                "type": movement_type.value, # Use .value for Enum
                "ref_id": reference_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=f"inventory.movement.{movement_type.value.lower()}" # Use .value for Enum
        )
    except Exception as e:
        print(f"Failed to publish inventory event: {e}")

    return movement
