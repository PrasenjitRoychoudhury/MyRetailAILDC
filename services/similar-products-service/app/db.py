import os
import boto3
from typing import Optional, List
from app.models import SimilarProduct

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


async def get_product_category(product_id: str) -> Optional[str]:
    """
    Retrieve the category of a product using GetItem.
    PK=PRODUCT#{product_id}, SK=METADATA
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
            return item.get("category")
        return None
    except Exception:
        return None


async def get_similar_products(
    product_id: str,
    category: str,
    limit: int = 4
) -> List[SimilarProduct]:
    """
    Find similar products using Scan with FilterExpression.
    Excludes current product and returns products in same category.
    """
    try:
        response = table.scan(
            FilterExpression="#category = :cat AND PK <> :pk",
            ExpressionAttributeNames={
                "#category": "category"
            },
            ExpressionAttributeValues={
                ":cat": category,
                ":pk": f"PRODUCT#{product_id}"
            },
            ProjectionExpression="PK,#name,#price,image_url,#category",
            Limit=limit
        )
        
        items = response.get("Items", [])
        similar_products = []
        
        for item in items:
            # Strip PRODUCT# prefix from PK to get product_id
            pk = item.get("PK", "")
            extracted_product_id = pk.replace("PRODUCT#", "")
            
            similar_products.append(
                SimilarProduct(
                    product_id=extracted_product_id,
                    name=item.get("name", ""),
                    price=float(item.get("price", 0)),
                    image_url=item.get("image_url", ""),
                    category=item.get("category", "")
                )
            )
        
        return similar_products
    except Exception:
        return []
