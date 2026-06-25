from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    promo_type: str = Field(..., pattern="^(PERCENT|FIXED|BOGO)$")
    value: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = Field(None, ge=0)
    min_cart_value: float = Field(default=0, ge=0)
    applicable_categories: Optional[List[str]] = Field(default_factory=list)


class PromotionResponse(BaseModel):
    promo_id: str
    name: str
    promo_type: str
    value: float
    start_date: str
    end_date: str
    usage_limit: Optional[int]
    usage_count: int
    min_cart_value: float
    applicable_categories: List[str]
    is_active: bool


class ValidatePromoRequest(BaseModel):
    promo_code: str = Field(..., min_length=1)
    cart_total: float = Field(..., ge=0)
    user_id: str = Field(..., min_length=1)


class ValidatePromoResponse(BaseModel):
    valid: bool
    discount_amount: float
    message: str


class ApplyPromoRequest(BaseModel):
    promo_code: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)


class ApplyPromoResponse(BaseModel):
    applied: bool
    discount_amount: float
    message: Optional[str] = None


class PromoUsage(BaseModel):
    user_id: str
    promo_id: str
    used_at: str
    order_id: str
