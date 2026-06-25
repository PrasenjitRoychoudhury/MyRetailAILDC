import os
import boto3
from datetime import datetime
from typing import Optional, Dict, List, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

async def create_promotion(
    promo_id: str,
    promo_code: str,
    name: str,
    promo_type: str,
    value: float,
    start_date: str,
    end_date: str,
    usage_limit: int,
    min_cart_value: float,
    applicable_categories: List[str],
    created_at: str,
) -> bool:
    """
    Create a new promotion in DynamoDB.
    Returns True if successful, False if code already exists.
    """
    try:
        existing = await get_promotion_by_code(promo_code)
        if existing:
            return False
        
        table.put_item(
            Item={
                "PK": promo_id,
                "SK": f"METADATA#{promo_code}",
                "promoId": promo_id,
                "promoCode": promo_code,
                "name": name,
                "promoType": promo_type,
                "value": value,
                "startDate": start_date,
                "endDate": end_date,
                "usageLimit": usage_limit,
                "usageCount": 0,
                "minCartValue": min_cart_value,
                "applicableCategories": applicable_categories,
                "createdAt": created_at,
            }
        )
        return True
    except Exception as e:
        print(f"Error creating promotion: {e}")
        return False

async def get_promotion_by_id(promo_id: str) -> Optional[Dict[str, Any]]:
    """
    Get promotion by ID.
    """
    try:
        response = table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": promo_id,
            },
            Limit=1,
        )
        if response["Items"]:
            return response["Items"][0]
        return None
    except Exception as e:
        print(f"Error fetching promotion: {e}")
        return None

async def get_promotion_by_code(promo_code: str) -> Optional[Dict[str, Any]]:
    """
    Get promotion by promo code using GSI or scan.
    """
    try:
        response = table.scan(
            FilterExpression="promoCode = :code",
            ExpressionAttributeValues={
                ":code": promo_code,
            },
            Limit=1,
        )
        if response["Items"]:
            return response["Items"][0]
        return None
    except Exception as e:
        print(f"Error fetching promotion by code: {e}")
        return None

async def list_active_promotions() -> List[Dict[str, Any]]:
    """
    List all active promotions.
    """
    try:
        now = datetime.utcnow().isoformat()
        response = table.scan(
            FilterExpression="begins_with(PK, :prefix) AND startDate <= :now AND endDate > :now",
            ExpressionAttributeValues={
                ":prefix": "PROMOTION#",
                ":now": now,
            },
        )
        return response.get("Items", [])
    except Exception as e:
        print(f"Error listing active promotions: {e}")
        return []

async def record_promo_usage(
    user_id: str,
    promo_id: str,
    order_id: str,
    used_at: str,
) -> bool:
    """
    Record promo usage for a user.
    """
    try:
        table.put_item(
            Item={
                "PK": f"PROMO_USAGE#{user_id}",
                "SK": f"PROMO#{promo_id}",
                "promoId": promo_id,
                "userId": user_id,
                "orderId": order_id,
                "usedAt": used_at,
            }
        )
        return True
    except Exception as e:
        print(f"Error recording promo usage: {e}")
        return False

async def get_user_promo_usage(
    user_id: str,
    promo_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Get user's usage of a specific promo.
    """
    try:
        response = table.get_item(
            Key={
                "PK": f"PROMO_USAGE#{user_id}",
                "SK": f"PROMO#{promo_id}",
            }
        )
        return response.get("Item")
    except Exception as e:
        print(f"Error fetching user promo usage: {e}")
        return None

async def increment_usage_count(promo_id: str) -> bool:
    """
    Increment usage count for a promotion.
    """
    try:
        promotion = await get_promotion_by_id(promo_id)
        if not promotion:
            return False
        
        table.update_item(
            Key={
                "PK": promo_id,
                "SK": promotion["SK"],
            },
            UpdateExpression="SET usageCount = usageCount + :inc",
            ExpressionAttributeValues={
                ":inc": 1,
            },
        )
        return True
    except Exception as e:
        print(f"Error incrementing usage count: {e}")
        return False
