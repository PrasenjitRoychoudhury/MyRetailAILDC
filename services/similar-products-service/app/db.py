import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, Any, List

table_name = os.getenv("TABLE_NAME", "retail-platform")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table(table_name)

def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by product_id from the retail-platform table.
    PK=PRODUCT#{product_id}, SK=METADATA
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

def query_similar_products(category: str, exclude_product_id: str) -> List[Dict[str, Any]]:
    """
    Query GSI1 for all products in the same category, exclude the requested product,
    sort by price ascending, and return up to 4 items.
    GSI1PK=CATEGORY#{category}, GSI1SK=PRODUCT#{product_id}
    """
    try:
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CATEGORY#{category}")
        )
        items = response.get("Items", [])
        
        filtered_items = [
            item for item in items
            if item.get("product_id", "") != exclude_product_id
        ]
        
        sorted_items = sorted(
            filtered_items,
            key=lambda x: float(x.get("price", 0))
        )
        
        return sorted_items
    except Exception:
        return []
