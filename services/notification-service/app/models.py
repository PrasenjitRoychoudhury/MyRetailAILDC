from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    user_id: str = Field(..., description="User ID")
    product_id: str = Field(..., description="Product ID")
    event_type: str = Field(..., description="Event type: added_to_cart, purchase, stock_alert")
    message: str = Field(..., description="Notification message")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    notification_id: str = Field(..., description="Notification ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    read: bool = Field(default=False, description="Read status")

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    read: bool = Field(..., description="Read status")

class NotificationList(BaseModel):
    notifications: list[Notification] = Field(default_factory=list)
    count: int = Field(default=0)

class HealthResponse(BaseModel):
    status: str
    service: str
