from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PromotionType(str, Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    BOGO = "BOGO"


class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    promo_code: str = Field(..., min_length=1, max_length=50)
    promotion_type: PromotionType
    value: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = Field(default=None, ge=1)
    min_cart_value: Optional[float] = Field(default=0, ge=0)
    applicable_categories: Optional[List[str]] = Field(default=None)


class PromotionResponse(BaseModel):
    promo_id: str
    name: str
    promo_code: str
    promotion_type: PromotionType
    value: float
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int]
    usage_count: int
    min_cart_value: float
    applicable_categories: Optional[List[str]]
    is_active: bool


class ValidatePromoRequest(BaseModel):
    promo_code: str = Field(..., min_length=1)
    cart_total: float = Field(..., ge=0)
    user_id: str = Field(..., min_length=1)


class ValidatePromoResponse(BaseModel):
    valid: bool
    discount_amount: float
    message: str
    promo_id: Optional[str] = None


class ApplyPromoRequest(BaseModel):
    promo_code: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)


class ApplyPromoResponse(BaseModel):
    applied: bool
    discount_amount: float
    message: str
    promo_id: Optional[str] = None


class PromoUsage(BaseModel):
    user_id: str
    promo_id: str
    used_at: datetime
    order_id: str


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
