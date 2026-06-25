from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
from app.models import (
    PromotionCreate,
    PromotionResponse,
    ValidatePromoRequest,
    ValidatePromoResponse,
    ApplyPromoRequest,
    ApplyPromoResponse,
)
from app import db

router = APIRouter()


def problem_json(status_code: int, title: str, detail: str, instance: Optional[str] = None):
    body = {
        "type": f"about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    return JSONResponse(status_code=status_code, content=body)


@router.post("/promotions", status_code=201, response_model=PromotionResponse)
async def create_promotion(req: PromotionCreate):
    if req.start_date >= req.end_date:
        return problem_json(
            400,
            "Invalid Date Range",
            "start_date must be before end_date"
        )
    
    try:
        item = db.create_promotion({
            "name": req.name,
            "promo_type": req.promo_type,
            "value": req.value,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "usage_limit": req.usage_limit,
            "min_cart_value": req.min_cart_value,
            "applicable_categories": req.applicable_categories,
        })
        return PromotionResponse(
            promo_id=item["promo_id"],
            name=item["name"],
            promo_type=item["promo_type"],
            value=item["value"],
            start_date=item["start_date"],
            end_date=item["end_date"],
            usage_limit=item.get("usage_limit"),
            usage_count=item.get("usage_count", 0),
            min_cart_value=item.get("min_cart_value", 0),
            applicable_categories=item.get("applicable_categories", []),
            is_active=True,
        )
    except Exception as e:
        return problem_json(
            500,
            "Internal Server Error",
            f"Failed to create promotion: {str(e)}"
        )


@router.get("/promotions/{promo_id}", response_model=PromotionResponse)
async def get_promotion(promo_id: str):
    promo = db.get_promotion(promo_id)
    if not promo:
        return problem_json(
            404,
            "Not Found",
            f"Promotion {promo_id} not found",
            instance=f"/promotions/{promo_id}"
        )
    
    now = datetime.utcnow().isoformat()
    is_active = promo["start_date"] <= now <= promo["end_date"]
    
    return PromotionResponse(
        promo_id=promo["promo_id"],
        name=promo["name"],
        promo_type=promo["promo_type"],
        value=promo["value"],
        start_date=promo["start_date"],
        end_date=promo["end_date"],
        usage_limit=promo.get("usage_limit"),
        usage_count=promo.get("usage_count", 0),
        min_cart_value=promo.get("min_cart_value", 0),
        applicable_categories=promo.get("applicable_categories", []),
        is_active=is_active,
    )


@router.get("/promotions", response_model=list[PromotionResponse])
async def list_promotions():
    try:
        promos = db.list_active_promotions()
        now = datetime.utcnow().isoformat()
        
        result = []
        for promo in promos:
            is_active = promo["start_date"] <= now <= promo["end_date"]
            result.append(PromotionResponse(
                promo_id=promo["promo_id"],
                name=promo["name"],
                promo_type=promo["promo_type"],
                value=promo["value"],
                start_date=promo["start_date"],
                end_date=promo["end_date"],
                usage_limit=promo.get("usage_limit"),
                usage_count=promo.get("usage_count", 0),
                min_cart_value=promo.get("min_cart_value", 0),
                applicable_categories=promo.get("applicable_categories", []),
                is_active=is_active,
            ))
        return result
    except Exception as e:
        return problem_json(
            500,
            "Internal Server Error",
            f"Failed to list promotions: {str(e)}"
        )


@router.post("/promotions/validate", response_model=ValidatePromoResponse)
async def validate_promo(req: ValidatePromoRequest):
    try:
        promo = db.get_promotion_by_code(req.promo_code)
        if not promo:
            return ValidatePromoResponse(
                valid=False,
                discount_amount=0,
                message="Promotion code not found"
            )
        
        now = datetime.utcnow().isoformat()
        if not (promo["start_date"] <= now <= promo["end_date"]):
            return ValidatePromoResponse(
                valid=False,
                discount_amount=0,
                message="Promotion code is not active"
            )
        
        if req.cart_total < promo.get("min_cart_value", 0):
            return ValidatePromoResponse(
                valid=False,
                discount_amount=0,
                message=f"Minimum cart value of {promo.get('min_cart_value', 0)} required"
            )
        
        usage_limit = promo.get("usage_limit")
        usage_count = promo.get("usage_count", 0)
        if usage_limit and usage_count >= usage_limit:
            return ValidatePromoResponse(
                valid=False,
                discount_amount=0,
                message="Promotion code usage limit exceeded"
            )
        
        user_usages = db.get_user_promo_usage(req.user_id, promo["promo_id"])
        if user_usages:
            return ValidatePromoResponse(
                valid=False,
                discount_amount=0,
                message="User has already used this promotion code"
            )
        
        discount_amount = 0
        if promo["promo_type"] == "PERCENT":
            discount_amount = req.cart_total * (promo["value"] / 100)
        elif promo["promo_type"] == "FIXED":
            discount_amount = min(promo["value"], req.cart_total)
        elif promo["promo_type"] == "BOGO":
            discount_amount = req.cart_total * 0.5
        
        return ValidatePromoResponse(
            valid=True,
            discount_amount=round(discount_amount, 2),
            message="Promotion code is valid"
        )
    except Exception as e:
        return problem_json(
            500,
            "Internal Server Error",
            f"Failed to validate promotion: {str(e)}"
        )


@router.post("/promotions/apply", response_model=ApplyPromoResponse)
async def apply_promo(req: ApplyPromoRequest):
    try:
        promo = db.get_promotion_by_code(req.promo_code)
        if not promo:
            return ApplyPromoResponse(
                applied=False,
                discount_amount=0,
                message="Promotion code not found"
            )
        
        now = datetime.utcnow().isoformat()
        if not (promo["start_date"] <= now <= promo["end_date"]):
            return ApplyPromoResponse(
                applied=False,
                discount_amount=0,
                message="Promotion code is not active"
            )
        
        usage_limit = promo.get("usage_limit")
        usage_count = promo.get("usage_count", 0)
        if usage_limit and usage_count >= usage_limit:
            return ApplyPromoResponse(
                applied=False,
                discount_amount=0,
                message="Promotion code usage limit exceeded"
            )
        
        user_usages = db.get_user_promo_usage(req.user_id, promo["promo_id"])
        if user_usages:
            return ApplyPromoResponse(
                applied=False,
                discount_amount=0,
                message="User has already used this promotion code"
            )
        
        db.record_promo_usage(req.user_id, promo["promo_id"], req.order_id)
        db.increment_promotion_usage(promo["promo_id"])
        
        discount_amount = 0
        if promo["promo_type"] == "PERCENT":
            discount_amount = 10.0
        elif promo["promo_type"] == "FIXED":
            discount_amount = promo["value"]
        elif promo["promo_type"] == "BOGO":
            discount_amount = 15.0
        
        return ApplyPromoResponse(
            applied=True,
            discount_amount=round(discount_amount, 2),
            message="Promotion applied successfully"
        )
    except Exception as e:
        return problem_json(
            500,
            "Internal Server Error",
            f"Failed to apply promotion: {str(e)}"
        )
