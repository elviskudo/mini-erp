import asyncio
import aio_pika
import json
from connections.rabbitmq_utils import get_rabbitmq_connection
from connections.mongodb import get_mongo_db
from datetime import datetime

async def process_lab_data(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        print(f"Received Lab Data: {data}")
        
        # Save to MongoDB
        db = await get_mongo_db()
        if db is not None:
            data["processed_at"] = datetime.utcnow()
            await db["raw_lab_data"].insert_one(data)
            print("Saved to MongoDB")
            
            # FUTURE: Broadcast to Redis for Realtime (Socket.IO)
            # We need a redis client here to publish to 'global_notifications'
            # For now, we will print.

async def consume_lab_data():
    try:
        connection = await get_rabbitmq_connection()
        channel = await connection.channel()
        queue = await channel.declare_queue("lab_data_ingress", durable=True)
        
        await queue.consume(process_lab_data)
        print("Waiting for messages in lab_data_ingress...")
        await asyncio.Future() # Run forever
    except Exception as e:
        print(f"Worker Error: {e}")
