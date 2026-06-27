import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, List, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table(TABLE_NAME)

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
        return response.get("Item", None)
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        return None

def query_similar_products(category: str, exclude_product_id: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Query GSI1 to find products in the same category.
    GSI1PK=CATEGORY#{category}, sorted by price ascending.
    Excludes the queried product_id.
    Returns max 4 items.
    """
    try:
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CATEGORY#{category}"),
            ScanIndexForward=True
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
        
        return sorted_items[:limit]
    except Exception as e:
        print(f"Error querying similar products for category {category}: {e}")
        return []
