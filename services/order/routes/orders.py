import os, uuid, time, boto3
from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["orders"])
TABLE = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

def table():
    kw = {"region_name": os.environ.get("AWS_DEFAULT_REGION","us-east-1")}
    if ENDPOINT: kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE)

class CreateOrderReq(BaseModel):
    user_id: Optional[str] = "guest"
    items: list
    total: float
    shipping_address: Optional[str] = ""

@router.get("/orders/{order_id}")
def get_order(order_id: str):
    t = table()
    resp = t.query(KeyConditionExpression=Key("PK").eq(f"ORDER#{order_id}"))
    items = resp.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail="Order not found")
    meta = next((i for i in items if i["SK"] == "METADATA"), None)
    order_items = [i for i in items if i["SK"].startswith("ITEM#")]
    return {"order_id": order_id, "status": meta.get("status","PENDING"),
            "total": float(meta.get("total", 0)), "items": order_items,
            "created_at": meta.get("created_at", "")}

@router.post("/orders")
def create_order(req: CreateOrderReq):
    order_id = str(uuid.uuid4())
    t = table()
    now = int(time.time())
    t.put_item(Item={"PK": f"ORDER#{order_id}", "SK": "METADATA",
        "GSI1PK": f"USER#{req.user_id}", "GSI1SK": f"ORDER#{now}",
        "order_id": order_id, "user_id": req.user_id,
        "status": "PENDING", "total": str(req.total),
        "shipping_address": req.shipping_address, "created_at": str(now)})
    return {"order_id": order_id, "status": "PENDING"}

@router.get("/orders")
def list_orders(user_id: str = "guest"):
    t = table()
    resp = t.query(IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"USER#{user_id}") & Key("GSI1SK").begins_with("ORDER#"))
    items = resp.get("Items", [])
    return {"orders": items, "total": len(items)}
