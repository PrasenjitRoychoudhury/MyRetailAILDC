from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationList,
    ProductNotification
)
from app.db import (
    create_notification,
    get_notification,
    get_user_notifications,
    update_notification,
    delete_notification,
    mark_as_read,
    get_unread_count
)
from datetime import datetime
import uuid

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

@router.post("/", response_model=Notification, status_code=201)
async def create_notification_endpoint(notification: NotificationCreate):
    """
    Create a new notification for a user.
    """
    notification_id = f"NOTIF#{uuid.uuid4()}"
    try:
        result = await create_notification(
            notification_id=notification_id,
            user_id=notification.user_id,
            product_id=notification.product_id,
            notification_type=notification.notification_type,
            message=notification.message,
            read=notification.read
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")

@router.get("/{notification_id}", response_model=Notification)
async def get_notification_endpoint(notification_id: str):
    """
    Retrieve a specific notification by ID.
    """
    try:
        notification = await get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notification: {str(e)}")

@router.get("/user/{user_id}", response_model=NotificationList)
async def get_user_notifications_endpoint(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    read: Optional[bool] = None
):
    """
    Retrieve all notifications for a user with pagination.
    """
    try:
        notifications, total = await get_user_notifications(user_id, skip, limit, read)
        return NotificationList(
            notifications=notifications,
            count=len(notifications),
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notifications: {str(e)}")

@router.patch("/{notification_id}", response_model=Notification)
async def update_notification_endpoint(
    notification_id: str,
    notification_update: NotificationUpdate
):
    """
    Update a notification (mark as read, update message).
    """
    try:
        notification = await update_notification(notification_id, notification_update)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notification: {str(e)}")

@router.put("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read_endpoint(notification_id: str):
    """
    Mark a notification as read.
    """
    try:
        notification = await mark_as_read(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")

@router.delete("/{notification_id}", status_code=204)
async def delete_notification_endpoint(notification_id: str):
    """
    Delete a notification.
    """
    try:
        success = await delete_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {str(e)}")

@router.get("/user/{user_id}/unread-count", response_model=dict)
async def get_unread_count_endpoint(user_id: str):
    """
    Get count of unread notifications for a user.
    """
    try:
        count = await get_unread_count(user_id)
        return {"user_id": user_id, "unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")

@router.post("/product-event", response_model=dict, status_code=201)
async def handle_product_event(event: ProductNotification):
    """
    Handle product events and create appropriate notifications.
    Triggered when product details change (stock, price, rating).
    """
    try:
        notification_message = f"Product '{event.product_name}' {event.event_type} changed: {event.current_value}"
        notification_id = f"NOTIF#{uuid.uuid4()}"
        
        # In a real scenario, this would query users interested in this product
        # For now, just acknowledge the event
        return {
            "status": "processed",
            "event_type": event.event_type,
            "product_id": event.product_id,
            "message": notification_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process product event: {str(e)}")
