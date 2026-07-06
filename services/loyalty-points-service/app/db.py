import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timezone

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

resource = boto3.resource("dynamodb")
table = resource.Table(TABLE_NAME)

def get_customer_balance(customer_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve current balance item for customer."""
    response = table.get_item(
        Key={"PK": f"CUSTOMER#{customer_id}", "SK": "LOYALTY#BALANCE"}
    )
    return response.get("Item")

def create_balance_item(customer_id: str, points: int, timestamp: str) -> Dict[str, Any]:
    """Create or update balance item atomically with transaction."""
    return {
        "PK": f"CUSTOMER#{customer_id}",
        "SK": "LOYALTY#BALANCE",
        "points_balance": points,
        "updated_at": timestamp,
        "created_at": timestamp,
    }

def create_transaction_item(
    customer_id: str,
    txn_type: str,
    points: int,
    timestamp: str,
    order_id: Optional[str] = None,
    order_total_gbp: Optional[float] = None,
    redemption_id: Optional[str] = None,
    discount_gbp: Optional[float] = None,
) -> Dict[str, Any]:
    """Create immutable transaction ledger item."""
    txn_id = str(uuid.uuid4())
    item = {
        "PK": f"CUSTOMER#{customer_id}",
        "SK": f"LOYALTY#TXN#{timestamp}#{txn_id}",
        "type": txn_type,
        "points": points,
        "created_at": timestamp,
    }
    if order_id:
        item["order_id"] = order_id
    if order_total_gbp is not None:
        item["order_total_gbp"] = Decimal(str(order_total_gbp))
    if redemption_id:
        item["redemption_id"] = redemption_id
    if discount_gbp is not None:
        item["discount_gbp"] = Decimal(str(discount_gbp))
    return item, txn_id

def check_duplicate_award(customer_id: str, order_id: str) -> bool:
    """Check if award already exists for this order."""
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"CUSTOMER#{customer_id}") &
                               Key("SK").begins_with("LOYALTY#TXN#"),
        FilterExpression=Attr("type").eq("AWARD") & Attr("order_id").eq(order_id),
        Limit=1
    )
    return len(response.get("Items", [])) > 0

def check_redemption_exists(customer_id: str, redemption_id: str) -> bool:
    """Check if redemption transaction exists."""
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"CUSTOMER#{customer_id}") &
                               Key("SK").begins_with("LOYALTY#TXN#"),
        FilterExpression=Attr("type").eq("REDEEM") & Attr("redemption_id").eq(redemption_id),
        Limit=1
    )
    return len(response.get("Items", [])) > 0

def check_reversal_exists(customer_id: str, redemption_id: str) -> bool:
    """Check if reversal already exists for this redemption."""
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"CUSTOMER#{customer_id}") &
                               Key("SK").begins_with("LOYALTY#TXN#"),
        FilterExpression=Attr("type").eq("REVERSAL") & Attr("redemption_id").eq(redemption_id),
        Limit=1
    )
    return len(response.get("Items", [])) > 0

def transact_write_balance_and_transaction(
    balance_item: Dict[str, Any],
    transaction_item: Dict[str, Any],
    customer_id: str,
    required_balance: Optional[int] = None,
) -> bool:
    """Atomic write of balance and transaction using TransactWriteItems."""
    transact_items = [
        {
            "Put": {
                "TableName": TABLE_NAME,
                "Item": balance_item,
            }
        },
        {
            "Put": {
                "TableName": TABLE_NAME,
                "Item": transaction_item,
            }
        },
    ]

    if required_balance is not None:
        transact_items[0]["Put"]["ConditionExpression"] = 
            "attribute_not_exists(points_balance) OR points_balance >= :required"
        transact_items[0]["Put"]["ExpressionAttributeValues"] = {
            ":required": required_balance
        }

    try:
        client = boto3.client("dynamodb")
        client.transact_write_items(TransactItems=transact_items)
        return True
    except client.exceptions.ConditionalCheckFailedException:
        return False
    except Exception as e:
        raise e

def get_current_timestamp() -> str:
    """Return ISO8601 UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
