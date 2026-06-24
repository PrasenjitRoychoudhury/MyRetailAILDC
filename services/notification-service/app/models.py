from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    product_id: str = Field(..., min_length=1, description="Product ID")
    notification_type: str = Field(..., min_length=1, description="Type of notification")
    message: str = Field(..., min_length=1, description="Notification message")
    read: bool = Field(default=False, description="Whether notification is read")

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    read: Optional[bool] = None
    message: Optional[str] = None

class Notification(NotificationBase):
    notification_id: str = Field(..., description="Unique notification ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class NotificationList(BaseModel):
    notifications: list[Notification] = Field(default_factory=list)
    count: int = Field(default=0)
    total: int = Field(default=0)

class ProductNotification(BaseModel):
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    event_type: str = Field(..., description="Event type (stock, price, rating)")
    previous_value: Optional[str] = None
    current_value: str = Field(..., description="Current value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
