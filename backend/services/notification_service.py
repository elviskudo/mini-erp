"""
Notification Service - Updated to use Kafka instead of RabbitMQ
"""
from connections.kafka_utils import publish_notification, publish_event
import logging

logger = logging.getLogger(__name__)


async def send_notification(
    title: str,
    message: str,
    tenant_id: str = None,
    user_id: str = None,
    notification_type: str = "info",
    data: dict = None
):
    """
    Send a notification via Kafka.
    
    Args:
        title: Notification title
        message: Notification message
        tenant_id: Target tenant ID (for tenant-wide notifications)
        user_id: Target user ID (for user-specific notifications)
        notification_type: Type of notification (info, warning, error, success)
        data: Additional data payload
    """
    try:
        await publish_notification(
            title=title,
            message=message,
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=notification_type,
            data=data
        )
        logger.info(f"Notification sent: {title}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        # Don't raise - notifications should not break main flow


async def notify_goods_receipt(
    tenant_id: str,
    po_number: str,
    vendor_name: str,
    items_count: int,
    received_by: str = None
):
    """Notification for goods receipt."""
    await send_notification(
        title="Goods Receipt",
        message=f"PO {po_number} from {vendor_name} received ({items_count} items)",
        tenant_id=tenant_id,
        notification_type="success",
        data={
            "type": "goods_receipt",
            "po_number": po_number,
            "vendor_name": vendor_name,
            "items_count": items_count,
            "received_by": received_by
        }
    )
    
    # Also publish as event for other services
    await publish_event(
        event_type="inventory.goods_received",
        source="procurement",
        data={
            "po_number": po_number,
            "vendor_name": vendor_name,
            "items_count": items_count
        },
        tenant_id=tenant_id
    )


async def notify_po_status_change(
    tenant_id: str,
    po_number: str,
    old_status: str,
    new_status: str,
    changed_by: str = None
):
    """Notification for PO status change."""
    await send_notification(
        title="PO Status Updated",
        message=f"PO {po_number} status changed from {old_status} to {new_status}",
        tenant_id=tenant_id,
        notification_type="info",
        data={
            "type": "po_status_change",
            "po_number": po_number,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by
        }
    )
    
    await publish_event(
        event_type="procurement.po_status_changed",
        source="procurement",
        data={
            "po_number": po_number,
            "old_status": old_status,
            "new_status": new_status
        },
        tenant_id=tenant_id
    )


async def notify_pr_approved(
    tenant_id: str,
    pr_number: str,
    approved_by: str,
    requested_by: str = None
):
    """Notification for PR approval."""
    await send_notification(
        title="PR Approved",
        message=f"Purchase Request {pr_number} has been approved by {approved_by}",
        tenant_id=tenant_id,
        user_id=requested_by,  # Notify the requester
        notification_type="success",
        data={
            "type": "pr_approved",
            "pr_number": pr_number,
            "approved_by": approved_by
        }
    )
    
    await publish_event(
        event_type="procurement.pr_approved",
        source="procurement",
        data={
            "pr_number": pr_number,
            "approved_by": approved_by
        },
        tenant_id=tenant_id
    )


async def notify_pr_rejected(
    tenant_id: str,
    pr_number: str,
    rejected_by: str,
    reason: str = None,
    requested_by: str = None
):
    """Notification for PR rejection."""
    await send_notification(
        title="PR Rejected",
        message=f"Purchase Request {pr_number} has been rejected by {rejected_by}",
        tenant_id=tenant_id,
        user_id=requested_by,
        notification_type="warning",
        data={
            "type": "pr_rejected",
            "pr_number": pr_number,
            "rejected_by": rejected_by,
            "reason": reason
        }
    )
    
    await publish_event(
        event_type="procurement.pr_rejected",
        source="procurement",
        data={
            "pr_number": pr_number,
            "rejected_by": rejected_by,
            "reason": reason
        },
        tenant_id=tenant_id
    )


async def notify_stock_low(
    tenant_id: str,
    product_name: str,
    product_code: str,
    current_stock: int,
    min_stock: int,
    warehouse: str = None
):
    """Notification for low stock alert."""
    await send_notification(
        title="Low Stock Alert",
        message=f"{product_name} ({product_code}) is below minimum stock ({current_stock}/{min_stock})",
        tenant_id=tenant_id,
        notification_type="warning",
        data={
            "type": "low_stock",
            "product_name": product_name,
            "product_code": product_code,
            "current_stock": current_stock,
            "min_stock": min_stock,
            "warehouse": warehouse
        }
    )
    
    await publish_event(
        event_type="inventory.stock_low",
        source="inventory",
        data={
            "product_code": product_code,
            "current_stock": current_stock,
            "min_stock": min_stock,
            "warehouse": warehouse
        },
        tenant_id=tenant_id
    )


async def notify_payment_received(
    tenant_id: str,
    invoice_number: str,
    amount: float,
    customer_name: str,
    payment_method: str = None
):
    """Notification for payment received."""
    await send_notification(
        title="Payment Received",
        message=f"Payment of {amount:,.2f} received for Invoice {invoice_number} from {customer_name}",
        tenant_id=tenant_id,
        notification_type="success",
        data={
            "type": "payment_received",
            "invoice_number": invoice_number,
            "amount": amount,
            "customer_name": customer_name,
            "payment_method": payment_method
        }
    )
    
    await publish_event(
        event_type="finance.payment_received",
        source="finance",
        data={
            "invoice_number": invoice_number,
            "amount": amount,
            "customer_name": customer_name
        },
        tenant_id=tenant_id
    )
