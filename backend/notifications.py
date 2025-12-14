from connections.rabbitmq_utils import publish_message
import datetime

async def send_notification(user_id: str, title: str, message: str, type: str = "info"):
    """
    Publish a notification event to RabbitMQ.
    Consumed by the Realtime Server (Node.js) -> Socket.IO -> Frontend.
    """
    payload = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": type,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    # We publish to 'notifications' queue (or exchange in a real system)
    await publish_message("notifications", payload)
