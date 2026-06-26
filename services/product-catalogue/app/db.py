import os
import boto3
from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

async def get_product_by_id(product_id: Optional[str] = None, category: Optional[str] = None, limit: int = 20) -> Optional[Dict[str, Any]]:
    """
    Retrieve product by ID from DynamoDB.
    PK: PRODUCT#{id}, SK: METADATA
    """
    if product_id:
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
                "product_id": product_id,
                "name": item.get("name"),
                "description": item.get("description"),
                "price": float(item.get("price", 0)),
                "category": item.get("category"),
                "stock_quantity": int(item.get("stock_quantity", 0)),
                "image_url": item.get("image_url"),
                "average_rating": float(item.get("average_rating", 0.0)),
                "rating_count": int(item.get("rating_count", 0))
            }
        
        except ClientError as e:
            raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")
    
    # If no product_id, scan for products by category
    try:
        if category:
            response = table.scan(
                FilterExpression="#cat = :cat",
                ExpressionAttributeNames={"#cat": "category"},
                ExpressionAttributeValues={":cat": category},
                Limit=limit
            )
        else:
            response = table.scan(Limit=limit)
        
        products = []
        for item in response.get("Items", []):
            if item.get("SK") == "METADATA":
                product_id = item.get("PK", "").replace("PRODUCT#", "")
                products.append({
                    "product_id": product_id,
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "price": float(item.get("price", 0)),
                    "category": item.get("category"),
                    "stock_quantity": int(item.get("stock_quantity", 0)),
                    "image_url": item.get("image_url"),
                    "average_rating": float(item.get("average_rating", 0.0)),
                    "rating_count": int(item.get("rating_count", 0))
                })
        
        return products
    
    except ClientError as e:
        raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")

async def create_product(product_id: str, product_data: Dict[str, Any]) -> bool:
    """
    Create a new product in DynamoDB.
    """
    try:
        table.put_item(
            Item={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA",
                "name": product_data["name"],
                "description": product_data["description"],
                "price": product_data["price"],
                "category": product_data["category"],
                "stock_quantity": product_data["stock_quantity"],
                "image_url": product_data["image_url"],
                "average_rating": product_data.get("average_rating", 0.0),
                "rating_count": product_data.get("rating_count", 0)
            }
        )
        return True
    
    except ClientError as e:
        raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")
