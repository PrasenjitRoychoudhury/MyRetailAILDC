import os, time, boto3
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel

router = APIRouter(tags=["coupon"])
TABLE = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

DISCOUNT_TYPES = ("percentage", "fixed")


def table():
    kw = {"region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
    if ENDPOINT:
        kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE)


# ---------- request models ----------
class ValidateReq(BaseModel):
    code: str
    order_total: float
    user_id: Optional[str] = "guest"


class ApplyReq(BaseModel):
    code: str
    order_total: float
    user_id: Optional[str] = "guest"


class CreateCouponReq(BaseModel):
    code: str
    discount_type: str          # "percentage" | "fixed"
    discount_value: float       # percent (0-100) or fixed amount in £
    expires_at: str             # ISO date, e.g. "2026-12-31"
    min_order: Optional[float] = 0
    max_uses: Optional[int] = 0  # 0 == unlimited global uses


# ---------- helpers ----------
def _money(value) -> float:
    """Round to 2 dp, half-up, returned as float for JSON responses."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _get_coupon(code: str):
    resp = table().get_item(Key={"PK": f"COUPON#{code.upper()}", "SK": "METADATA"})
    return resp.get("Item")


def _is_expired(expires_at: str) -> bool:
    try:
        exp = datetime.strptime(expires_at, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return True
    return date.today() > exp


def _user_redeemed(code: str, user_id: str) -> bool:
    resp = table().get_item(
        Key={"PK": f"COUPON#{code.upper()}", "SK": f"REDEMPTION#{user_id}"}
    )
    return "Item" in resp


def _compute_discount(coupon: dict, order_total: float) -> float:
    value = float(coupon["discount_value"])
    if coupon["discount_type"] == "percentage":
        discount = order_total * value / 100.0
    else:  # fixed
        discount = value
    return _money(min(discount, order_total))


def _validate(coupon: Optional[dict], code: str, order_total: float, user_id: str):
    """Run all coupon rules. Raises HTTPException on failure, returns discount summary."""
    if not coupon or not coupon.get("active", True):
        raise HTTPException(status_code=404, detail="Coupon not found or inactive")
    if _is_expired(coupon.get("expires_at", "")):
        raise HTTPException(status_code=400, detail="Coupon has expired")
    min_order = float(coupon.get("min_order", 0))
    if order_total < min_order:
        raise HTTPException(
            status_code=400,
            detail=f"Order total £{order_total:.2f} is below minimum £{min_order:.2f}",
        )
    max_uses = int(coupon.get("max_uses", 0))
    uses_count = int(coupon.get("uses_count", 0))
    if max_uses and uses_count >= max_uses:
        raise HTTPException(status_code=409, detail="Coupon usage limit reached")
    if _user_redeemed(code, user_id):
        raise HTTPException(status_code=409, detail="Coupon already used by this user")

    discount = _compute_discount(coupon, order_total)
    return {
        "code": coupon["code"],
        "discount_type": coupon["discount_type"],
        "discount_value": float(coupon["discount_value"]),
        "discount": discount,
        "order_total": _money(order_total),
        "final_total": _money(max(0.0, order_total - discount)),
    }


# ---------- endpoints ----------
@router.post("/coupons/validate")
def validate_coupon(req: ValidateReq):
    """Stateless check — does NOT consume the coupon."""
    coupon = _get_coupon(req.code)
    result = _validate(coupon, req.code, req.order_total, req.user_id)
    result["valid"] = True
    return result


@router.post("/cart/{session_id}/coupon")
def apply_coupon(session_id: str, req: ApplyReq):
    """Validate then atomically consume the coupon and attach it to the session."""
    code = req.code.upper()
    coupon = _get_coupon(code)
    result = _validate(coupon, code, req.order_total, req.user_id)
    t = table()

    # Atomically increment the global use counter, guarding max_uses.
    max_uses = int(coupon.get("max_uses", 0))
    try:
        if max_uses:
            t.update_item(
                Key={"PK": f"COUPON#{code}", "SK": "METADATA"},
                UpdateExpression="SET uses_count = if_not_exists(uses_count, :z) + :one",
                ConditionExpression="attribute_not_exists(uses_count) OR uses_count < :max",
                ExpressionAttributeValues={":one": 1, ":z": 0, ":max": max_uses},
            )
        else:
            t.update_item(
                Key={"PK": f"COUPON#{code}", "SK": "METADATA"},
                UpdateExpression="SET uses_count = if_not_exists(uses_count, :z) + :one",
                ExpressionAttributeValues={":one": 1, ":z": 0},
            )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail="Coupon usage limit reached")
        raise

    # Record per-user redemption (single use per user).
    try:
        t.put_item(
            Item={
                "PK": f"COUPON#{code}",
                "SK": f"REDEMPTION#{req.user_id}",
                "code": code,
                "user_id": req.user_id,
                "session_id": session_id,
                "redeemed_at": int(time.time()),
            },
            ConditionExpression="attribute_not_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Roll back the counter we just incremented.
            t.update_item(
                Key={"PK": f"COUPON#{code}", "SK": "METADATA"},
                UpdateExpression="SET uses_count = uses_count - :one",
                ExpressionAttributeValues={":one": 1},
            )
            raise HTTPException(status_code=409, detail="Coupon already used by this user")
        raise

    # Attach the applied coupon to the session (owned COUPON# prefix, never CART#).
    t.put_item(Item={
        "PK": f"COUPON#SESSION#{session_id}",
        "SK": "APPLIED",
        "code": code,
        "user_id": req.user_id,
        "discount": Decimal(str(result["discount"])),
        "order_total": Decimal(str(result["order_total"])),
        "final_total": Decimal(str(result["final_total"])),
        "applied_at": int(time.time()),
        "entity_type": "COUPON_APPLICATION",
    })

    result["session_id"] = session_id
    result["applied"] = True
    return result


@router.delete("/cart/{session_id}/coupon")
def remove_coupon(session_id: str):
    """Detach the coupon from the session and release its consumption."""
    t = table()
    resp = t.get_item(Key={"PK": f"COUPON#SESSION#{session_id}", "SK": "APPLIED"})
    applied = resp.get("Item")
    if not applied:
        raise HTTPException(status_code=404, detail="No coupon applied to this session")

    code = applied["code"]
    user_id = applied.get("user_id", "guest")

    t.delete_item(Key={"PK": f"COUPON#SESSION#{session_id}", "SK": "APPLIED"})
    t.delete_item(Key={"PK": f"COUPON#{code}", "SK": f"REDEMPTION#{user_id}"})
    try:
        t.update_item(
            Key={"PK": f"COUPON#{code}", "SK": "METADATA"},
            UpdateExpression="SET uses_count = uses_count - :one",
            ConditionExpression="uses_count > :z",
            ExpressionAttributeValues={":one": 1, ":z": 0},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise

    return {"status": "removed", "session_id": session_id, "code": code}


@router.post("/coupons", status_code=201)
def create_coupon(req: CreateCouponReq):
    """Admin: create a coupon definition."""
    if req.discount_type not in DISCOUNT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"discount_type must be one of {DISCOUNT_TYPES}",
        )
    if req.discount_value <= 0:
        raise HTTPException(status_code=400, detail="discount_value must be positive")
    if req.discount_type == "percentage" and req.discount_value > 100:
        raise HTTPException(status_code=400, detail="percentage discount cannot exceed 100")
    if _is_expired(req.expires_at):
        raise HTTPException(status_code=400, detail="expires_at must be a future ISO date (YYYY-MM-DD)")

    code = req.code.upper()
    t = table()
    try:
        t.put_item(
            Item={
                "PK": f"COUPON#{code}",
                "SK": "METADATA",
                "code": code,
                "discount_type": req.discount_type,
                "discount_value": Decimal(str(req.discount_value)),
                "min_order": Decimal(str(req.min_order or 0)),
                "expires_at": req.expires_at,
                "max_uses": int(req.max_uses or 0),
                "uses_count": 0,
                "active": True,
                "entity_type": "COUPON",
                "created_at": int(time.time()),
            },
            ConditionExpression="attribute_not_exists(PK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail=f"Coupon {code} already exists")
        raise

    return {"status": "created", "code": code}
