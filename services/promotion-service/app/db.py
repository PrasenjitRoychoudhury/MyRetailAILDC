import os
import boto3
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def generate_promo_id() -> str:
    return str(uuid.uuid4())


def create_promotion(data: Dict[str, Any]) -> Dict[str, Any]:
    promo_id = generate_promo_id()
    pk = f"PROMOTION#{promo_id}"
    sk = "METADATA"
    
    item = {
        "PK": pk,
        "SK": sk,
        "promo_id": promo_id,
        "name": data["name"],
        "promo_type": data["promo_type"],
        "value": data["value"],
        "start_date": data["start_date"].isoformat(),
        "end_date": data["end_date"].isoformat(),
        "usage_limit": data.get("usage_limit"),
        "usage_count": 0,
        "min_cart_value": data.get("min_cart_value", 0),
        "applicable_categories": data.get("applicable_categories", []),
        "created_at": datetime.utcnow().isoformat(),
    }
    
    table.put_item(Item=item)
    return item


def get_promotion(promo_id: str) -> Optional[Dict[str, Any]]:
    pk = f"PROMOTION#{promo_id}"
    sk = "METADATA"
    
    response = table.get_item(Key={"PK": pk, "SK": sk})
    return response.get("Item")


def get_promotion_by_code(promo_code: str) -> Optional[Dict[str, Any]]:
    response = table.query(
        IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :code",
        ExpressionAttributeValues={":code": f"PROMO_CODE#{promo_code}"},
        Limit=1
    )
    if response["Items"]:
        promo_id = response["Items"][0]["promo_id"]
        return get_promotion(promo_id)
    return None


def list_active_promotions() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    
    response = table.query(
        KeyConditionExpression="begins_with(PK, :pk)",
        FilterExpression="start_date <= :now AND end_date >= :now",
        ExpressionAttributeValues={
            ":pk": "PROMOTION#",
            ":now": now
        }
    )
    return response.get("Items", [])


def record_promo_usage(user_id: str, promo_id: str, order_id: str) -> None:
    pk = f"PROMO_USAGE#{user_id}#{promo_id}"
    sk = order_id
    
    item = {
        "PK": pk,
        "SK": sk,
        "user_id": user_id,
        "promo_id": promo_id,
        "order_id": order_id,
        "used_at": datetime.utcnow().isoformat(),
    }
    
    table.put_item(Item=item)


def get_user_promo_usage(user_id: str, promo_id: str) -> List[Dict[str, Any]]:
    pk = f"PROMO_USAGE#{user_id}#{promo_id}"
    
    response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": pk}
    )
    return response.get("Items", [])


def increment_promotion_usage(promo_id: str) -> None:
    pk = f"PROMOTION#{promo_id}"
    sk = "METADATA"
    
    table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression="SET usage_count = if_not_exists(usage_count, :zero) + :one",
        ExpressionAttributeValues={
            ":zero": 0,
            ":one": 1
        }
    )
