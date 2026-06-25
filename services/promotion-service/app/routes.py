from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from app.models import (
    PromotionCreate,
    PromotionUpdate,
    Promotion,
    ValidatePromoRequest,
    ValidatePromoResponse,
    ApplyPromoRequest,
    ApplyPromoResponse,
    UpdatePromotionResponse,
    DeletePromotionResponse,
    PromotionType
)
from app.db import (
    create_promotion,
    get_promotion,
    update_promotion,
    delete_promotion,
    list_active_promotions,
    validate_promo_code,
    apply_promo_code,
    check_user_promo_usage
)

router = APIRouter(prefix="/promotions", tags=["promotions"])

def verify_admin_header(x_admin_token: Optional[str] = Header(None)):
    if not x_admin_token:
        raise HTTPException(status_code=403, detail="Admin authorization required")
    return x_admin_token

@router.post("", status_code=201)
async def create_promotion_endpoint(
    request: PromotionCreate,
    admin_token: str = Depends(verify_admin_header)
) -> Promotion:
    promo_id = str(uuid4())
    now = datetime.utcnow()
    
    if request.end_date <= request.start_date:
        raise HTTPException(
            status_code=400,
            detail={"type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
                   "title": "Invalid Date Range",
                   "status": 400,
                   "detail": "end_date must be after start_date"}
        )
    
    promotion_data = {
        "promo_id": promo_id,
        "name": request.name,
        "type": request.type.value,
        "value": request.value,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "usage_limit": request.usage_limit,
        "usage_count": 0,
        "min_cart_value": request.min_cart_value,
        "applicable_categories": request.applicable_categories,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    created = await create_promotion(promo_id, promotion_data)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create promotion")
    
    return Promotion(
        promo_id=promo_id,
        name=request.name,
        type=request.type,
        value=request.value,
        start_date=request.start_date,
        end_date=request.end_date,
        usage_limit=request.usage_limit,
        usage_count=0,
        min_cart_value=request.min_cart_value,
        applicable_categories=request.applicable_categories,
        created_at=now,
        updated_at=now
    )

@router.get("/{promo_id}")
async def get_promotion_endpoint(promo_id: str) -> Promotion:
    promotion = await get_promotion(promo_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    return Promotion(
        promo_id=promotion.get("promo_id"),
        name=promotion.get("name"),
        type=PromotionType(promotion.get("type")),
        value=float(promotion.get("value")),
        start_date=datetime.fromisoformat(promotion.get("start_date")),
        end_date=datetime.fromisoformat(promotion.get("end_date")),
        usage_limit=int(promotion.get("usage_limit")),
        usage_count=int(promotion.get("usage_count", 0)),
        min_cart_value=float(promotion.get("min_cart_value", 0)),
        applicable_categories=promotion.get("applicable_categories", []),
        created_at=datetime.fromisoformat(promotion.get("created_at")),
        updated_at=datetime.fromisoformat(promotion.get("updated_at"))
    )

@router.patch("/{promo_id}")
async def update_promotion_endpoint(
    promo_id: str,
    request: PromotionUpdate,
    admin_token: str = Depends(verify_admin_header)
) -> UpdatePromotionResponse:
    promotion = await get_promotion(promo_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.value is not None:
        update_data["value"] = request.value
    if request.end_date is not None:
        update_data["end_date"] = request.end_date.isoformat()
    if request.usage_limit is not None:
        update_data["usage_limit"] = request.usage_limit
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    updated = await update_promotion(promo_id, update_data)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update promotion")
    
    updated_promo = await get_promotion(promo_id)
    
    return UpdatePromotionResponse(
        updated=True,
        promotion=Promotion(
            promo_id=updated_promo.get("promo_id"),
            name=updated_promo.get("name"),
            type=PromotionType(updated_promo.get("type")),
            value=float(updated_promo.get("value")),
            start_date=datetime.fromisoformat(updated_promo.get("start_date")),
            end_date=datetime.fromisoformat(updated_promo.get("end_date")),
            usage_limit=int(updated_promo.get("usage_limit")),
            usage_count=int(updated_promo.get("usage_count", 0)),
            min_cart_value=float(updated_promo.get("min_cart_value", 0)),
            applicable_categories=updated_promo.get("applicable_categories", []),
            created_at=datetime.fromisoformat(updated_promo.get("created_at")),
            updated_at=datetime.fromisoformat(updated_promo.get("updated_at"))
        )
    )

@router.delete("/{promo_id}")
async def delete_promotion_endpoint(
    promo_id: str,
    admin_token: str = Depends(verify_admin_header)
) -> DeletePromotionResponse:
    promotion = await get_promotion(promo_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    deleted = await delete_promotion(promo_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete promotion")
    
    return DeletePromotionResponse(deleted=True, promo_id=promo_id)

@router.post("/validate", response_model=ValidatePromoResponse)
async def validate_promo_endpoint(request: ValidatePromoRequest) -> ValidatePromoResponse:
    result = await validate_promo_code(
        request.promo_code,
        request.cart_total,
        request.user_id
    )
    return ValidatePromoResponse(**result)

@router.post("/apply", response_model=ApplyPromoResponse)
async def apply_promo_endpoint(request: ApplyPromoRequest) -> ApplyPromoResponse:
    result = await apply_promo_code(
        request.promo_code,
        request.order_id,
        request.user_id
    )
    if not result.get("applied"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to apply promotion"))
    
    return ApplyPromoResponse(
        applied=result.get("applied"),
        discount_amount=result.get("discount_amount", 0)
    )

@router.get("", response_model=List[Promotion])
async def list_promotions_endpoint() -> List[Promotion]:
    promotions = await list_active_promotions()
    return [
        Promotion(
            promo_id=p.get("promo_id"),
            name=p.get("name"),
            type=PromotionType(p.get("type")),
            value=float(p.get("value")),
            start_date=datetime.fromisoformat(p.get("start_date")),
            end_date=datetime.fromisoformat(p.get("end_date")),
            usage_limit=int(p.get("usage_limit")),
            usage_count=int(p.get("usage_count", 0)),
            min_cart_value=float(p.get("min_cart_value", 0)),
            applicable_categories=p.get("applicable_categories", []),
            created_at=datetime.fromisoformat(p.get("created_at")),
            updated_at=datetime.fromisoformat(p.get("updated_at"))
        )
        for p in promotions
    ]
