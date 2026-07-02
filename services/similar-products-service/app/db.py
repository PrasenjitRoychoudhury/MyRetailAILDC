import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, List, Dict, Any

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

def get_dynamodb_resource():
    """Get DynamoDB resource (uses IAM role, no hardcoded credentials)."""
    return boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-2"))

def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by product_id from DynamoDB.
    
    PK: PRODUCT#{product_id}
    SK: METADATA
    
    Returns the item dict or None if not found.
    """
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.get_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA"
            }
        )
        return response.get("Item")
    except Exception as e:
        raise Exception(f"DynamoDB get_item failed: {str(e)}")

def get_products_by_category(category: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve all products in a category using GSI1.
    
    GSI1PK: CATEGORY#{category}
    GSI1SK: PRODUCT#{product_id}
    
    Returns list of product items.
    """
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CATEGORY#{category}"),
            Limit=limit
        )
        return response.get("Items", [])
    except Exception as e:
        raise Exception(f"DynamoDB query failed: {str(e)}")
