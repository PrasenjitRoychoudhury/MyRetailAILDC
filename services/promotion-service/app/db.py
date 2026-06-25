import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


async def create_promotion(item: dict) -> dict:
    """
    Create a new promotion in DynamoDB.
    """
    try:
        table.put_item(Item=item)
        return {"success": True, "item": item}
    except ClientError as e:
        return {"success": False, "error": str(e)}


async def get_promotion_by_id(promo_id: str) -> dict:
    """
    Get promotion by promo_id (PK).
    """
    try:
        response = table.get_item(
            Key={"pk": promo_id, "sk": "METADATA"}
        )
        return response.get("Item")
    except ClientError as e:
        return None


async def get_promotion_by_code(promo_code: str) -> dict:
    """
    Query promotion by promo_code using scan (or GSI if available).
    """
    try:
        response = table.scan(
            FilterExpression="promo_code = :code",
            ExpressionAttributeValues={":code": promo_code}
        )
        items = response.get("Items", [])
        if items:
            return items[0]
        return None
    except ClientError as e:
        return None


async def list_active_promotions() -> list:
    """
    List all active promotions (scan for items with pk starting with PROMOTION#).
    """
    try:
        response = table.scan(
            FilterExpression="begins_with(pk, :prefix)",
            ExpressionAttributeValues={":prefix": "PROMOTION#"}
        )
        return response.get("Items", [])
    except ClientError as e:
        return []


async def record_promo_usage(user_id: str, promo_id: str, order_id: str) -> dict:
    """
    Record usage of a promotion by a user.
    """
    item = {
        "pk": f"PROMO_USAGE#{user_id}#{promo_id}",
        "sk": "METADATA",
        "user_id": user_id,
        "promo_id": promo_id,
        "order_id": order_id,
        "used_at": datetime.utcnow().isoformat()
    }
    try:
        table.put_item(Item=item)
        return {"success": True}
    except ClientError as e:
        return {"success": False, "error": str(e)}


async def get_user_promo_usage(user_id: str, promo_id: str) -> dict:
    """
    Check if user has already used a promotion.
    """
    try:
        response = table.get_item(
            Key={"pk": f"PROMO_USAGE#{user_id}#{promo_id}", "sk": "METADATA"}
        )
        return response.get("Item")
    except ClientError as e:
        return None


async def increment_usage_count(promo_id: str) -> dict:
    """
    Increment the usage count of a promotion.
    """
    try:
        response = table.update_item(
            Key={"pk": promo_id, "sk": "METADATA"},
            UpdateExpression="SET usage_count = if_not_exists(usage_count, :zero) + :inc",
            ExpressionAttributeValues={
                ":zero": 0,
                ":inc": 1
            },
            ReturnValues="ALL_NEW"
        )
        return {"success": True, "item": response.get("Attributes")}
    except ClientError as e:
        return {"success": False, "error": str(e)}
