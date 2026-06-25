from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from app.models import (
    PromotionCreate, PromotionResponse, ValidatePromotionRequest,
    ValidatePromotionResponse, ApplyPromotionRequest, ApplyPromotionResponse
)
from app import db

router = APIRouter(prefix="/promotions")

def _to_promotion_response(item: dict) -> PromotionResponse:
    return PromotionResponse(
        promo_id=item["promo_id"],
        name=item["name"],
        promo_code=item["promo_code"],
        promotion_type=item["promotion_type"],
        value=item["value"],
        start_date=item["start_date"],
        end_date=item["end_date"],
        usage_limit=item.get("usage_limit"),
        usage_count=item.get("usage_count", 0),
        min_cart_value=item.get("min_cart_value"),
        applicable_categories=item.get("applicable_categories")
    )

@router.post("", status_code=201, response_model=PromotionResponse)
async def create_promotion(promotion: PromotionCreate):
    if promotion.start_date >= promotion.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    promotion_data = {
        "name": promotion.name,
        "promo_code": promotion.promo_code,
        "promotion_type": promotion.promotion_type.value,
        "value": promotion.value,
        "start_date": promotion.start_date.isoformat(),
        "end_date": promotion.end_date.isoformat(),
        "usage_limit": promotion.usage_limit,
        "min_cart_value": promotion.min_cart_value,
        "applicable_categories": promotion.applicable_categories
    }
    
    promo_id = db.create_promotion(promotion_data)
    item = db.get_promotion_by_id(promo_id)
    
    return _to_promotion_response(item)

@router.get("/{promo_id}", response_model=PromotionResponse)
async def get_promotion(promo_id: str):
    item = db.get_promotion_by_id(promo_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion not found"
        )
    
    return _to_promotion_response(item)

@router.get("", response_model=list[PromotionResponse])
async def list_active_promotions():
    items = db.list_active_promotions()
    return [_to_promotion_response(item) for item in items]

@router.post("/validate", response_model=ValidatePromotionResponse)
async def validate_promotion(request: ValidatePromotionRequest):
    promotion = db.get_promotion_by_code(request.promo_code)
    
    if not promotion:
        return ValidatePromotionResponse(
            valid=False,
            discount_amount=0.0,
            message="Promotion code not found"
        )
    
    now = datetime.utcnow().isoformat()
    
    if promotion["start_date"] > now or promotion["end_date"] < now:
        return ValidatePromotionResponse(
            valid=False,
            discount_amount=0.0,
            message="Promotion is not active"
        )
    
    if promotion.get("usage_limit") is not None:
        if promotion.get("usage_count", 0) >= promotion["usage_limit"]:
            return ValidatePromotionResponse(
                valid=False,
                discount_amount=0.0,
                message="Promotion usage limit reached"
            )
    
    min_cart_value = promotion.get("min_cart_value", 0)
    if request.cart_total < min_cart_value:
        return ValidatePromotionResponse(
            valid=False,
            discount_amount=0.0,
            message=f"Cart total must be at least {min_cart_value}"
        )
    
    promotion_type = promotion["promotion_type"]
    value = promotion["value"]
    
    if promotion_type == "PERCENT":
        discount_amount = request.cart_total * (value / 100)
    elif promotion_type == "FIXED":
        discount_amount = value
    elif promotion_type == "BOGO":
        discount_amount = request.cart_total * (value / 100)
    else:
        discount_amount = 0.0
    
    return ValidatePromotionResponse(
        valid=True,
        discount_amount=round(discount_amount, 2),
        message="Promotion is valid"
    )

@router.post("/apply", response_model=ApplyPromotionResponse)
async def apply_promotion(request: ApplyPromotionRequest):
    promotion = db.get_promotion_by_code(request.promo_code)
    
    if not promotion:
        return ApplyPromotionResponse(
            applied=False,
            discount_amount=0.0,
            message="Promotion code not found"
        )
    
    now = datetime.utcnow().isoformat()
    
    if promotion["start_date"] > now or promotion["end_date"] < now:
        return ApplyPromotionResponse(
            applied=False,
            discount_amount=0.0,
            message="Promotion is not active"
        )
    
    if promotion.get("usage_limit") is not None:
        if promotion.get("usage_count", 0) >= promotion["usage_limit"]:
            return ApplyPromotionResponse(
                applied=False,
                discount_amount=0.0,
                message="Promotion usage limit reached"
            )
    
    promo_id = promotion["promo_id"]
    
    try:
        db.record_promo_usage(request.user_id, promo_id, request.order_id)
        db.increment_promotion_usage_count(promo_id)
        
        promotion_type = promotion["promotion_type"]
        value = promotion["value"]
        
        if promotion_type == "PERCENT":
            discount_amount = 100.0 * (value / 100)
        elif promotion_type == "FIXED":
            discount_amount = value
        elif promotion_type == "BOGO":
            discount_amount = 100.0 * (value / 100)
        else:
            discount_amount = 0.0
        
        return ApplyPromotionResponse(
            applied=True,
            discount_amount=round(discount_amount, 2),
            message="Promotion applied successfully"
        )
    except Exception as e:
        return ApplyPromotionResponse(
            applied=False,
            discount_amount=0.0,
            message=f"Error applying promotion: {str(e)}"
        )
