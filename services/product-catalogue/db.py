import os
import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

def get_table():
    kwargs = {"region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
    if ENDPOINT:
        kwargs["endpoint_url"] = ENDPOINT
    dynamodb = boto3.resource("dynamodb", **kwargs)
    return dynamodb.Table(TABLE_NAME)

def get_product(product_id: str):
    table = get_table()
    resp = table.get_item(Key={"PK": f"PRODUCT#{product_id}", "SK": "METADATA"})
    return resp.get("Item")

def list_products(category: str = None, limit: int = 20, last_key: str = None):
    table = get_table()
    if category:
        kwargs = {
            "IndexName": "GSI1",
            "KeyConditionExpression": Key("GSI1PK").eq(f"CATEGORY#{category}"),
            "Limit": limit,
        }
    else:
        kwargs = {
            "FilterExpression": "entity_type = :t",
            "ExpressionAttributeValues": {":t": "PRODUCT"},
            "Limit": limit,
        }
    if last_key:
        kwargs["ExclusiveStartKey"] = {"PK": last_key, "SK": "METADATA"}
    resp = table.scan(**kwargs) if not category else table.query(**kwargs)
    return resp.get("Items", []), resp.get("LastEvaluatedKey")

def list_categories():
    table = get_table()
    resp = table.scan(
        FilterExpression="entity_type = :t",
        ExpressionAttributeValues={":t": "CATEGORY"},
    )
    return resp.get("Items", [])
