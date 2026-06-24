from fastapi import APIRouter, HTTPException, status
from app.models import (
    CouponCreate,
    CouponUpdate,
    CouponResponse,
    ValidateCouponRequest,
    ValidateCouponResponse,
)
from app import db
from botocore.exceptions import ClientError
from datetime import datetime, timezone

router = APIRouter(prefix="/v1/coupons", tags=["coupons"])


def _serialize_coupon(item: dict) -> CouponResponse:
    return CouponResponse(
        coupon_code=item["coupon_code"],
        discount_type=item["discount_type"],
        discount_value=float(item["discount_value"]),
        min_order_value=float(item.get("min_order_value", 0.0)),
        max_uses=int(item["max_uses"]) if item.get("max_uses") is not None else None,
        times_used=int(item.get("times_used", 0)),
        expiry_date=item.get("expiry_date"),
        applicable_categories=item.get("applicable_categories", []),
        applicable_product_ids=item.get("applicable_product_ids", []),
        active=bool(item.get("active", True)),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(payload: CouponCreate):
    now = datetime.now(timezone.utc).isoformat()
    item_data = payload.model_dump()
    item_data["times_used"] = 0
    item_data["active"] = True
    item_data["created_at"] = now
    item_data["updated_at"] = now
    try:
        created = db.create_coupon(item_data)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Coupon with code '{payload.coupon_code.upper()}' already exists.",
            )
        raise HTTPException(status_code=500, detail="Database error")
    return _serialize_coupon(created)


@router.get("/{coupon_code}", response_model=CouponResponse)
def get_coupon(coupon_code: str):
    item = db.get_coupon(coupon_code)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon '{coupon_code.upper()}' not found.",
        )
    return _serialize_coupon(item)


@router.patch("/{coupon_code}", response_model=CouponResponse)
def update_coupon(coupon_code: str, payload: CouponUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updated = db.update_coupon(coupon_code, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon '{coupon_code.upper()}' not found.",
        )
    return _serialize_coupon(updated)


@router.delete("/{coupon_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon(coupon_code: str):
    deleted = db.delete_coupon(coupon_code)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon '{coupon_code.upper()}' not found.",
        )


@router.post("/validate", response_model=ValidateCouponResponse)
def validate_coupon(payload: ValidateCouponRequest):
    item = db.get_coupon(payload.coupon_code)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon '{payload.coupon_code.upper()}' not found.",
        )

    if not item.get("active", True):
        return ValidateCouponResponse(
            valid=False,
            discount_amount=0.0,
            final_order_value=payload.order_value,
            message="Coupon is inactive.",
            coupon_code=item["coupon_code"],
        )

    expiry = item.get("expiry_date")
    if expiry:
        expiry_dt = datetime.fromisoformat(expiry)
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expiry_dt:
            return ValidateCouponResponse(
                valid=False,
                discount_amount=0.0,
                final_order_value=payload.order_value,
                message="Coupon has expired.",
                coupon_code=item["coupon_code"],
            )

    max_uses = item.get("max_uses")
    times_used = int(item.get("times_used", 0))
    if max_uses is not None and times_used >= int(max_uses):
        return ValidateCouponResponse(
            valid=False,
            discount_amount=0.0,
            final_order_value=payload.order_value,
            message="Coupon usage limit reached.",
            coupon_code=item["coupon_code"],
        )

    min_order = float(item.get("min_order_value", 0.0))
    if payload.order_value < min_order:
        return ValidateCouponResponse(
            valid=False,
            discount_amount=0.0,
            final_order_value=payload.order_value,
            message=f"Order value must be at least {min_order}.",
            coupon_code=item["coupon_code"],
        )

    applicable_categories = item.get("applicable_categories", [])
    applicable_product_ids = item.get("applicable_product_ids", [])
    if applicable_categories or applicable_product_ids:
        category_match = any(c in applicable_categories for c in payload.categories)
        product_match = any(p in applicable_product_ids for p in payload.product_ids)
        if not category_match and not product_match:
            return ValidateCouponResponse(
                valid=False,
                discount_amount=0.0,
                final_order_value=payload.order_value,
                message="Coupon is not applicable to the provided products or categories.",
                coupon_code=item["coupon_code"],
            )

    discount_type = item["discount_type"]
    discount_value = float(item["discount_value"])
    if discount_type == "percentage":
        discount_amount = round(payload.order_value * (discount_value / 100), 2)
    else:
        discount_amount = min(round(discount_value, 2), payload.order_value)

    final_order_value = round(payload.order_value - discount_amount, 2)

    return ValidateCouponResponse(
        valid=True,
        discount_amount=discount_amount,
        final_order_value=final_order_value,
        message="Coupon applied successfully.",
        coupon_code=item["coupon_code"],
    )
