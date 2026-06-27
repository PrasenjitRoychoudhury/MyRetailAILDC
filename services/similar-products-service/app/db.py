import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, List, Dict, Any
from decimal import Decimal

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def _to_float(val):
    if isinstance(val, Decimal): return float(val)
    try: return float(val)
    except: return 0.0

def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = table.get_item(Key={"PK": f"PRODUCT#{product_id}", "SK": "METADATA"})
        return response.get("Item")
    except Exception:
        return None

def scan_products_by_category(category: str) -> List[Dict[str, Any]]:
    try:
        response = table.scan(FilterExpression=Attr("category").eq(category))
        items = response.get("Items", [])
        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=Attr("category").eq(category),
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        return items
    except Exception:
        return []
