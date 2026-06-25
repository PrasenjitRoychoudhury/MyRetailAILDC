from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid
from app.models import (
    PromotionCreate,
    PromotionResponse,
    ValidatePromoRequest,
    ValidatePromoResponse,
    ApplyPromoRequest,
    ApplyPromoResponse,
    ProblemDetail
)
from app.db import (
    create_promotion,
    get_promotion_by_id,
    get_promotion_by_code,
    list_active_promotions,
    record_promo_usage,
    get_user_promo_usage,
    increment_usage_count
)

router = APIRouter(prefix="/promotions", tags=["promotions"])


def problem_response(status_code: int, title: str, detail: str, instance: str = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "type": "https://retail-platform.example.com/problems/promotion-error",
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": instance
        }
    )


@router.post("", status_code=201, response_model=PromotionResponse)
async def create_promotion_endpoint(promotion: PromotionCreate):
    """
    Create a new promotion (admin only).
    """
    if promotion.end_date <= promotion.start_date:
        return problem_response(
            status.HTTP_400_BAD_REQUEST,
            "Invalid Date Range",
            "end_date must be after start_date"
        )
    
    promo_id = f"PROMOTION#{uuid.uuid4().hex[:12]}"
    
    promotion_item = {
        "pk": promo_id,
        "sk": "METADATA",
        "name": promotion.name,
        "promo_code": promotion.promo_code,
        "promotion_type": promotion.promotion_type.value,
        "value": promotion.value,
        "start_date": promotion.start_date.isoformat(),
        "end_date": promotion.end_date.isoformat(),
        "usage_limit": promotion.usage_limit,
        "usage_count": 0,
        "min_cart_value": promotion.min_cart_value or 0,
        "applicable_categories": promotion.applicable_categories or [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = await create_promotion(promotion_item)
    
    return PromotionResponse(
        promo_id=promo_id,
        name=promotion.name,
        promo_code=promotion.promo_code,
        promotion_type=promotion.promotion_type,
        value=promotion.value,
        start_date=promotion.start_date,
        end_date=promotion.end_date,
        usage_limit=promotion.usage_limit,
        usage_count=0,
        min_cart_value=promotion.min_cart_value or 0,
        applicable_categories=promotion.applicable_categories,
        is_active=True
    )


@router.get("/{promo_id}", response_model=PromotionResponse)
async def get_promotion_endpoint(promo_id: str):
    """
    Get promotion details by promo_id.
    """
    promotion = await get_promotion_by_id(promo_id)
    
    if not promotion:
        return problem_response(
            status.HTTP_404_NOT_FOUND,
            "Promotion Not Found",
            f"Promotion {promo_id} does not exist"
        )
    
    start = datetime.fromisoformat(promotion["start_date"])
    end = datetime.fromisoformat(promotion["end_date"])
    is_active = start <= datetime.utcnow() <= end
    
    return PromotionResponse(
        promo_id=promo_id,
        name=promotion["name"],
        promo_code=promotion["promo_code"],
        promotion_type=promotion["promotion_type"],
        value=promotion["value"],
        start_date=start,
        end_date=end,
        usage_limit=promotion.get("usage_limit"),
        usage_count=promotion.get("usage_count", 0),
        min_cart_value=promotion.get("min_cart_value", 0),
        applicable_categories=promotion.get("applicable_categories"),
        is_active=is_active
    )


@router.get("", response_model=list[PromotionResponse])
async def list_promotions_endpoint():
    """
    List all active promotions.
    """
    promotions = await list_active_promotions()
    
    result = []
    for promo in promotions:
        start = datetime.fromisoformat(promo["start_date"])
        end = datetime.fromisoformat(promo["end_date"])
        is_active = start <= datetime.utcnow() <= end
        
        result.append(PromotionResponse(
            promo_id=promo["pk"],
            name=promo["name"],
            promo_code=promo["promo_code"],
            promotion_type=promo["promotion_type"],
            value=promo["value"],
            start_date=start,
            end_date=end,
            usage_limit=promo.get("usage_limit"),
            usage_count=promo.get("usage_count", 0),
            min_cart_value=promo.get("min_cart_value", 0),
            applicable_categories=promo.get("applicable_categories"),
            is_active=is_active
        ))
    
    return result


@router.post("/validate", response_model=ValidatePromoResponse)
async def validate_promo_endpoint(request: ValidatePromoRequest):
    """
    Validate promo code against a cart.
    """
    promotion = await get_promotion_by_code(request.promo_code)
    
    if not promotion:
        return ValidatePromoResponse(
            valid=False,
            discount_amount=0,
            message="Promo code not found"
        )
    
    now = datetime.utcnow()
    start = datetime.fromisoformat(promotion["start_date"])
    end = datetime.fromisoformat(promotion["end_date"])
    
    if not (start <= now <= end):
        return ValidatePromoResponse(
            valid=False,
            discount_amount=0,
            message="Promotion is not active",
            promo_id=promotion["pk"]
        )
    
    if request.cart_total < promotion.get("min_cart_value", 0):
        return ValidatePromoResponse(
            valid=False,
            discount_amount=0,
            message=f"Cart total does not meet minimum requirement of {promotion.get('min_cart_value', 0)}",
            promo_id=promotion["pk"]
        )
    
    if promotion.get("usage_limit"):
        if promotion.get("usage_count", 0) >= promotion["usage_limit"]:
            return ValidatePromoResponse(
                valid=False,
                discount_amount=0,
                message="Promotion usage limit reached",
                promo_id=promotion["pk"]
            )
    
    user_usage = await get_user_promo_usage(request.user_id, promotion["pk"])
    if user_usage:
        return ValidatePromoResponse(
            valid=False,
            discount_amount=0,
            message="You have already used this promotion",
            promo_id=promotion["pk"]
        )
    
    discount_amount = 0
    if promotion["promotion_type"] == "PERCENT":
        discount_amount = request.cart_total * (promotion["value"] / 100)
    elif promotion["promotion_type"] == "FIXED":
        discount_amount = promotion["value"]
    elif promotion["promotion_type"] == "BOGO":
        discount_amount = request.cart_total * 0.5
    
    discount_amount = min(discount_amount, request.cart_total)
    
    return ValidatePromoResponse(
        valid=True,
        discount_amount=round(discount_amount, 2),
        message="Promotion is valid",
        promo_id=promotion["pk"]
    )


@router.post("/apply", response_model=ApplyPromoResponse)
async def apply_promo_endpoint(request: ApplyPromoRequest):
    """
    Apply promo code to an order.
    """
    promotion = await get_promotion_by_code(request.promo_code)
    
    if not promotion:
        return ApplyPromoResponse(
            applied=False,
            discount_amount=0,
            message="Promo code not found"
        )
    
    now = datetime.utcnow()
    start = datetime.fromisoformat(promotion["start_date"])
    end = datetime.fromisoformat(promotion["end_date"])
    
    if not (start <= now <= end):
        return ApplyPromoResponse(
            applied=False,
            discount_amount=0,
            message="Promotion is not active",
            promo_id=promotion["pk"]
        )
    
    if promotion.get("usage_limit"):
        if promotion.get("usage_count", 0) >= promotion["usage_limit"]:
            return ApplyPromoResponse(
                applied=False,
                discount_amount=0,
                message="Promotion usage limit reached",
                promo_id=promotion["pk"]
            )
    
    user_usage = await get_user_promo_usage(request.user_id, promotion["pk"])
    if user_usage:
        return ApplyPromoResponse(
            applied=False,
            discount_amount=0,
            message="You have already used this promotion",
            promo_id=promotion["pk"]
        )
    
    discount_amount = 0
    if promotion["promotion_type"] == "PERCENT":
        discount_amount = 100 * (promotion["value"] / 100)
    elif promotion["promotion_type"] == "FIXED":
        discount_amount = promotion["value"]
    elif promotion["promotion_type"] == "BOGO":
        discount_amount = 50
    
    await record_promo_usage(request.user_id, promotion["pk"], request.order_id)
    await increment_usage_count(promotion["pk"])
    
    return ApplyPromoResponse(
        applied=True,
        discount_amount=round(discount_amount, 2),
        message="Promotion applied successfully",
        promo_id=promotion["pk"]
    )
