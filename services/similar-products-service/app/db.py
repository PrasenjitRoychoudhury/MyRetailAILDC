import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, List, Dict, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by product_id from DynamoDB.
    Returns None if product not found.
    """
    try:
        response = table.get_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA"
            }
        )
        item = response.get("Item")
        if item:
            item["id"] = product_id
        return item
    except Exception:
        return None


def get_similar_products(category: str, exclude_product_id: str) -> List[Dict[str, Any]]:
    """
    Scan DynamoDB for all products in a given category.
    Exclude the product with exclude_product_id.
    Sort by rating (average_rating) in descending order.
    """
    try:
        response = table.scan(
            FilterExpression=Attr("category").eq(category)
        )
        items = response.get("Items", [])

        filtered_items = []
        for item in items:
            item_id = item.get("id")
            if item_id and item_id != exclude_product_id:
                filtered_items.append(item)

        filtered_items.sort(
            key=lambda x: float(x.get("rating", {}).get("average_rating", 0)),
            reverse=True
        )

        return filtered_items
    except Exception:
        return []
