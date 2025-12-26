"""
Notification Service - Publishes notifications to RabbitMQ for realtime server distribution
"""
import json
from datetime import datetime
from connections.rabbitmq_utils import publish_message

NOTIFICATIONS_QUEUE = "notifications"

async def send_notification(
    title: str,
    message: str,
    tenant_id: str = None,
    user_id: str = None,
    notification_type: str = "info",
    data: dict = None
):
    """
    Send notification to realtime server via RabbitMQ
    
    Args:
        title: Notification title
        message: Notification message body
        tenant_id: Target tenant (optional - if set, only users in this tenant receive it)
        user_id: Target user (optional - if set, only this user receives it)
        notification_type: Type of notification (info, success, warning, error)
        data: Additional data payload
    """
    payload = {
        "title": title,
        "message": message,
        "type": notification_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {}
    }
    
    if tenant_id:
        payload["tenant_id"] = str(tenant_id)
    if user_id:
        payload["user_id"] = str(user_id)
    
    try:
        await publish_message(NOTIFICATIONS_QUEUE, payload)
        print(f"Notification sent: {title}")
    except Exception as e:
        print(f"Failed to send notification: {e}")


async def notify_goods_receipt(
    tenant_id: str,
    po_number: str,
    batches_created: int,
    progress: float,
    status: str,
    received_by: str = None
):
    """Send notification for goods receipt completion"""
    await send_notification(
        title="📦 Goods Receipt Completed",
        message=f"PO {po_number}: {batches_created} batch(es) received. Progress: {progress:.1f}%",
        tenant_id=tenant_id,
        notification_type="success",
        data={
            "po_number": po_number,
            "progress": progress,
            "status": status,
            "batches_created": batches_created
        }
    )


async def notify_po_status_change(
    tenant_id: str,
    po_number: str,
    old_status: str,
    new_status: str
):
    """Send notification for PO status change"""
    await send_notification(
        title="🔄 PO Status Updated",
        message=f"PO {po_number}: Status changed from {old_status} to {new_status}",
        tenant_id=tenant_id,
        notification_type="info",
        data={
            "po_number": po_number,
            "old_status": old_status,
            "new_status": new_status
        }
    )


async def notify_pr_approved(
    tenant_id: str,
    pr_number: str,
    requester_id: str = None
):
    """Send notification when PR is approved"""
    notification_params = {
        "title": "✅ PR Approved",
        "message": f"Purchase Request {pr_number} has been approved",
        "tenant_id": tenant_id,
        "notification_type": "success",
        "data": {"pr_number": pr_number}
    }
    
    # Notify requester directly if available
    if requester_id:
        notification_params["user_id"] = requester_id
    
    await send_notification(**notification_params)


async def notify_pr_rejected(
    tenant_id: str,
    pr_number: str,
    reason: str = None,
    requester_id: str = None
):
    """Send notification when PR is rejected"""
    message = f"Purchase Request {pr_number} has been rejected"
    if reason:
        message += f": {reason}"
    
    notification_params = {
        "title": "❌ PR Rejected",
        "message": message,
        "tenant_id": tenant_id,
        "notification_type": "error",
        "data": {"pr_number": pr_number, "reason": reason}
    }
    
    if requester_id:
        notification_params["user_id"] = requester_id
    
    await send_notification(**notification_params)
