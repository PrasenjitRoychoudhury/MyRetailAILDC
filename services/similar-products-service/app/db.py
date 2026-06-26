import os
import boto3
from typing import Optional, List
from app.models import SimilarProduct

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


async def get_product_category(product_id: str) -> Optional[str]:
    response = table.get_item(
        Key={"PK": f"PRODUCT#{product_id}", "SK": "METADATA"}
    )
    item = response.get("Item")
    return item.get("category") if item else None


async def get_similar_products(
    product_id: str,
    category: str,
    limit: int = 4
) -> List[SimilarProduct]:
    try:
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :gsi1pk",
            FilterExpression="PK <> :exclude",
            ExpressionAttributeValues={
                ":gsi1pk": f"CATEGORY#{category}",
                ":exclude": f"PRODUCT#{product_id}"
            },
            Limit=20
        )
        items = response.get("Items", [])[:limit]
        return [
            SimilarProduct(
                product_id=item.get("product_id", item.get("PK","").replace("PRODUCT#","")),
                name=item.get("name", ""),
                price=float(item.get("price", 0)),
                image_url=item.get("image_url", ""),
                category=item.get("category", "")
            )
            for item in items
        ]
    except Exception as e:
        print(f"[db] get_similar_products error: {e}")
        return []
