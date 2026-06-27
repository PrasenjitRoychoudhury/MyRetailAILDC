import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, List, Dict, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by PK=PRODUCT#{product_id}, SK=METADATA
    """
    try:
        response = table.get_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA"
            }
        )
        return response.get("Item")
    except Exception:
        return None

def query_products_by_category(category: str, exclude_product_id: str = "") -> List[Dict[str, Any]]:
    """
    Query GSI1 where GSI1PK=CATEGORY#{category}
    Exclude the queried product_id from results
    Sort by price ascending (application layer)
    """
    try:
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CATEGORY#{category}")
        )
        items = response.get("Items", [])
        
        filtered = [
            item for item in items
            if item.get("id") != exclude_product_id
        ]
        
        sorted_items = sorted(
            filtered,
            key=lambda x: float(x.get("price", 0))
        )
        
        return sorted_items
    except Exception:
        return []
