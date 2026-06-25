import boto3
import os
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

table_name = os.getenv("TABLE_NAME", "retail-platform")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)

def create_promotion(promotion_data: Dict[str, Any]) -> str:
    promo_id = str(uuid.uuid4())
    pk = f"PROMOTION#{promo_id}"
    sk = "METADATA"
    
    item = {
        "pk": pk,
        "sk": sk,
        "promo_id": promo_id,
        "name": promotion_data["name"],
        "promo_code": promotion_data["promo_code"],
        "promotion_type": promotion_data["promotion_type"],
        "value": promotion_data["value"],
        "start_date": promotion_data["start_date"],
        "end_date": promotion_data["end_date"],
        "usage_limit": promotion_data.get("usage_limit"),
        "usage_count": 0,
        "min_cart_value": promotion_data.get("min_cart_value"),
        "applicable_categories": promotion_data.get("applicable_categories"),
        "created_at": datetime.utcnow().isoformat(),
    }
    
    table.put_item(Item=item)
    return promo_id

def get_promotion_by_id(promo_id: str) -> Optional[Dict[str, Any]]:
    response = table.get_item(
        Key={
            "pk": f"PROMOTION#{promo_id}",
            "sk": "METADATA"
        }
    )
    return response.get("Item")

def get_promotion_by_code(promo_code: str) -> Optional[Dict[str, Any]]:
    response = table.scan(
        FilterExpression="promo_code = :code AND begins_with(pk, :pk_prefix)",
        ExpressionAttributeValues={
            ":code": promo_code,
            ":pk_prefix": "PROMOTION#"
        }
    )
    
    items = response.get("Items", [])
    return items[0] if items else None

def list_active_promotions() -> list:
    now = datetime.utcnow().isoformat()
    response = table.scan(
        FilterExpression="begins_with(pk, :pk_prefix) AND start_date <= :now AND end_date >= :now",
        ExpressionAttributeValues={
            ":pk_prefix": "PROMOTION#",
            ":now": now
        }
    )
    
    return response.get("Items", [])

def record_promo_usage(user_id: str, promo_id: str, order_id: str) -> bool:
    pk = f"PROMO_USAGE#{user_id}#{promo_id}"
    sk = datetime.utcnow().isoformat()
    
    item = {
        "pk": pk,
        "sk": sk,
        "user_id": user_id,
        "promo_id": promo_id,
        "order_id": order_id,
        "used_at": sk
    }
    
    table.put_item(Item=item)
    return True

def get_user_promo_usage_count(user_id: str, promo_id: str) -> int:
    response = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={
            ":pk": f"PROMO_USAGE#{user_id}#{promo_id}"
        }
    )
    return response.get("Count", 0)

def increment_promotion_usage_count(promo_id: str) -> bool:
    pk = f"PROMOTION#{promo_id}"
    sk = "METADATA"
    
    table.update_item(
        Key={"pk": pk, "sk": sk},
        UpdateExpression="SET usage_count = if_not_exists(usage_count, :zero) + :one",
        ExpressionAttributeValues={
            ":zero": 0,
            ":one": 1
        }
    )
    return True
