import aio_pika
import os
import json
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")
RABBITMQ_HOST = "rabbitmq_broker" # Docker service name
RABBITMQ_PORT = 5672

async def get_rabbitmq_connection():
    return await aio_pika.connect_robust(
        f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
    )

async def publish_message(queue_name: str, message: dict):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        # Declare queue
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=queue_name
        )
