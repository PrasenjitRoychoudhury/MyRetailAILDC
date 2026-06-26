import os
import boto3
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError


class DynamoDBClient:
    def __init__(self):
        self.table_name = os.getenv("TABLE_NAME", "retail-platform")
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamodb.Table(self.table_name)
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product metadata by product_id.
        
        Args:
            product_id: The product ID
        
        Returns:
            Product item dict or None if not found
        """
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"PRODUCT#{product_id}",
                    "SK": "METADATA"
                },
                ProjectionExpression="product_id, #name, price, image_url, category, #desc",
                ExpressionAttributeNames={
                    "#name": "name",
                    "#desc": "description"
                }
            )
            return response.get("Item")
        except ClientError as e:
            print(f"Error getting product {product_id}: {e}")
            return None
    
    async def query_similar_products(
        self,
        category: str,
        exclude_product_id: str,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Query products from same category, excluding the current product.
        Uses GSI1 index: GSI1PK = CATEGORY#{category}
        
        Args:
            category: The product category
            exclude_product_id: Product ID to exclude from results
            limit: Maximum products to return (will query 20 then filter)
        
        Returns:
            List of similar product items
        """
        try:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :gsi1pk",
                FilterExpression="PK <> :exclude_pk",
                ExpressionAttributeValues={
                    ":gsi1pk": f"CATEGORY#{category}",
                    ":exclude_pk": f"PRODUCT#{exclude_product_id}"
                },
                ProjectionExpression="product_id, #name, price, image_url, category",
                ExpressionAttributeNames={
                    "#name": "name"
                },
                Limit=20
            )
            
            items = response.get("Items", [])
            # Return only up to the requested limit
            return items[:limit]
        except ClientError as e:
            print(f"Error querying similar products for category {category}: {e}")
            return []
