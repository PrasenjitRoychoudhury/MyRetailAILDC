import boto3
import os
from typing import Optional, Dict, Any, List

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


async def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by product_id from DynamoDB.
    PK = PRODUCT#{product_id}, SK = METADATA
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
        print(f"Error retrieving product {product_id}: {e}")
        return None


async def scan_products_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Scan retail-platform table with filter expression on category attribute.
    Returns all products in the specified category.
    """
    try:
        products = []
        response = table.scan(
            FilterExpression="#cat = :category",
            ExpressionAttributeNames={"#cat": "category"},
            ExpressionAttributeValues={":category": category}
        )
        
        products.extend(response.get("Items", []))
        
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression="#cat = :category",
                ExpressionAttributeNames={"#cat": "category"},
                ExpressionAttributeValues={":category": category},
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            products.extend(response.get("Items", []))
        
        return products
    except Exception as e:
        print(f"Error scanning products by category {category}: {e}")
        return []
