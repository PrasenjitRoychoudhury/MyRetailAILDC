import boto3
import os
from typing import Optional, Dict, Any, Tuple, List
from botocore.exceptions import ClientError

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

async def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve product details from DynamoDB using PK=PRODUCT#{id}, SK=METADATA
    """
    try:
        response = table.get_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA"
            }
        )
        item = response.get("Item")
        if not item:
            return None
        
        return {
            "id": product_id,
            "name": item.get("name"),
            "description": item.get("description"),
            "price": float(item.get("price", 0)),
            "category": item.get("category"),
            "stock_quantity": int(item.get("stock_quantity", 0)),
            "image_url": item.get("image_url"),
            "rating": {
                "average_rating": float(item.get("average_rating", 0)),
                "rating_count": int(item.get("rating_count", 0))
            }
        }
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")

async def list_products(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List products with optional category filtering.
    Returns list of products and total count.
    """
    try:
        scan_kwargs = {}
        if category:
            scan_kwargs["FilterExpression"] = "#cat = :cat"
            scan_kwargs["ExpressionAttributeNames"] = {"#cat": "category"}
            scan_kwargs["ExpressionAttributeValues"] = {":cat": category}
        
        response = table.scan(**scan_kwargs)
        items = response.get("Items", [])
        
        products = []
        for item in items:
            if item.get("SK") == "METADATA" and item.get("PK", "").startswith("PRODUCT#"):
                product_id = item["PK"].replace("PRODUCT#", "")
                products.append({
                    "id": product_id,
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "price": float(item.get("price", 0)),
                    "category": item.get("category"),
                    "stock_quantity": int(item.get("stock_quantity", 0)),
                    "image_url": item.get("image_url"),
                    "rating": {
                        "average_rating": float(item.get("average_rating", 0)),
                        "rating_count": int(item.get("rating_count", 0))
                    }
                })
        
        paginated = products[offset:offset + limit]
        return paginated, len(products)
    except ClientError as e:
        raise Exception(f"DynamoDB error: {str(e)}")
