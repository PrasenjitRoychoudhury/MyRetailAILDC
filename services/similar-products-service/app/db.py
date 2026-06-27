import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, List, Dict, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table(TABLE_NAME)


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by product_id using PK=PRODUCT#{product_id}, SK=METADATA.
    """
    try:
        response = table.get_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA"
            }
        )
        return response.get("Item")
    except Exception as e:
        print(f"Error retrieving product {product_id}: {str(e)}")
        return None


def query_similar_products(category: str, exclude_product_id: str) -> List[Dict[str, Any]]:
    """
    Query GSI1 for all products in the same category, excluding the given product_id.
    Sort by rating_rate descending and return top 4.
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
            key=lambda x: float(x.get("rating_rate", 0)),
            reverse=True
        )
        
        return sorted_items[:4]
    except Exception as e:
        print(f"Error querying similar products for category {category}: {str(e)}")
        return []
