import os, time, uuid, boto3, requests
from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

router = APIRouter(tags=["cart"])
TABLE = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")
PRODUCT_URL = os.environ.get("PRODUCT_CATALOGUE_URL", "http://localhost:8001")
CART_TTL = 604800  # 7 days

def table():
    kw = {"region_name": os.environ.get("AWS_DEFAULT_REGION","us-east-1")}
    if ENDPOINT: kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE)

class AddItemReq(BaseModel):
    product_id: str
    qty: int

class UpdateItemReq(BaseModel):
    qty: int

class CheckoutReq(BaseModel):
    user_id: Optional[str] = "guest"
    shipping_address: Optional[str] = ""

def _get_cart(session_id: str):
    t = table()
    resp = t.query(KeyConditionExpression=Key("PK").eq(f"CART#{session_id}"))
    items = resp.get("Items", [])
    cart_items = [i for i in items if i["SK"].startswith("ITEM#")]
    return cart_items

@router.get("/cart/{session_id}")
def get_cart(session_id: str):
    items = _get_cart(session_id)
    subtotal = sum(float(i["unit_price"]) * int(i["qty"]) for i in items)
    return {"session_id": session_id, "items": [
        {"product_id": i["SK"].replace("ITEM#",""), "name": i.get("name",""), "qty": int(i["qty"]), "unit_price": float(i["unit_price"]), "image_url": i.get("image_url","")}
        for i in items], "subtotal": round(subtotal, 2), "item_count": len(items)}

@router.post("/cart/{session_id}/items")
def add_item(session_id: str, req: AddItemReq):
    # validate product via SVC-1
    try:
        r = requests.get(f"{PRODUCT_URL}/v1/products/{req.product_id}", timeout=5)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail="Product not found")
        product = r.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Product service unavailable")
    t = table()
    expires = int(time.time()) + CART_TTL
    t.put_item(Item={
        "PK": f"CART#{session_id}", "SK": f"ITEM#{req.product_id}",
        "qty": req.qty, "unit_price": Decimal(str(product["price"])),
        "name": product["name"], "image_url": product["image_url"],
        "added_at": int(time.time()), "expires_at": expires,
    })
    return get_cart(session_id)

@router.put("/cart/{session_id}/items/{product_id}")
def update_item(session_id: str, product_id: str, req: UpdateItemReq):
    if req.qty <= 0:
        return remove_item(session_id, product_id)
    t = table()
    t.update_item(
        Key={"PK": f"CART#{session_id}", "SK": f"ITEM#{product_id}"},
        UpdateExpression="SET qty = :q",
        ExpressionAttributeValues={":q": req.qty},
    )
    return get_cart(session_id)

@router.delete("/cart/{session_id}/items/{product_id}")
def remove_item(session_id: str, product_id: str):
    table().delete_item(Key={"PK": f"CART#{session_id}", "SK": f"ITEM#{product_id}"})
    return get_cart(session_id)

@router.delete("/cart/{session_id}")
def clear_cart(session_id: str):
    t = table()
    items = _get_cart(session_id)
    for item in items:
        t.delete_item(Key={"PK": f"CART#{session_id}", "SK": item["SK"]})
    return {"status": "cleared", "session_id": session_id}

@router.post("/cart/{session_id}/checkout")
def checkout(session_id: str, req: CheckoutReq):
    items = _get_cart(session_id)
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    order_id = str(uuid.uuid4())
    # In prod this publishes to EventBridge; locally just return order_id
    return {"order_id": order_id, "status": "PENDING", "item_count": len(items),
            "total": round(sum(float(i["unit_price"]) * int(i["qty"]) for i in items), 2)}
