"""
Kafka Utils - Replaces RabbitMQ for message publishing
Uses aiokafka for async Kafka operations
"""
import os
import json
import asyncio
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
KAFKA_TOPIC_PREFIX = os.getenv("KAFKA_TOPIC_PREFIX", "mini-erp")

# Global producer instance (connection pooling)
_producer: Optional[AIOKafkaProducer] = None
_producer_lock = asyncio.Lock()


async def get_kafka_producer() -> AIOKafkaProducer:
    """Get or create a Kafka producer with connection pooling."""
    global _producer
    
    if _producer is None:
        async with _producer_lock:
            if _producer is None:
                _producer = AIOKafkaProducer(
                    bootstrap_servers=KAFKA_BROKERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas
                    enable_idempotence=True,  # Exactly-once semantics
                    max_batch_size=16384,
                    linger_ms=10,  # Small batch delay for better throughput
                )
                await _producer.start()
                logger.info(f"Kafka producer connected to {KAFKA_BROKERS}")
    
    return _producer


async def close_kafka_producer():
    """Close the Kafka producer gracefully."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer closed")


async def publish_message(topic: str, message: Dict[str, Any], key: Optional[str] = None):
    """
    Publish a message to a Kafka topic.
    
    Args:
        topic: Kafka topic name (will be prefixed with KAFKA_TOPIC_PREFIX)
        message: Message payload as dictionary
        key: Optional message key for partitioning
    """
    try:
        producer = await get_kafka_producer()
        full_topic = f"{KAFKA_TOPIC_PREFIX}.{topic}"
        
        # Add metadata to message
        message['_timestamp'] = asyncio.get_event_loop().time()
        message['_topic'] = full_topic
        
        await producer.send_and_wait(
            topic=full_topic,
            value=message,
            key=key
        )
        
        logger.debug(f"Message published to {full_topic}: {message.get('type', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Failed to publish message to {topic}: {e}")
        raise


async def publish_notification(
    title: str,
    message: str,
    tenant_id: str = None,
    user_id: str = None,
    notification_type: str = "info",
    data: dict = None
):
    """
    Publish a notification event to Kafka.
    Replaces the RabbitMQ notification publishing.
    
    Args:
        title: Notification title
        message: Notification message
        tenant_id: Optional tenant ID for tenant-specific notifications
        user_id: Optional user ID for user-specific notifications
        notification_type: Type of notification (info, warning, error, success)
        data: Additional data payload
    """
    payload = {
        "type": "notification",
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "data": data or {}
    }
    
    # Use tenant_id or user_id as key for proper partitioning
    key = tenant_id or user_id or "global"
    
    await publish_message("notifications", payload, key=key)


async def publish_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    tenant_id: str = None,
    user_id: str = None
):
    """
    Publish a generic event to Kafka.
    
    Args:
        event_type: Type of event (e.g., 'user.created', 'order.completed')
        source: Source service/module
        data: Event data
        tenant_id: Optional tenant ID
        user_id: Optional user ID
    """
    payload = {
        "type": event_type,
        "source": source,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "data": data
    }
    
    # Derive topic from event type (e.g., 'user.created' -> 'user')
    topic = event_type.split('.')[0] if '.' in event_type else event_type
    key = tenant_id or user_id
    
    await publish_message(topic, payload, key=key)


# Backward compatibility functions (same signature as rabbitmq_utils)
async def legacy_publish_message(queue_name: str, message: dict):
    """
    Legacy compatibility function for existing code using RabbitMQ.
    Maps queue_name to Kafka topic.
    """
    # Map queue names to topics
    topic_mapping = {
        "notifications": "notifications",
        "lab_data": "lab",
        "finance": "finance",
    }
    
    topic = topic_mapping.get(queue_name, queue_name)
    await publish_message(topic, message)


# Alias for backward compatibility
get_rabbitmq_connection = None  # Explicitly remove RabbitMQ
