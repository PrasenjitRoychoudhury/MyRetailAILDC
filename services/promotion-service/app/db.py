import boto3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

async def create_promotion(promo_id: str, data: Dict[str, Any]) -> bool:
    try:
        table.put_item(
            Item={
                "PK": f"PROMOTION#{promo_id}",
                "SK": f"PROMOTION#{promo_id}",
                **data
            }
        )
        return True
    except Exception as e:
        print(f"Error creating promotion: {e}")
        return False

async def get_promotion(promo_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = table.get_item(
            Key={
                "PK": f"PROMOTION#{promo_id}",
                "SK": f"PROMOTION#{promo_id}"
            }
        )
        item = response.get("Item")
        if item:
            return {
                "promo_id": item.get("promo_id"),
                "name": item.get("name"),
                "type": item.get("type"),
                "value": item.get("value"),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
                "usage_limit": item.get("usage_limit"),
                "usage_count": item.get("usage_count", 0),
                "min_cart_value": item.get("min_cart_value", 0),
                "applicable_categories": item.get("applicable_categories", []),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at")
            }
        return None
    except Exception as e:
        print(f"Error getting promotion: {e}")
        return None

async def update_promotion(promo_id: str, data: Dict[str, Any]) -> bool:
    try:
        update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in data.keys()])
        expression_values = {f":{k}": v for k, v in data.items()}
        
        table.update_item(
            Key={
                "PK": f"PROMOTION#{promo_id}",
                "SK": f"PROMOTION#{promo_id}"
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        return True
    except Exception as e:
        print(f"Error updating promotion: {e}")
        return False

async def delete_promotion(promo_id: str) -> bool:
    try:
        table.delete_item(
            Key={
                "PK": f"PROMOTION#{promo_id}",
                "SK": f"PROMOTION#{promo_id}"
            }
        )
        return True
    except Exception as e:
        print(f"Error deleting promotion: {e}")
        return False

async def list_active_promotions() -> List[Dict[str, Any]]:
    try:
        response = table.scan(
            FilterExpression="begins_with(PK, :pk)",
            ExpressionAttributeValues={":pk": "PROMOTION#"}
        )
        items = response.get("Items", [])
        now = datetime.utcnow().isoformat()
        
        active = []
        for item in items:
            start = item.get("start_date")
            end = item.get("end_date")
            if start <= now <= end:
                active.append({
                    "promo_id": item.get("promo_id"),
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "value": item.get("value"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "usage_limit": item.get("usage_limit"),
                    "usage_count": item.get("usage_count", 0),
                    "min_cart_value": item.get("min_cart_value", 0),
                    "applicable_categories": item.get("applicable_categories", []),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at")
                })
        
        return active
    except Exception as e:
        print(f"Error listing promotions: {e}")
        return []

async def validate_promo_code(promo_code: str, cart_total: float, user_id: str) -> Dict[str, Any]:
    promotion = await get_promotion(promo_code)
    
    if not promotion:
        return {
            "valid": False,
            "discount_amount": 0,
            "message": "Promotion code not found"
        }
    
    now = datetime.utcnow().isoformat()
    if not (promotion["start_date"] <= now <= promotion["end_date"]):
        return {
            "valid": False,
            "discount_amount": 0,
            "message": "Promotion is not currently active"
        }
    
    if promotion["usage_count"] >= promotion["usage_limit"]:
        return {
            "valid": False,
            "discount_amount": 0,
            "message": "Promotion usage limit exceeded"
        }
    
    if cart_total < promotion["min_cart_value"]:
        return {
            "valid": False,
            "discount_amount": 0,
            "message": f"Cart total must be at least {promotion['min_cart_value']}"
        }
    
    user_usage = await check_user_promo_usage(user_id, promo_code)
    if user_usage:
        return {
            "valid": False,
            "discount_amount": 0,
            "message": "You have already used this promotion"
        }
    
    promo_type = promotion["type"]
    if promo_type == "PERCENT":
        discount = cart_total * (promotion["value"] / 100)
    elif promo_type == "FIXED":
        discount = promotion["value"]
    elif promo_type == "BOGO":
        discount = cart_total * 0.5
    else:
        discount = 0
    
    return {
        "valid": True,
        "discount_amount": min(discount, cart_total),
        "message": "Promotion is valid"
    }

async def apply_promo_code(promo_code: str, order_id: str, user_id: str) -> Dict[str, Any]:
    validation = await validate_promo_code(promo_code, float("inf"), user_id)
    
    if not validation["valid"]:
        return {
            "applied": False,
            "discount_amount": 0,
            "message": validation["message"]
        }
    
    try:
        now = datetime.utcnow().isoformat()
        table.put_item(
            Item={
                "PK": f"PROMO_USAGE#{user_id}#{promo_code}",
                "SK": f"PROMO_USAGE#{user_id}#{promo_code}",
                "user_id": user_id,
                "promo_id": promo_code,
                "used_at": now,
                "order_id": order_id
            }
        )
        
        await update_promotion(promo_code, {"usage_count": int(await get_promotion(promo_code) or {}).get("usage_count", 0) + 1})
        
        promotion = await get_promotion(promo_code)
        promo_type = promotion["type"]
        
        if promo_type == "PERCENT":
            discount = float(order_id) * (promotion["value"] / 100) if order_id.replace('.', '', 1).isdigit() else 0
        elif promo_type == "FIXED":
            discount = promotion["value"]
        elif promo_type == "BOGO":
            discount = float(order_id) * 0.5 if order_id.replace('.', '', 1).isdigit() else 0
        else:
            discount = 0
        
        return {
            "applied": True,
            "discount_amount": discount,
            "message": "Promotion applied successfully"
        }
    except Exception as e:
        print(f"Error applying promotion: {e}")
        return {
            "applied": False,
            "discount_amount": 0,
            "message": "Failed to apply promotion"
        }

async def check_user_promo_usage(user_id: str, promo_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = table.get_item(
            Key={
                "PK": f"PROMO_USAGE#{user_id}#{promo_id}",
                "SK": f"PROMO_USAGE#{user_id}#{promo_id}"
            }
        )
        item = response.get("Item")
        return item if item else None
    except Exception as e:
        print(f"Error checking user promo usage: {e}")
        return None
