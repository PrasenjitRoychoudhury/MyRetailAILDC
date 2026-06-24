import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

_executor = ThreadPoolExecutor(max_workers=10)
_dynamodb = None

def get_dynamodb_resource():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
    return _dynamodb

def get_table():
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(TABLE_NAME)

async def create_notification(notification_data: dict) -> bool:
    """
    Create a new notification in DynamoDB.
    PK: USER#{user_id}, SK: NOTIF#{notification_id}
    """
    table = get_table()
    pk = f"USER#{notification_data['user_id']}"
    sk = notification_data['notification_id']
    
    item = {
        "PK": pk,
        "SK": sk,
        "user_id": notification_data['user_id'],
        "product_id": notification_data['product_id'],
        "event_type": notification_data['event_type'],
        "message": notification_data['message'],
        "metadata": notification_data.get('metadata', {}),
        "created_at": notification_data['created_at'],
        "read": notification_data['read']
    }
    
    def _put_item():
        table.put_item(Item=item)
        return True
    
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _put_item)
    except Exception as e:
        print(f"Error creating notification: {e}")
        return False

async def get_notification(notification_id: str) -> Optional[dict]:
    """
    Retrieve a notification by ID.
    Scans for SK matching the notification_id.
    """
    table = get_table()
    
    def _scan():
        response = table.scan(
            FilterExpression=Attr('SK').eq(notification_id)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    try:
        loop = asyncio.get_event_loop()
        item = await loop.run_in_executor(_executor, _scan)
        if item:
            return {
                "notification_id": item['SK'],
                "user_id": item['user_id'],
                "product_id": item['product_id'],
                "event_type": item['event_type'],
                "message": item['message'],
                "metadata": item.get('metadata', {}),
                "created_at": item['created_at'],
                "read": item['read']
            }
        return None
    except Exception as e:
        print(f"Error getting notification: {e}")
        return None

async def list_user_notifications(
    user_id: str,
    limit: int = 10,
    unread_only: bool = False
) -> list[dict]:
    """
    List notifications for a user.
    PK: USER#{user_id}, SK begins with NOTIF#
    """
    table = get_table()
    pk = f"USER#{user_id}"
    
    def _query():
        filter_expr = Attr('SK').begins_with('NOTIF#')
        if unread_only:
            filter_expr = filter_expr & Attr('read').eq(False)
        
        response = table.query(
            KeyConditionExpression=Key('PK').eq(pk),
            FilterExpression=filter_expr,
            Limit=limit,
            ScanIndexForward=False
        )
        items = response.get('Items', [])
        return items
    
    try:
        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(_executor, _query)
        notifications = []
        for item in items:
            notifications.append({
                "notification_id": item['SK'],
                "user_id": item['user_id'],
                "product_id": item['product_id'],
                "event_type": item['event_type'],
                "message": item['message'],
                "metadata": item.get('metadata', {}),
                "created_at": item['created_at'],
                "read": item['read']
            })
        return notifications
    except Exception as e:
        print(f"Error listing notifications: {e}")
        return []

async def update_notification(notification_id: str, updates: dict) -> bool:
    """
    Update a notification's attributes.
    """
    table = get_table()
    
    def _scan_and_update():
        response = table.scan(
            FilterExpression=Attr('SK').eq(notification_id)
        )
        items = response.get('Items', [])
        if not items:
            return False
        
        item = items[0]
        pk = item['PK']
        sk = item['SK']
        
        update_expr = "SET " + ", ".join([f"{k}=:{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return True
    
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _scan_and_update)
    except Exception as e:
        print(f"Error updating notification: {e}")
        return False

async def delete_notification(notification_id: str) -> bool:
    """
    Delete a notification by ID.
    """
    table = get_table()
    
    def _scan_and_delete():
        response = table.scan(
            FilterExpression=Attr('SK').eq(notification_id)
        )
        items = response.get('Items', [])
        if not items:
            return False
        
        item = items[0]
        pk = item['PK']
        sk = item['SK']
        
        table.delete_item(Key={"PK": pk, "SK": sk})
        return True
    
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _scan_and_delete)
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False
