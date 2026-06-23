import os, time, boto3
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
from pydantic import BaseModel

router = APIRouter(tags=["coupon"])
TABLE = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")


def table():
    kw = {"region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
    if ENDPOINT:
        kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE)


class ValidateReq(BaseModel):
    code: str
    cart_total: float


class RedeemReq(BaseModel):
    code: str
    order_id: str


def _money(value) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _get_coupon(code: str):
    resp = table().get_item(Key={"PK": f"COUPON#{code.upper()}", "SK": "METADATA"})
    return resp.get("Item")


@router.post("/coupons/validate")
def validate_coupon(req: ValidateReq):
    coupon = _get_coupon(req.code)
    if not coupon:
        return {"valid": False, "error": "Invalid coupon code."}
    if coupon.get("status") == "REDEEMED":
        return {"valid": False, "error": "This coupon has already been used."}

    value = float(coupon["discount_value"])
    discount_type = coupon["discount_type"]
    if discount_type == "percentage":
        discounted_total = _money(max(0.0, req.cart_total - req.cart_total * value / 100.0))
    else:
        discounted_total = _money(max(0.0, req.cart_total - value))

    return {
        "valid": True,
        "discount_type": discount_type,
        "discount_value": value,
        "discounted_total": discounted_total,
    }


@router.post("/coupons/redeem")
def redeem_coupon(req: RedeemReq):
    code = req.code.upper()
    if not _get_coupon(code):
        raise HTTPException(status_code=404, detail="Invalid coupon code.")

    try:
        table().update_item(
            Key={"PK": f"COUPON#{code}", "SK": "METADATA"},
            UpdateExpression="SET #s = :redeemed, redeemed_at = :now, redeemed_by_order_id = :order_id",
            ConditionExpression="#s = :active",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":redeemed": "REDEEMED",
                ":active": "ACTIVE",
                ":now": int(time.time()),
                ":order_id": req.order_id,
            },
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail="This coupon has already been used.")
        raise

    return {"status": "redeemed", "code": code, "order_id": req.order_id}
