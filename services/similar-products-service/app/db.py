import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, List, Dict, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table(TABLE_NAME)


async def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a product by product_id using PK=PRODUCT#{product_id}, SK=METADATA
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


async def query_similar_products(
    category: str, exclude_product_id: str, limit: int = 4
) -> List[Dict[str, Any]]:
    """
    Query products in the same category using GSI1.
    GSI1PK=CATEGORY#{category}, GSI1SK=PRODUCT#{product_id}
    Excludes the queried product and returns up to 4 items sorted by price ascending.
    """
    try:
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CATEGORY#{category}"),
        )
        
        items = response.get("Items", [])
        
        # Filter out the current product and sort by price
        filtered_items = [
            item for item in items
            if item.get("product_id", "") != exclude_product_id
        ]
        
        # Sort by price ascending
        filtered_items.sort(
            key=lambda x: float(x.get("price", 0))
        )
        
        # Return first 4 items
        return filtered_items[:limit]
    except Exception:
        return []
