from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import uuid
from app.models import (
    NotificationCreate,
    Notification,
    NotificationUpdate,
    NotificationList
)
from app.db import (
    create_notification,
    get_notification,
    list_user_notifications,
    update_notification,
    delete_notification
)

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

@router.post("", response_model=Notification, status_code=201)
async def send_notification(notification: NotificationCreate):
    """
    Create and send a new notification.
    """
    notification_id = f"NOTIF#{str(uuid.uuid4())}"
    created_at = datetime.utcnow().isoformat()
    
    notification_data = {
        "notification_id": notification_id,
        "user_id": notification.user_id,
        "product_id": notification.product_id,
        "event_type": notification.event_type,
        "message": notification.message,
        "metadata": notification.metadata or {},
        "created_at": created_at,
        "read": False
    }
    
    result = await create_notification(notification_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create notification")
    
    return Notification(**notification_data)

@router.get("/{notification_id}", response_model=Notification)
async def get_notification_detail(notification_id: str):
    """
    Retrieve a specific notification by ID.
    """
    notification = await get_notification(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return Notification(**notification)

@router.get("/user/{user_id}", response_model=NotificationList)
async def list_notifications(
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    unread_only: bool = Query(False)
):
    """
    List notifications for a user.
    Optionally filter by unread status.
    """
    notifications = await list_user_notifications(user_id, limit=limit, unread_only=unread_only)
    return NotificationList(notifications=notifications, count=len(notifications))

@router.patch("/{notification_id}", response_model=Notification)
async def mark_notification(
    notification_id: str,
    update: NotificationUpdate
):
    """
    Update notification read status.
    """
    updated = await update_notification(notification_id, {"read": update.read})
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification = await get_notification(notification_id)
    return Notification(**notification)

@router.delete("/{notification_id}", status_code=204)
async def remove_notification(notification_id: str):
    """
    Delete a notification.
    """
    result = await delete_notification(notification_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return None
