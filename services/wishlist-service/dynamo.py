import os
import uuid
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime, timezone

TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", os.environ.get("DYNAMODB_TABLE", "retail-platform"))
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")
REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))


def _table():
    kw = {"region_name": REGION}
    if ENDPOINT:
        kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE_NAME)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_wishlist_meta(user_id: str) -> dict:
    t = _table()
    pk, sk = f"USER#{user_id}", "WISHLIST#default"
    resp = t.get_item(Key={"PK": pk, "SK": sk})
    if "Item" in resp:
        return resp["Item"]
    now = _now_iso()
    item = {
        "PK": pk, "SK": sk,
        "name": "My Wishlist",
        "shareToken": None,
        "createdAt": now,
        "updatedAt": now,
    }
    t.put_item(Item=item)
    return item


def get_wishlist(user_id: str):
    t = _table()
    resp = t.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("WISHLIST")
    )
    rows = resp.get("Items", [])
    meta = next((r for r in rows if r["SK"] == "WISHLIST#default"), None)
    items = [r for r in rows if r["SK"].startswith("WISHLIST_ITEM#")]
    return meta, items


def add_item(user_id: str, product_id: str, name: str, price: float, image_url: str) -> None:
    _ensure_wishlist_meta(user_id)
    _table().put_item(Item={
        "PK": f"USER#{user_id}",
        "SK": f"WISHLIST_ITEM#{product_id}",
        "productId": product_id,
        "name": name,
        "price": Decimal(str(price)),
        "imageUrl": image_url,
        "addedAt": _now_iso(),
    })


def remove_item(user_id: str, product_id: str) -> None:
    _table().delete_item(Key={"PK": f"USER#{user_id}", "SK": f"WISHLIST_ITEM#{product_id}"})


def get_or_create_share_token(user_id: str) -> str:
    t = _table()
    pk, sk = f"USER#{user_id}", "WISHLIST#default"
    resp = t.get_item(Key={"PK": pk, "SK": sk})
    meta = resp.get("Item") or _ensure_wishlist_meta(user_id)
    if meta.get("shareToken"):
        return meta["shareToken"]
    token = str(uuid.uuid4())
    wishlist_name = meta.get("name", "My Wishlist")
    t.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression="SET shareToken = :t, updatedAt = :u",
        ExpressionAttributeValues={":t": token, ":u": _now_iso()},
    )
    # O(1) lookup record keyed by the token itself
    t.put_item(Item={
        "PK": f"SHARE#{token}",
        "SK": "META",
        "userId": user_id,
        "wishlistName": wishlist_name,
    })
    return token


def get_shared_wishlist(token: str):
    t = _table()
    resp = t.get_item(Key={"PK": f"SHARE#{token}", "SK": "META"})
    meta = resp.get("Item")
    if not meta:
        return None, None, None
    user_id = meta["userId"]
    wishlist_name = meta["wishlistName"]
    items_resp = t.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("WISHLIST_ITEM#")
    )
    return user_id, wishlist_name, items_resp.get("Items", [])
