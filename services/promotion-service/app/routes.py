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
    PromotionType,
)
from app.db import (
    create_promotion,
    get_promotion_by_id,
    get_promotion_by_code,
    list_active_promotions,
    record_promo_usage,
    get_user_promo_usage,
    increment_usage_count,
)

router = APIRouter(prefix="/promotions", tags=["promotions"])

def error_response(status_code: int, title: str, detail: str, instance: str = None):
    """RFC 7807 Problem+JSON response"""
    body = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    return JSONResponse(status_code=status_code, content=body)

@router.post("", status_code=201)
async def create_promotion_endpoint(promotion: PromotionCreate):
    """
    Create a new promotion (admin only).
    """
    try:
        if promotion.startDate >= promotion.endDate:
            return error_response(
                400,
                "Invalid Promotion Dates",
                "startDate must be before endDate",
            )
        
        promo_id = f"PROMOTION#{uuid.uuid4()}"
        created_at = datetime.utcnow().isoformat()
        
        success = await create_promotion(
            promo_id=promo_id,
            promo_code=promotion.promoCode,
            name=promotion.name,
            promo_type=promotion.promoType.value,
            value=promotion.value,
            start_date=promotion.startDate.isoformat(),
            end_date=promotion.endDate.isoformat(),
            usage_limit=promotion.usageLimit,
            min_cart_value=promotion.minCartValue,
            applicable_categories=promotion.applicableCategories or [],
            created_at=created_at,
        )
        
        if not success:
            return error_response(
                409,
                "Conflict",
                "Promotion code already exists",
            )
        
        return JSONResponse(
            status_code=201,
            content={
                "promoId": promo_id,
                "promoCode": promotion.promoCode,
                "name": promotion.name,
                "message": "Promotion created successfully",
            },
        )
    except Exception as e:
        return error_response(
            500,
            "Internal Server Error",
            str(e),
        )

@router.get("/{promoId}")
async def get_promotion(promo_id: str):
    """
    Get promotion details by ID.
    """
    try:
        promotion = await get_promotion_by_id(promo_id)
        if not promotion:
            return error_response(
                404,
                "Not Found",
                f"Promotion {promo_id} not found",
                f"/promotions/{promo_id}",
            )
        
        return JSONResponse(
            status_code=200,
            content=PromotionResponse(**promotion).model_dump(),
        )
    except Exception as e:
        return error_response(
            500,
            "Internal Server Error",
            str(e),
        )

@router.get("")
async def list_promotions():
    """
    List all active promotions.
    """
    try:
        promotions = await list_active_promotions()
        return JSONResponse(
            status_code=200,
            content={
                "promotions": [PromotionResponse(**p).model_dump() for p in promotions],
                "count": len(promotions),
            },
        )
    except Exception as e:
        return error_response(
            500,
            "Internal Server Error",
            str(e),
        )

@router.post("/validate")
async def validate_promo(request: ValidatePromoRequest):
    """
    Validate promo code against cart total.
    """
    try:
        promotion = await get_promotion_by_code(request.promoCode)
        if not promotion:
            return JSONResponse(
                status_code=200,
                content=ValidatePromoResponse(
                    valid=False,
                    discountAmount=0.0,
                    message="Invalid promo code",
                ).model_dump(),
            )
        
        now = datetime.utcnow().isoformat()
        start_date = promotion.get("startDate")
        end_date = promotion.get("endDate")
        
        if now < start_date or now > end_date:
            return JSONResponse(
                status_code=200,
                content=ValidatePromoResponse(
                    valid=False,
                    discountAmount=0.0,
                    message="Promotion is not active",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        if request.cartTotal < promotion.get("minCartValue", 0):
            return JSONResponse(
                status_code=200,
                content=ValidatePromoResponse(
                    valid=False,
                    discountAmount=0.0,
                    message=f"Cart total must be at least ${promotion.get('minCartValue', 0)}",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        usage_limit = promotion.get("usageLimit", 0)
        usage_count = promotion.get("usageCount", 0)
        if usage_limit > 0 and usage_count >= usage_limit:
            return JSONResponse(
                status_code=200,
                content=ValidatePromoResponse(
                    valid=False,
                    discountAmount=0.0,
                    message="Promotion usage limit reached",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        user_usage = await get_user_promo_usage(
            request.userId,
            promotion.get("promoId"),
        )
        if user_usage:
            return JSONResponse(
                status_code=200,
                content=ValidatePromoResponse(
                    valid=False,
                    discountAmount=0.0,
                    message="You have already used this promotion",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        discount_amount = 0.0
        promo_type = promotion.get("promoType")
        value = promotion.get("value")
        
        if promo_type == "PERCENT":
            discount_amount = (request.cartTotal * value) / 100
        elif promo_type == "FIXED":
            discount_amount = value
        elif promo_type == "BOGO":
            discount_amount = value
        
        return JSONResponse(
            status_code=200,
            content=ValidatePromoResponse(
                valid=True,
                discountAmount=min(discount_amount, request.cartTotal),
                message="Promo code is valid",
                promoId=promotion.get("promoId"),
            ).model_dump(),
        )
    except Exception as e:
        return error_response(
            500,
            "Internal Server Error",
            str(e),
        )

@router.post("/apply")
async def apply_promo(request: ApplyPromoRequest):
    """
    Apply promo code to an order.
    """
    try:
        promotion = await get_promotion_by_code(request.promoCode)
        if not promotion:
            return JSONResponse(
                status_code=200,
                content=ApplyPromoResponse(
                    applied=False,
                    discountAmount=0.0,
                    message="Invalid promo code",
                ).model_dump(),
            )
        
        now = datetime.utcnow().isoformat()
        start_date = promotion.get("startDate")
        end_date = promotion.get("endDate")
        
        if now < start_date or now > end_date:
            return JSONResponse(
                status_code=200,
                content=ApplyPromoResponse(
                    applied=False,
                    discountAmount=0.0,
                    message="Promotion is not active",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        usage_limit = promotion.get("usageLimit", 0)
        usage_count = promotion.get("usageCount", 0)
        if usage_limit > 0 and usage_count >= usage_limit:
            return JSONResponse(
                status_code=200,
                content=ApplyPromoResponse(
                    applied=False,
                    discountAmount=0.0,
                    message="Promotion usage limit reached",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        user_usage = await get_user_promo_usage(
            request.userId,
            promotion.get("promoId"),
        )
        if user_usage:
            return JSONResponse(
                status_code=200,
                content=ApplyPromoResponse(
                    applied=False,
                    discountAmount=0.0,
                    message="You have already used this promotion",
                    promoId=promotion.get("promoId"),
                ).model_dump(),
            )
        
        promo_id = promotion.get("promoId")
        await record_promo_usage(
            user_id=request.userId,
            promo_id=promo_id,
            order_id=request.orderId,
            used_at=datetime.utcnow().isoformat(),
        )
        
        await increment_usage_count(promo_id)
        
        discount_amount = promotion.get("value", 0.0)
        if promotion.get("promoType") == "PERCENT":
            discount_amount = 0.0
        
        return JSONResponse(
            status_code=200,
            content=ApplyPromoResponse(
                applied=True,
                discountAmount=discount_amount,
                message="Promo code applied successfully",
                promoId=promo_id,
            ).model_dump(),
        )
    except Exception as e:
        return error_response(
            500,
            "Internal Server Error",
            str(e),
        )
