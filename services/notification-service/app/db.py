import boto3
import os
from typing import Optional, Tuple, List
from datetime import datetime
from app.models import Notification, NotificationUpdate
from botocore.exceptions import ClientError

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

async def create_notification(
    notification_id: str,
    user_id: str,
    product_id: str,
    notification_type: str,
    message: str,
    read: bool = False
) -> Notification:
    """
    Create a new notification in DynamoDB.
    """
    now = datetime.utcnow().isoformat()
    
    item = {
        "PK": f"USER#{user_id}",
        "SK": f"NOTIF#{notification_id}",
        "notification_id": notification_id,
        "user_id": user_id,
        "product_id": product_id,
        "notification_type": notification_type,
        "message": message,
        "read": read,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        table.put_item(Item=item)
        return Notification(
            notification_id=notification_id,
            user_id=user_id,
            product_id=product_id,
            notification_type=notification_type,
            message=message,
            read=read,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

async def get_notification(notification_id: str) -> Optional[Notification]:
    """
    Retrieve a notification by ID.
    Note: In a real scenario, you'd need to query by GSI or scan since PK is needed.
    """
    try:
        # This is a simplified approach; in production, use GSI
        response = table.scan(
            FilterExpression="notification_id = :notif_id",
            ExpressionAttributeValues={":notif_id": notification_id}
        )
        
        if response["Items"]:
            item = response["Items"][0]
            return _item_to_notification(item)
        return None
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

async def get_user_notifications(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    read: Optional[bool] = None
) -> Tuple[List[Notification], int]:
    """
    Retrieve notifications for a user with pagination.
    """
    try:
        query_kwargs = {
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": f"USER#{user_id}"},
            "ScanIndexForward": False  # Most recent first
        }
        
        if read is not None:
            query_kwargs["FilterExpression"] = "#r = :read"
            query_kwargs["ExpressionAttributeNames"] = {"#r": "read"}
            query_kwargs["ExpressionAttributeValues"]["]read"] = read
        
        response = table.query(**query_kwargs)
        
        items = response.get("Items", [])
        total = response.get("Count", 0)
        
        # Apply pagination
        paginated_items = items[skip : skip + limit]
        
        notifications = [_item_to_notification(item) for item in paginated_items]
        return notifications, total
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate
) -> Optional[Notification]:
    """
    Update a notification.
    """
    try:
        # First, get the notification to find its PK and SK
        response = table.scan(
            FilterExpression="notification_id = :notif_id",
            ExpressionAttributeValues={":notif_id": notification_id}
        )
        
        if not response["Items"]:
            return None
        
        item = response["Items"][0]
        pk = item["PK"]
        sk = item["SK"]
        
        update_expression = "SET updated_at = :now"
        expr_attr_values = {":now": datetime.utcnow().isoformat()}
        expr_attr_names = {}
        
        if notification_update.read is not None:
            update_expression += ", #r = :read"
            expr_attr_names["#r"] = "read"
            expr_attr_values[":read"] = notification_update.read
        
        if notification_update.message is not None:
            update_expression += ", message = :msg"
            expr_attr_values[":msg"] = notification_update.message
        
        kwargs = {
            "Key": {"PK": pk, "SK": sk},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expr_attr_values,
            "ReturnValues": "ALL_NEW"
        }
        
        if expr_attr_names:
            kwargs["ExpressionAttributeNames"] = expr_attr_names
        
        response = table.update_item(**kwargs)
        return _item_to_notification(response["Attributes"])
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

async def mark_as_read(notification_id: str) -> Optional[Notification]:
    """
    Mark a notification as read.
    """
    return await update_notification(notification_id, NotificationUpdate(read=True))

async def delete_notification(notification_id: str) -> bool:
    """
    Delete a notification.
    """
    try:
        # First, find the notification
        response = table.scan(
            FilterExpression="notification_id = :notif_id",
            ExpressionAttributeValues={":notif_id": notification_id}
        )
        
        if not response["Items"]:
            return False
        
        item = response["Items"][0]
        table.delete_item(
            Key={"PK": item["PK"], "SK": item["SK"]}
        )
        return True
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

async def get_unread_count(user_id: str) -> int:
    """
    Get count of unread notifications for a user.
    """
    try:
        response = table.query(
            KeyConditionExpression="PK = :pk",
            FilterExpression="#r = :read",
            ExpressionAttributeValues={
                ":pk": f"USER#{user_id}",
                ":read": False
            },
            ExpressionAttributeNames={"#r": "read"},
            Select="COUNT"
        )
        return response.get("Count", 0)
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

def _item_to_notification(item: dict) -> Notification:
    """
    Convert DynamoDB item to Notification model.
    """
    return Notification(
        notification_id=item.get("notification_id"),
        user_id=item.get("user_id"),
        product_id=item.get("product_id"),
        notification_type=item.get("notification_type"),
        message=item.get("message"),
        read=item.get("read", False),
        created_at=datetime.fromisoformat(item.get("created_at")),
        updated_at=datetime.fromisoformat(item.get("updated_at"))
    )
