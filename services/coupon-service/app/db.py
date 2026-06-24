import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional

TABLE_NAME = os.environ.get("TABLE_NAME", "retail-platform")


def get_table():
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(TABLE_NAME)


def coupon_pk(coupon_code: str) -> str:
    return f"COUPON#{coupon_code.upper()}"


COUPON_SK = "METADATA"


def create_coupon(item: dict) -> dict:
    table = get_table()
    code = item["coupon_code"].upper()
    db_item = {
        "PK": coupon_pk(code),
        "SK": COUPON_SK,
        **item,
        "coupon_code": code,
    }
    table.put_item(
        Item=db_item,
        ConditionExpression="attribute_not_exists(PK)",
    )
    return db_item


def get_coupon(coupon_code: str) -> Optional[dict]:
    table = get_table()
    response = table.get_item(
        Key={"PK": coupon_pk(coupon_code), "SK": COUPON_SK}
    )
    return response.get("Item")


def update_coupon(coupon_code: str, updates: dict) -> Optional[dict]:
    table = get_table()
    if not updates:
        return get_coupon(coupon_code)
    update_parts = []
    expr_names = {}
    expr_values = {}
    for idx, (key, val) in enumerate(updates.items()):
        placeholder = f"#attr{idx}"
        value_placeholder = f":val{idx}"
        update_parts.append(f"{placeholder} = {value_placeholder}")
        expr_names[placeholder] = key
        expr_values[value_placeholder] = val
    update_expression = "SET " + ", ".join(update_parts)
    try:
        response = table.update_item(
            Key={"PK": coupon_pk(coupon_code), "SK": COUPON_SK},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ConditionExpression="attribute_exists(PK)",
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise


def delete_coupon(coupon_code: str) -> bool:
    table = get_table()
    try:
        table.delete_item(
            Key={"PK": coupon_pk(coupon_code), "SK": COUPON_SK},
            ConditionExpression="attribute_exists(PK)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def increment_coupon_usage(coupon_code: str) -> Optional[dict]:
    table = get_table()
    try:
        response = table.update_item(
            Key={"PK": coupon_pk(coupon_code), "SK": COUPON_SK},
            UpdateExpression="SET times_used = times_used + :inc",
            ExpressionAttributeValues={":inc": 1},
            ConditionExpression="attribute_exists(PK)",
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
